---
phase: 02-code-reliability
reviewed: 2026-06-20T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - apps/packing_list/serializers.py
  - apps/packing_list/views.py
  - apps/certificate_of_analysis/serializers.py
  - apps/workflow/services.py
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-20
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed four files covering the packing list domain (serializers + views), the certificate of analysis serializer, and the central workflow service. The workflow service is well-structured and correctly enforces constraint #11/#12 (all transitions through WorkflowService, AuditLog in the same atomic block). The packing list write path is correctly wrapped in `transaction.atomic()` with both PL and CI created atomically.

Two critical issues were found: a double-call to `self.get_object()` in `ContainerItemViewSet.perform_update` that causes a stale-reference bug for CI rebuilding, and missing `transaction.atomic()` wrapping in the COA serializer's `create` and `update` methods, which can produce orphaned/empty records on partial failures. Five warnings cover audit log data integrity, an extra DB query race window, missing `updated_at` on signed-copy save, and an unsafe CI state assumption. Four info items cover unused imports, a redundant alias, and a duplicated serializer class.

---

## Critical Issues

### CR-01: `ContainerItemViewSet.perform_update` calls `self.get_object()` twice — second call returns stale data

**File:** `apps/packing_list/views.py:561-565`

**Issue:** `perform_update` calls `self.get_object()` at line 562 to check editability, then calls it again at line 565 (after the save) to get the container's packing list for `rebuild_ci_line_items`. The second `get_object()` hits the database again and returns a fresh database row. Because `serializer.instance` already holds the saved object, the second `get_object()` is redundant and misleading — if the `container` FK could ever be changed by the serializer, the second call would return the pre-update FK value (the old container), causing `rebuild_ci_line_items` to be called on the wrong packing list. Even without that, the pattern is error-prone and creates an extra, unjustified DB round-trip inside every item update.

The `perform_destroy` method (line 568) correctly captures `pl` before the delete and passes it directly — `perform_update` should follow the same pattern.

**Fix:**
```python
def perform_update(self, serializer):
    # Capture the instance and its container before saving.
    instance = self.get_object()
    self._check_editable(instance.container)
    serializer.save()
    # Use the container captured above — do not call get_object() again.
    from apps.commercial_invoice.services import rebuild_ci_line_items
    rebuild_ci_line_items(instance.container.packing_list)
```

---

### CR-02: `CertificateOfAnalysisSerializer.create` and `update` are not wrapped in `transaction.atomic()`

**File:** `apps/certificate_of_analysis/serializers.py:119-140`

**Issue:** `create()` (lines 119-128) creates the `CertificateOfAnalysis` record first, then creates `COAParameter` rows in a loop. `update()` (lines 130-140) deletes all existing parameters then recreates them in a loop. Neither method uses `transaction.atomic()`. If any parameter creation fails — due to a DB error, constraint violation, or an exception from `**param_data` unpacking — the COA exists in the database with zero parameters. For `update`, the old parameters are already deleted and the new ones are partially written. Neither state is recoverable by the caller.

**Fix:**
```python
from django.db import transaction

def create(self, validated_data):
    from .services import generate_document_number
    parameters_data = validated_data.pop("parameters")
    with transaction.atomic():
        coa = CertificateOfAnalysis.objects.create(
            coa_number=generate_document_number(),
            **validated_data,
        )
        for param_data in parameters_data:
            COAParameter.objects.create(coa=coa, **param_data)
    return coa

def update(self, instance, validated_data):
    parameters_data = validated_data.pop("parameters", None)
    with transaction.atomic():
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if parameters_data is not None:
            instance.parameters.all().delete()
            for param_data in parameters_data:
                COAParameter.objects.create(coa=instance, **param_data)
    return instance
```

---

## Warnings

### WR-01: CI AuditLog records the PL's `from_status` instead of the CI's own `from_status`

**File:** `apps/workflow/services.py:203-212`

**Issue:** In `transition_joint`, `current_status` is read from `packing_list.status` at line 133 and then reused as `from_status` for the CI's `AuditLog` entry at line 208. In normal operation the PL and CI statuses are always in sync, so this is usually harmless. However, if the two records ever drift (manual DB fix, migration bug, or a previous partial failure), every subsequent workflow action will record the wrong `from_status` in the CI's audit trail. This makes the audit log unreliable as a compliance record.

**Fix:** Read the CI's current status explicitly before overwriting it:
```python
ci_from_status = ci.status   # capture before overwriting

ci.status = next_status
ci.save(update_fields=["status", "updated_at"])
AuditLog.objects.create(
    ...
    from_status=ci_from_status,  # use CI's actual prior status
    ...
)
```

---

### WR-02: `PackingListViewSet.signed_copy` upload does not update `updated_at`

**File:** `apps/packing_list/views.py:394-401`

**Issue:** Line 398 saves the PL with `update_fields=["signed_copy"]`. Django's `auto_now=True` fields (including `updated_at`) are only written to the database when they appear in `update_fields`. By omitting `"updated_at"`, the record's timestamp does not change when a signed copy is uploaded. This means sorting or filtering by `updated_at` will not surface PLs that received a signed copy upload.

**Fix:**
```python
pl.signed_copy = uploaded_file
pl.save(update_fields=["signed_copy", "updated_at"])
```

---

### WR-03: `PackingListViewSet.perform_update` status check uses a second `get_object()` call that is not inside a database lock

**File:** `apps/packing_list/views.py:196-198`

**Issue:** `perform_update` calls `instance = self.get_object()` at line 197 to read the PL's current status for the editability check, then calls `serializer.save()` at line 220 which issues a separate `UPDATE`. Between the `SELECT` (line 197) and the `UPDATE` (line 220), a concurrent request could change the status from `DRAFT` to `PENDING_APPROVAL`. The update would then silently succeed on a non-editable document because the status was checked on the snapshot, not with a `SELECT FOR UPDATE`. The existing `transaction.atomic()` block starts at line 219, but the status check at line 198 happens before it.

**Fix:** Move the status check inside the atomic block and use `select_for_update()` to lock the row:
```python
with transaction.atomic():
    # Lock the PL row so concurrent workflow transitions block until we finish.
    instance = PackingList.objects.select_for_update().get(pk=serializer.instance.pk)
    if instance.status not in EDITABLE_STATES:
        raise ValidationError(
            {"detail": f"Cannot edit a Packing List with status '{instance.status}'."}
        )
    pl = serializer.save()
    ...
```

---

### WR-04: `ContainerViewSet.perform_update` does not rebuild CI line items after a container header update

**File:** `apps/packing_list/views.py:473-476`

**Issue:** `perform_update` in `ContainerViewSet` (lines 473-476) saves the container but does not call `rebuild_ci_line_items`. `perform_create` (line 469-471) and `perform_destroy` (line 479-483) both call `rebuild_ci_line_items` after their operations. Updating a container (`tare_weight`, `marks_numbers`, etc.) does not directly affect CI line item quantities, so this may be intentional for those fields. However, if `tare_weight` is updated, the container `gross_weight` is recomputed on `container.save()` (model-level), but the CI totals won't reflect the update if any downstream CI calculation depends on gross weight. More importantly, the inconsistency between create/destroy (which call rebuild) and update (which does not) is a pattern gap that can mislead future contributors.

**Fix:** Add a `rebuild_ci_line_items` call for consistency, or add a clear comment explaining why the CI rebuild is deliberately skipped on container header updates:
```python
def perform_update(self, serializer):
    instance = self.get_object()
    self._check_pl_editable(instance.packing_list)
    serializer.save()
    # Container header fields (ref, marks, tare_weight) do not change CI line
    # item quantities. CI rebuild is only needed on item-level changes.
    # If this changes in future, add: rebuild_ci_line_items(instance.packing_list)
```

---

### WR-05: `COAParameterSerializer` does not validate `spec_type` is present on create

**File:** `apps/certificate_of_analysis/serializers.py:26-49`

**Issue:** The `validate` method silently passes (returns `data` unchanged) when `spec_type` is neither `"QUANTITATIVE"` nor `"QUALITATIVE"`. The `COAParameter.spec_type` field has `choices` on the model, which means DRF's `ModelSerializer` will reject unknown values before `validate()` is called. However, if `spec_type` is provided as an empty string or `None`, DRF may pass it through to `validate()` as `None` depending on the field configuration, and the method will return `data` without raising. This creates a parameter row with a null/empty `spec_type` that is meaningless and cannot be rendered in the PDF.

**Fix:** Add an explicit guard at the top of `validate`:
```python
def validate(self, data):
    spec_type = data.get("spec_type")
    if spec_type not in ("QUANTITATIVE", "QUALITATIVE"):
        raise serializers.ValidationError(
            {"spec_type": "spec_type must be 'QUANTITATIVE' or 'QUALITATIVE'."}
        )
    ...
```

---

## Info

### IN-01: Unused import `generate_pl_number` in `serializers.py`

**File:** `apps/packing_list/serializers.py:18`

**Issue:** `generate_document_number` is imported as `generate_pl_number` but is never called within `serializers.py`. The actual call happens inside `views.py` via a local inline import. This dead import adds noise and could confuse a reader into thinking number generation happens at the serializer layer.

**Fix:** Remove line 18:
```python
# Remove this line:
from .services import generate_document_number as generate_pl_number
```

---

### IN-02: Unused import `EDITABLE_STATES` in `serializers.py`

**File:** `apps/packing_list/serializers.py:16`

**Issue:** `EDITABLE_STATES` is imported from `apps.workflow.constants` at line 16 but is never referenced in the serializer file. It is used in `views.py`, not here.

**Fix:** Remove `EDITABLE_STATES` from the import at line 16:
```python
# Before:
from apps.workflow.constants import EDITABLE_STATES

# After: (remove the import entirely — it's unused in this file)
```

---

### IN-03: Redundant `status` alias import inside `PackingListViewSet.create`

**File:** `apps/packing_list/views.py:141`

**Issue:** `from rest_framework import status as drf_status` is imported inside the `create` method body at line 141. However, `status` is already imported at the module level at line 12 (`from rest_framework import filters, status, viewsets`). The alias `drf_status` is only needed to avoid a name collision with DRF's `status` module and the local variable `status` (which doesn't exist in `create`'s scope). The inline import and alias are unnecessary.

**Fix:** Remove the inline import and use the module-level `status` directly:
```python
# Remove line 141:
from rest_framework import status as drf_status

# Change line 142:
return Response(read_serializer.data, status=status.HTTP_201_CREATED)
```

---

### IN-04: `AuditLogSerializer` is duplicated in `certificate_of_analysis/serializers.py`

**File:** `apps/certificate_of_analysis/serializers.py:143-155`

**Issue:** `AuditLogSerializer` is defined in `apps/workflow/serializers.py` with a comment explicitly stating it "lives here rather than being duplicated per app." The COA serializer file defines an identical (but slightly different) `AuditLogSerializer` as a `ModelSerializer` rather than a plain `Serializer`. The COA views file (`views.py:22`) imports from `.serializers` (the local copy) rather than from `apps.workflow.serializers`. This means the two implementations can drift independently.

**Fix:** Remove the `AuditLogSerializer` class from `apps/certificate_of_analysis/serializers.py` (lines 143-155) and update `apps/certificate_of_analysis/views.py` line 22:
```python
# In views.py, change:
from .serializers import AuditLogSerializer, CertificateOfAnalysisSerializer

# To:
from apps.workflow.serializers import AuditLogSerializer
from .serializers import CertificateOfAnalysisSerializer
```

---

_Reviewed: 2026-06-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
