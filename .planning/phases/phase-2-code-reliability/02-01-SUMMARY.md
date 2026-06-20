---
phase: 2
plan: "01"
subsystem: backend-reliability
tags: [exception-handling, packing-list, workflow, coa, bug-fix]
dependency_graph:
  requires: []
  provides: [specific-exception-handling, null-ci-safety, protected-error-propagation]
  affects: [apps/packing_list, apps/certificate_of_analysis, apps/workflow]
tech_stack:
  added: []
  patterns: [ObjectDoesNotExist-for-reverse-OneToOne, ProtectedError-propagation, conditional-CI-load]
key_files:
  modified:
    - apps/packing_list/serializers.py
    - apps/packing_list/views.py
    - apps/certificate_of_analysis/serializers.py
    - apps/workflow/services.py
decisions:
  - "Raise ValidationError in perform_update only when CI fields are present in the payload — avoids breaking PL-only patches on PLs without a linked CI (factory test scenario)"
  - "Use ObjectDoesNotExist (importable base class) rather than RelatedObjectDoesNotExist (accessor attribute only) per Django docs"
  - "ProtectedError intentionally not caught in perform_destroy and hard_delete — lets it propagate and roll back the atomic block, which is the correct behavior"
metrics:
  duration_minutes: 12
  completed_date: "2026-06-20"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 4
---

# Phase 2 Plan 01: Code Reliability Summary

**One-liner:** Replaced all broad `except Exception` blocks with `ObjectDoesNotExist` in four backend files; fixed null-CI AttributeError crash in perform_update; ensured ProtectedError propagates on destroy; confirmed transition_joint() atomic coverage.

---

## Tasks Completed

| Task | Title | Commit | Files |
|------|-------|--------|-------|
| 2.1 | Fix exception handling in packing_list/serializers.py | `60ab499` | apps/packing_list/serializers.py |
| 2.2 | Fix null CI reference and destroy safety in packing_list/views.py | `e1b975d` | apps/packing_list/views.py |
| 2.3 | Fix COA serializers and workflow services; audit transition_joint() | `f9db700` | apps/certificate_of_analysis/serializers.py, apps/workflow/services.py |

---

## Files Modified and Exact Changes

### apps/packing_list/serializers.py

- **Imports added:** `import logging`, `from django.core.exceptions import ObjectDoesNotExist`
- **Line after imports:** `logger = logging.getLogger(__name__)`
- **PackingListListSerializer.get_ci_number (line ~131):** `except Exception` replaced with `except ObjectDoesNotExist`
- **PackingListSerializer._get_ci (line ~239):** `except Exception` replaced with `except ObjectDoesNotExist`; added `logger.warning("CI missing for PL %s — expected in production", obj.pk)`

### apps/packing_list/views.py

- **Imports added:** `from django.core.exceptions import ObjectDoesNotExist`; `ProtectedError` added to `from django.db.models import Prefetch, ProtectedError`
- **perform_update:** Added `ci_has_updates` guard — CI is only fetched and validated when the payload contains CI fields. When CI is missing and CI fields are present, raises `ValidationError` instead of silently setting `ci = None` which then crashes on `ci.ci_date`.
- **perform_destroy:** `except Exception: pass` replaced with `except ObjectDoesNotExist: pass` with explanatory comment. `ProtectedError` now propagates naturally and rolls back the atomic block.
- **hard_delete:** Same `except ObjectDoesNotExist` pattern as perform_destroy.
- Removed redundant `and ci is not None` guard on the `if update_fields` check (unreachable after the fix).

### apps/certificate_of_analysis/serializers.py

- **Import added:** `from django.core.exceptions import ObjectDoesNotExist`
- **CertificateOfAnalysisSerializer.get_ci_number (line ~100):** `except Exception` replaced with `except ObjectDoesNotExist`

### apps/workflow/services.py

- **Import added:** `from django.core.exceptions import ObjectDoesNotExist`
- **transition_joint() CI load (line ~178):** `except Exception` replaced with `except ObjectDoesNotExist`
- **Line before transaction.atomic():** Added two-line inline comment confirming all PL+CI status updates and AuditLog entries are within the atomic block

---

## Exception Types Used and Why

| Exception | Used For | Why |
|-----------|----------|-----|
| `ObjectDoesNotExist` | Reverse OneToOne accessor failures (`pl.commercial_invoice`) | Importable base class from `django.core.exceptions`; `PackingList.commercial_invoice.RelatedObjectDoesNotExist` is a subclass, so this catches it correctly |
| `ProtectedError` | FK PROTECT constraint violations on CI.delete() | Intentionally NOT caught — must propagate to roll back the atomic block and prevent orphaned records |

---

## Test Suite Result

**605 tests, 0 failures** (confirmed with `pytest --tb=short -q`)

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Conditional CI load in perform_update**

- **Found during:** Task 2.2 — one test failed after initially applying the plan's exact fix
- **Issue:** The plan specified: always load CI and raise ValidationError if missing. But `PackingListFactory` creates PLs without a linked CI, and `test_creator_can_patch_in_draft` patches only `vessel_flight_no` (a PL-native field, no CI fields). The original plan's fix caused a 400 for what should be a 200.
- **Root cause:** In production, every PL always has a linked CI (created atomically in `perform_create`). But tests using `PackingListFactory` directly may not. More importantly, if no CI fields are in the payload, there is no reason to access the CI at all.
- **Fix:** Added `ci_has_updates = any(v is not None for v in ci_data.values())` guard before the atomic block. CI is only loaded and validated when the request payload actually contains CI fields. This preserves the crash-prevention goal (null CI + CI field update = ValidationError) while not breaking PL-only patches.
- **Files modified:** `apps/packing_list/views.py`
- **Commit:** `e1b975d`

---

## Known Stubs

None — all changes are targeted bug fixes with no placeholder values.

---

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. All changes are internal exception-handling fixes within existing endpoints.

---

## Self-Check: PASSED

- `apps/packing_list/serializers.py` — modified in commit `60ab499` (verified)
- `apps/packing_list/views.py` — modified in commit `e1b975d` (verified)
- `apps/certificate_of_analysis/serializers.py` — modified in commit `f9db700` (verified)
- `apps/workflow/services.py` — modified in commit `f9db700` (verified)
- All commits confirmed in `git log`: `60ab499`, `e1b975d`, `f9db700`
- 605 tests pass, 0 failures
