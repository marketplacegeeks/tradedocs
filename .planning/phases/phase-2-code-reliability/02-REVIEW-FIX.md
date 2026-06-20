---
phase: 02-code-reliability
fixed_at: 2026-06-20T00:00:00Z
review_path: .planning/phases/phase-2-code-reliability/02-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 2: Code Review Fix Report

**Fixed at:** 2026-06-20
**Source review:** .planning/phases/phase-2-code-reliability/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (2 Critical, 5 Warning — Info excluded per fix_scope)
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: `ContainerItemViewSet.perform_update` calls `self.get_object()` twice — second call returns stale data

**Files modified:** `apps/packing_list/views.py`
**Commit:** 4419da3
**Applied fix:** Introduced a local `instance = self.get_object()` variable at the top of `perform_update`. The editability check uses `instance.container` and the `rebuild_ci_line_items` call uses `instance.container.packing_list` — both referencing the single captured snapshot. The second `self.get_object()` call after `serializer.save()` is eliminated.

---

### CR-02: `CertificateOfAnalysisSerializer.create` and `update` are not wrapped in `transaction.atomic()`

**Files modified:** `apps/certificate_of_analysis/serializers.py`
**Commit:** 5342742
**Applied fix:** Added `from django.db import transaction` to the module imports. Wrapped the body of `create()` (COA record creation + parameter loop) in `with transaction.atomic()`. Wrapped the body of `update()` (field updates + parameter delete-and-recreate loop) in `with transaction.atomic()`. Both methods now roll back fully on any mid-loop failure.

---

### WR-01: CI AuditLog records the PL's `from_status` instead of the CI's own `from_status`

**Files modified:** `apps/workflow/services.py`
**Commit:** 658b06c
**Applied fix:** In `transition_joint`, added `ci_from_status = ci.status` immediately before `ci.status = next_status`. The `AuditLog.objects.create()` call for the CI now passes `from_status=ci_from_status` instead of `from_status=current_status` (which was the PL's status snapshot).

---

### WR-02: `PackingListViewSet.signed_copy` upload does not update `updated_at`

**Files modified:** `apps/packing_list/views.py`
**Commit:** 29154f1
**Applied fix:** Changed `pl.save(update_fields=["signed_copy"])` to `pl.save(update_fields=["signed_copy", "updated_at"])` so Django writes the `auto_now` timestamp when a signed copy is uploaded.

---

### WR-03: `PackingListViewSet.perform_update` status check is not inside a database lock

**Files modified:** `apps/packing_list/views.py`
**Commit:** bfff2ee
**Applied fix:** Moved the PL editability check inside the `transaction.atomic()` block. The check now uses `PackingList.objects.select_for_update().get(pk=serializer.instance.pk)` to acquire a row lock before reading `status`, eliminating the race window between the snapshot read and the `UPDATE`. The role check (CHECKER denial) remains outside the atomic block since it does not depend on the locked row.

---

### WR-04: `ContainerViewSet.perform_update` does not rebuild CI line items after a container header update

**Files modified:** `apps/packing_list/views.py`
**Commit:** d151519
**Applied fix:** Added a block comment after `serializer.save()` in `ContainerViewSet.perform_update` explaining that CI rebuild is intentionally omitted for container header fields (container_ref, marks_numbers, seal_number, tare_weight) because they do not affect CI line item quantities. The comment also points to the location where a rebuild call should be added if that assumption changes in future.

---

### WR-05: `COAParameterSerializer` does not validate `spec_type` is present on create

**Files modified:** `apps/certificate_of_analysis/serializers.py`
**Commit:** 115c784
**Applied fix:** Added an explicit guard at the top of `COAParameterSerializer.validate()` that raises `ValidationError({"spec_type": "spec_type must be 'QUANTITATIVE' or 'QUALITATIVE'."})` when `spec_type` is anything other than those two values (including `None` or empty string). The existing QUANTITATIVE and QUALITATIVE branch checks follow immediately after the guard and are unreachable for invalid values.

---

---

_Fixed: 2026-06-20_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
