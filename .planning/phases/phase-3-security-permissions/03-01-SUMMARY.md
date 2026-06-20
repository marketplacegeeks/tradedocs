---
phase: 3
plan: "01"
subsystem: security-permissions
tags: [permissions, throttling, workflow, security]
dependency_graph:
  requires: []
  provides:
    - IsMakerOrAdmin permission class (apps/accounts/permissions.py)
    - ScopedRateThrottle config (tradetocs/settings.py)
    - Verified self-approval guard in WorkflowService
  affects:
    - apps/proforma_invoice/views.py (plan 02 imports IsMakerOrAdmin)
    - apps/packing_list/views.py (plan 02 imports IsMakerOrAdmin)
    - apps/commercial_invoice/views.py (plan 02 imports IsMakerOrAdmin)
    - apps/certificate_of_analysis/views.py (plan 02 imports IsMakerOrAdmin)
tech_stack:
  added: []
  patterns:
    - DRF ScopedRateThrottle for per-scope rate limiting
    - DRF BasePermission subclass for role-based write access
key_files:
  created: []
  modified:
    - apps/accounts/permissions.py
    - tradetocs/settings.py
decisions:
  - IsMakerOrAdmin grants MAKER + COMPANY_ADMIN + SUPER_ADMIN (mirrors _ADMIN_ROLES tuple already in the file)
  - Throttle rate set to 100/day per user — generous for legitimate export trade, blocks programmatic flooding
  - Self-approval guard was already present in WorkflowService — no modification needed
metrics:
  duration_minutes: 20
  completed_date: "2026-06-20"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 2
---

# Phase 3 Plan 01: Permission Class + Throttle Foundation Summary

**One-liner:** Added `IsMakerOrAdmin` DRF permission class and `ScopedRateThrottle` config at 100/day; confirmed FR-08.2 self-approval guard already in `WorkflowService`.

---

## What Was Built

### Task 1: IsMakerOrAdmin permission class

Added to `apps/accounts/permissions.py` (appended after `IsDocumentOwner`):

```python
class IsMakerOrAdmin(BasePermission):
    """
    Grants write access to MAKER, COMPANY_ADMIN, and SUPER_ADMIN.
    Used by document viewsets to block Checkers from create/update/destroy actions.
    Checkers have read-only access to all documents; only Makers (and Admins) create/edit.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.MAKER, *_ADMIN_ROLES)
        )
```

- Allows: `MAKER`, `COMPANY_ADMIN`, `SUPER_ADMIN`
- Denies: `CHECKER` (will receive 403 on any write action)
- All 5 existing permission classes (`IsSuperAdmin`, `IsCompanyAdmin`, `IsCheckerOrAdmin`, `IsAnyRole`, `IsDocumentOwner`) unchanged
- Commit: `6b9fc8f`

### Task 2: ScopedRateThrottle config in settings.py

Added inside `REST_FRAMEWORK` dict in `tradetocs/settings.py`:

```python
"DEFAULT_THROTTLE_CLASSES": [
    "rest_framework.throttling.ScopedRateThrottle",
],
"DEFAULT_THROTTLE_RATES": {
    # Generous for legitimate export trade use; blocks programmatic spam.
    "document_creation": "100/day",
},
```

- No existing keys changed
- Viewsets will opt in by declaring `throttle_scope = "document_creation"` (wired in Plan 02)
- Django system check passes (0 issues)
- Commit: `ec98c91`

### Task 3: Self-approval guard verification (no code change)

Confirmed both FR-08.2 guards already present in `apps/workflow/services.py`:

- `transition()` — lines 74-82: checks `document.created_by == performed_by` when `action == APPROVE`
- `transition_joint()` — lines 158-162: checks `packing_list.created_by == performed_by` when `action == APPROVE`
- Both raise `PermissionDenied("You cannot approve a document you created.")`
- Both exempt `COMPANY_ADMIN` and `SUPER_ADMIN` from this restriction (trusted roles)
- `grep -c` count = 2 (matches acceptance criteria)
- No modification to `services.py` was needed

---

## Test Results

```
52 passed, 0 failures (apps/accounts/ + apps/workflow/)
```

---

## Deviations from Plan

None — plan executed exactly as written.

- Task 1: Append-only edit, no renames
- Task 2: Settings keys added as specified, no existing keys touched
- Task 3: Guard was already present — no implementation needed

---

## Known Stubs

None. This plan adds infrastructure (permission class, throttle config) — no UI-facing data flows.

---

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced.

`IsMakerOrAdmin` is a permission class (no new endpoint). `ScopedRateThrottle` reduces attack surface (rate limits). `WorkflowService` guard already existed.

No new threat flags.

---

## Self-Check: PASSED

- `apps/accounts/permissions.py` modified: FOUND (class IsMakerOrAdmin at line 47)
- `tradetocs/settings.py` modified: FOUND (ScopedRateThrottle at line 101, document_creation at line 105)
- Commit `6b9fc8f`: FOUND
- Commit `ec98c91`: FOUND
- 52 tests pass, 0 failures
