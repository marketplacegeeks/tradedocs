---
phase: 04-test-coverage
reviewed: 2026-06-20T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - apps/packing_list/tests/test_views.py
  - apps/proforma_invoice/serializers.py
  - apps/proforma_invoice/services.py
  - apps/proforma_invoice/tests/test_views.py
  - apps/workflow/tests/test_services.py
findings:
  critical: 0
  warning: 2
  info: 5
  total: 7
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-06-20
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Five files were reviewed: the proforma invoice serializer and document-number service, and three test modules covering proforma invoices, packing lists, and workflow service transitions. The application code is solid overall — the serializer correctly enforces state-aware read-only fields, cost-field validation per incoterm, and atomic document-number generation. The test suites are comprehensive and well-structured.

Two warnings were found. The more significant one is a logic bug in `services.py`: the COUNT-based document-number algorithm generates duplicate PI numbers after a hard-delete, which will hit the unique constraint and cause an `IntegrityError` in production. The second is a misleading comment in the atomicity mock test that contradicts the actual patching strategy used.

The five info items are code quality gaps: unused imports, hardcoded status strings, and a raw action string where a constant should be used.

## Warnings

### WR-01: `generate_document_number()` reuses numbers after hard-delete

**File:** `apps/proforma_invoice/services.py:48`
**Issue:** The sequence number is derived from `len(existing) + 1`, where `existing` is the list of all PI rows whose `pi_number` starts with the current year prefix. If a SUPER_ADMIN hard-deletes a PI that is not the latest one in a given year (e.g., `PI-2026-0002` is deleted while `PI-2026-0001` still exists), the count drops by one and the next call returns `PI-2026-0002` again. The database `unique` constraint on `pi_number` prevents silent data corruption, but the end-user sees an `IntegrityError` / 500 instead of a successful creation.

This path is reachable: `test_super_admin_can_hard_delete_pi` confirms the hard-delete endpoint works. There is no test covering "create PI after a non-latest PI has been hard-deleted".

**Fix:** Replace the count-based approach with a `MAX`-based approach so the sequence only moves forward:

```python
from django.db.models import Max
import re

def generate_document_number():
    from .models import ProformaInvoice

    year = date.today().year
    prefix = f"PI-{year}-"

    # Lock all rows for this year and find the highest sequence number used.
    existing = (
        ProformaInvoice.objects
        .select_for_update()
        .filter(pi_number__startswith=prefix)
        .values_list("pi_number", flat=True)
    )
    # Extract the numeric suffix from each matching number and take the max.
    max_seq = 0
    for number in existing:
        suffix = number[len(prefix):]
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    return f"{prefix}{max_seq + 1:04d}"
```

This guarantees monotonic growth regardless of hard-deletes.

---

### WR-02: Atomicity mock test comment contradicts the actual patching strategy

**File:** `apps/workflow/tests/test_services.py:205-218`
**Issue:** The comment at line 206 states *"We patch on the instance (ci) rather than the class to avoid affecting other test infrastructure."* However, `patch.object(ci.__class__, "save", failing_save)` patches `CommercialInvoice.save` at the **class level**, not on the instance. Any `CommercialInvoice` save call made inside the `with` block — even for a different CI object — will enter `failing_save`. The `self_inner.pk == ci.pk` guard prevents false failures for other CIs, so the test is functionally correct, but the comment is the opposite of the truth. A future maintainer following this comment and trying to make the mock "truly instance-level" could introduce a real bug.

Additionally, since the class is being patched, if `CommercialInvoiceFactory` or any other fixture were called inside this `with` block in a future edit, it would silently enter the failing path (the `call_count` check would pass for any new CI since they have different `pk`s — actually they'd succeed, but this remains a fragile pattern).

**Fix:** Either correct the comment or switch to true instance-level patching:

```python
# Option A: Correct the comment
# Patch CommercialInvoice.save at the CLASS level. The pk guard prevents
# this from affecting unrelated CI saves within this block.
with patch.object(ci.__class__, "save", failing_save):
    ...

# Option B: Use true instance-level patching
with patch.object(ci, "save", side_effect=IntegrityError("Simulated CI save failure")):
    with pytest.raises(IntegrityError):
        WorkflowService.transition_joint(
            packing_list=pl,
            action=APPROVE,
            performed_by=checker,
        )
```

Option B also removes the `call_count` bookkeeping entirely.

---

## Info

### IN-01: Unused imports in `test_services.py`

**File:** `apps/workflow/tests/test_services.py:9,19`
**Issue:** Two symbols are imported but never referenced in the file:
- Line 9: `MagicMock` from `unittest.mock`
- Line 19: `SUBMIT` from `apps.workflow.constants`

**Fix:** Remove both unused imports:

```python
from unittest.mock import patch  # remove MagicMock

from apps.workflow.constants import (
    APPROVED, DRAFT, PENDING_APPROVAL, PERMANENTLY_REJECTED, REWORK,
    PERMANENTLY_REJECT, APPROVE,  # remove SUBMIT
)
```

---

### IN-02: Raw action string `"REWORK"` used instead of `REWORK_ACTION` constant

**File:** `apps/workflow/tests/test_services.py:178`
**Issue:** `TestTransitionJointStatusParity.test_rework_transitions_both_pl_and_ci` passes `action="REWORK"` as a raw string. The correct constant for the REWORK *action* is `REWORK_ACTION` (defined in `apps/workflow/constants.py`). The imported `REWORK` at line 18 is the *status* constant, not the action. Both evaluate to `"REWORK"` today, but this is a semantic confusion — if these values were ever decoupled, the test would silently pass with the wrong action string.

**Fix:** Import and use the action constant:

```python
# In the import block:
from apps.workflow.constants import (
    APPROVED, DRAFT, PENDING_APPROVAL, PERMANENTLY_REJECTED, REWORK,
    PERMANENTLY_REJECT, APPROVE, REWORK_ACTION,
)

# In the test:
WorkflowService.transition_joint(
    packing_list=pl,
    action=REWORK_ACTION,   # was "REWORK"
    performed_by=checker,
    comment="Quantities mismatch.",
)
```

---

### IN-03: Hardcoded status strings in `_make_pl_ci_pair` helper

**File:** `apps/packing_list/tests/test_views.py:1199,1208,1218`
**Issue:** The `_make_pl_ci_pair` helper in `TestPlCiPdfEdgeCases` uses bare string literals `"APPROVED"` and `"DRAFT"` for `status=` kwargs even though `APPROVED` and `DRAFT` are already imported at the top of the file from `apps.workflow.constants`. This is inconsistent with the rest of the test file and violates the project rule: *"Status strings in the frontend come from `src/utils/constants.ts`. Never hardcode 'DRAFT', 'APPROVED', etc."* — the same spirit applies to backend tests.

**Fix:**

```python
pi = ProformaInvoiceFactory(
    status=APPROVED,   # was "APPROVED"
    ...
)
pl_kwargs = {
    ...
    "status": DRAFT,   # was "DRAFT"
}
ci_kwargs = {
    ...
    "status": DRAFT,   # was "DRAFT"
}
```

---

### IN-04: `get_currency_display` has no None guard in `ProformaInvoiceListSerializer`

**File:** `apps/proforma_invoice/serializers.py:116`
**Issue:** `get_currency_display` on `ProformaInvoiceListSerializer` directly accesses `obj.currency.id`, `obj.currency.code`, and `obj.currency.name` without checking for `None`. The `currency` FK on the model is defined without `null=True`, so this cannot happen via normal API usage. However, if a data migration or direct DB manipulation leaves a row with `currency_id=NULL`, the serializer will raise `AttributeError` on any list request, taking down the entire PI list page. The companion method on `ProformaInvoiceSerializer` (line 415) has the same pattern.

**Fix:** Add a None guard consistent with how other FK name fields are handled in the same file:

```python
def get_currency_display(self, obj):
    if not obj.currency_id:
        return None
    return {"id": obj.currency.id, "code": obj.currency.code, "name": obj.currency.name}
```

---

### IN-05: Overly weak assertion in no-CI PATCH test

**File:** `apps/packing_list/tests/test_views.py:379`
**Issue:** `test_patch_pl_ci_fields_with_no_ci_does_not_crash` asserts only `resp.status_code != 500`. Any status code — including `400` or `200` — passes this assertion. The comment acknowledges this intentionally ("What matters is that no `AttributeError` is raised"), but because the test accepts any non-500 response, a future regression that returns, say, `404` would silently pass.

**Fix:** Tighten to the actually expected behaviour. Per the comment in the test, the guard `if update_fields and ci is not None` in `perform_update` should cause CI fields to be silently skipped, returning 200:

```python
# Assert the PL-level update succeeds and CI fields are silently skipped
assert resp.status_code == 200
```

If the intent is truly "any non-crash response is acceptable", at minimum document the acceptable range explicitly:

```python
assert resp.status_code in (200, 400), (
    f"Expected 200 or 400 when patching CI fields with no CI; got {resp.status_code}"
)
```

---

_Reviewed: 2026-06-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
