---
phase: 04-test-coverage
plan: "01"
subsystem: test-coverage
tags: [tests, permissions, packing-list, proforma-invoice, checker, serializer-safety]
dependency_graph:
  requires: []
  provides:
    - TestCheckerPermissionsOnPL (3 tests) in apps/packing_list/tests/test_views.py
    - TestPlWithoutCi (4 tests) in apps/packing_list/tests/test_views.py
    - TestCheckerCannotEditPI (2 tests) in apps/proforma_invoice/tests/test_views.py
  affects:
    - apps/packing_list/tests/test_views.py
    - apps/proforma_invoice/tests/test_views.py
tech_stack:
  added: []
  patterns:
    - pytest class-based test organisation with @pytest.mark.django_db
    - APIClient.force_authenticate() for role-based permission testing
    - factory-boy SubFactory pattern for related model setup
key_files:
  created: []
  modified:
    - apps/packing_list/tests/test_views.py
    - apps/proforma_invoice/tests/test_views.py
decisions:
  - New test classes added after their related predecessor classes to keep permission-denial tests co-located per permissions matrix
  - TestCheckerPermissionsOnPL intentionally overlaps with TestCheckerPermissions.test_checker_cannot_patch_pl — new class is the canonical permission-denial home
  - TestCheckerCannotEditPI.test_checker_cannot_patch_draft_pi intentionally overlaps with TestCompanyAdminPermissions.test_checker_cannot_update_draft_pi — same rationale
metrics:
  duration_minutes: 25
  completed_date: "2026-06-20"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
  tests_added: 9
---

# Phase 4 Plan 01: Checker Permission-Denial and PL Serializer Safety Tests Summary

**One-liner:** 9 new tests covering Checker edit/delete blocks on PL+PI and null-CI serializer safety returning None fields instead of 500.

---

## What Was Built

Two test files were extended with three new test classes covering the two highest-risk untested paths:

1. **Checker silently editing documents** — tests added to prove that Checker PATCH and DELETE on PL and PI return 403, not 200 or 500.
2. **PL serializer 500 when CI is missing** — tests added to prove `_get_ci()` returns `None` and the view never crashes on `None.ci_date`.

### New Test Classes

| Class | File | Tests |
|-------|------|-------|
| `TestCheckerPermissionsOnPL` | `apps/packing_list/tests/test_views.py` | 3 |
| `TestPlWithoutCi` | `apps/packing_list/tests/test_views.py` | 4 |
| `TestCheckerCannotEditPI` | `apps/proforma_invoice/tests/test_views.py` | 2 |
| **Total** | | **9** |

---

## Verification Results

```
pytest apps/packing_list/tests/test_views.py::TestCheckerPermissionsOnPL   → 3 passed
pytest apps/proforma_invoice/tests/test_views.py::TestCheckerCannotEditPI  → 2 passed
pytest apps/packing_list/tests/test_views.py::TestPlWithoutCi              → 4 passed
pytest apps/packing_list/tests/ apps/proforma_invoice/tests/ -q            → 255 passed (no regressions)
```

---

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 + Task 2 | d798b50 | test(04-01): add TestCheckerPermissionsOnPL + TestCheckerCannotEditPI + TestPlWithoutCi |

---

## Deviations from Plan

**None** — plan executed exactly as written. Tasks 1 and 2 were committed atomically in a single commit since both touched `apps/packing_list/tests/test_views.py` and were completed together before committing.

---

## Known Stubs

None — all new tests wire up real factory data and assert real endpoint responses. No hardcoded empty values or placeholder assertions.

---

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes introduced. Tests only.

---

## Self-Check: PASSED

- `apps/packing_list/tests/test_views.py` — FOUND (modified)
- `apps/proforma_invoice/tests/test_views.py` — FOUND (modified)
- Commit d798b50 — FOUND in git log
- 255 tests pass, 0 failures
