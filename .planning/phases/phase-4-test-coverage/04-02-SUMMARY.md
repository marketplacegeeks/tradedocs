---
phase: 04-test-coverage
plan: 02
subsystem: workflow
tags: [tests, workflow, cascade, atomicity, tdd]
dependency_graph:
  requires: []
  provides: [workflow-cascade-tests, transition-joint-atomicity-tests]
  affects: [apps/workflow/tests/test_services.py]
tech_stack:
  added: []
  patterns: [pytest-django, unittest.mock.patch, factory-boy SubFactory]
key_files:
  created:
    - apps/workflow/tests/test_services.py
  modified: []
decisions:
  - Used patch.object on CommercialInvoice.save (class-level, filtered by pk) for atomic rollback test to avoid affecting other CI saves during the test
  - Tests call WorkflowService directly (not via HTTP) for speed and isolation from URL routing
metrics:
  duration: "~8 minutes"
  completed: "2026-06-20"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 1
requirements:
  - PHASE4-P2-cascade-pi-to-pl-and-ci
  - PHASE4-P3-joint-workflow-status-parity
  - PHASE4-P3-atomic-rollback
---

# Phase 4 Plan 02: WorkflowService Cascade + Atomicity Tests Summary

**One-liner:** 6 service-level tests covering PI→PL→CI cascade, already-rejected skip guard, per-document AuditLog, APPROVE/REWORK status parity, and transaction.atomic() rollback on CI save failure.

---

## What Was Built

Created `apps/workflow/tests/test_services.py` — a new file that was absent before this plan.

### TestWorkflowCascade (3 tests)
Tests that call `WorkflowService.transition()` directly and verify the cascade chain triggered by `_cascade_permanently_rejected()`:

1. **test_permanently_rejecting_pi_cascades_to_linked_ci** — PI (APPROVED) → PERMANENTLY_REJECT triggers cascade; verifies PI, PL, and CI all end in PERMANENTLY_REJECTED. Complements the existing HTTP-layer test in `test_views.py` which only checked PL.
2. **test_permanently_rejecting_already_rejected_pl_is_skipped** — PL already in PERMANENTLY_REJECTED when PI cascade fires; confirms `.exclude(status=PERMANENTLY_REJECTED)` guard prevents ValidationError.
3. **test_cascade_writes_audit_log_for_each_document** — Verifies each of the three documents in the cascade chain gets its own AuditLog entry with the correct `document_type`.

### TestTransitionJointStatusParity (3 tests)
Tests for `WorkflowService.transition_joint()`:

4. **test_approve_transitions_both_pl_and_ci** — APPROVE action moves both PL and CI from PENDING_APPROVAL to APPROVED simultaneously; asserts `pl.status == ci.status == APPROVED`.
5. **test_rework_transitions_both_pl_and_ci** — REWORK action moves both PL and CI to REWORK simultaneously.
6. **test_transition_joint_is_atomic_ci_failure_rolls_back_pl** — Patches `CommercialInvoice.save` to raise `IntegrityError` after PL has been saved. Asserts PL status is unchanged after the exception (transaction rolled back).

---

## Verification Results

```
pytest apps/workflow/tests/test_services.py -v
→ 6 passed, 0 failed

pytest --tb=short -q
→ 632 passed, 0 failed (full suite, up from 605+)
```

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Known Stubs

None.

---

## Threat Flags

None — this plan adds tests only. No new network endpoints, auth paths, or schema changes introduced.

---

## Self-Check: PASSED

- `apps/workflow/tests/test_services.py` exists: FOUND
- Task commit `81a0f6c` exists: FOUND
- 6 tests pass, 0 failures: CONFIRMED
- Full suite 632 passed: CONFIRMED
