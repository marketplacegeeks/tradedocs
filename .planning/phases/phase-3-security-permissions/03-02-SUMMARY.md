---
phase: 3
plan: "02"
subsystem: security-permissions
tags: [permissions, throttling, drf, security, get_permissions]
dependency_graph:
  requires:
    - 03-01 (IsMakerOrAdmin permission class, ScopedRateThrottle settings)
  provides:
    - get_permissions() on ProformaInvoiceViewSet (apps/proforma_invoice/views.py)
    - get_permissions() on PackingListViewSet, ContainerViewSet, ContainerItemViewSet (apps/packing_list/views.py)
    - get_permissions() on CommercialInvoiceViewSet, CommercialInvoiceLineItemViewSet (apps/commercial_invoice/views.py)
    - get_permissions() on CertificateOfAnalysisViewSet (apps/certificate_of_analysis/views.py)
  affects:
    - All document creation/edit/delete endpoints now enforce IsMakerOrAdmin at DRF routing layer
tech_stack:
  added: []
  patterns:
    - DRF get_permissions() per-action permission dispatch
    - Explicit IsAuthenticated in every get_permissions() return (CLAUDE.md rule #10 per-action equivalent)
    - throttle_scope = "document_creation" on PI, PL, COA viewsets
key_files:
  created: []
  modified:
    - apps/proforma_invoice/views.py
    - apps/packing_list/views.py
    - apps/commercial_invoice/views.py
    - apps/certificate_of_analysis/views.py
    - apps/accounts/permissions.py (worktree: added IsMakerOrAdmin — plan-01 commits not in worktree)
    - tradetocs/settings.py (worktree: added ScopedRateThrottle — plan-01 commits not in worktree)
decisions:
  - get_permissions() pattern uses explicit IsAuthenticated in every return branch (not relying on global DEFAULT_PERMISSION_CLASSES)
  - hard_delete action on PI and PL viewsets handled explicitly in get_permissions() returning [IsAuthenticated, IsSuperAdmin] — prevents IsMakerOrAdmin from accidentally allowing Makers to hard-delete
  - APIView subclasses (LineItemListCreateView, LineItemDetailView, ChargeListCreateView, ChargeDetailView) NOT changed — their _check_editable methods already raise PermissionDenied for Checkers (second-layer guard sufficient for APIView which does not use get_permissions() routing)
  - CI viewset excludes "create" and "destroy" from IsMakerOrAdmin gate (both raise ValidationError regardless of role) — only "update"/"partial_update" restricted
  - COA workflow @action decorators updated from [IsAnyRole] to [IsAuthenticated, IsAnyRole] for CLAUDE.md rule #10 compliance
metrics:
  duration_minutes: 30
  completed_date: "2026-06-20"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 3 Plan 02: Wire get_permissions() on All Document Viewsets Summary

**One-liner:** Added DRF `get_permissions()` to all four document viewsets enforcing `[IsAuthenticated, IsMakerOrAdmin]` for write actions and `[IsAuthenticated, IsAnyRole]` for reads, with `throttle_scope` on PI, PL, and COA.

---

## What Was Built

### Task 1: PI and PL viewsets

**apps/proforma_invoice/views.py**

- Added `from rest_framework.permissions import IsAuthenticated` and `IsMakerOrAdmin` to imports
- Added `throttle_scope = "document_creation"` to `ProformaInvoiceViewSet`
- Added `get_permissions()` to `ProformaInvoiceViewSet`:
  - `hard_delete` action returns `[IsAuthenticated(), IsSuperAdmin()]`
  - create/update/partial_update/destroy returns `[IsAuthenticated(), IsMakerOrAdmin()]`
  - all other actions (list, retrieve, workflow, pdf, signed_copy, audit_log) return `[IsAuthenticated(), IsAnyRole()]`

**APIView subclasses (LineItemListCreateView, LineItemDetailView, ChargeListCreateView, ChargeDetailView):** No change made. Their `_check_editable` / `_get_objects` methods explicitly raise `PermissionDenied("Checkers cannot modify line items.")` / `PermissionDenied("Checkers cannot modify charges.")` for any user with `role == CHECKER`. These APIView classes use `permission_classes` (not `get_permissions()`), and the existing second-layer Checker guard is adequate. `permission_classes = [IsAnyRole]` remains — the manual check in the method body blocks Checkers on writes while allowing reads via GET.

**apps/packing_list/views.py**

- Added `from rest_framework.permissions import IsAuthenticated` and `IsMakerOrAdmin` to imports
- Added `throttle_scope = "document_creation"` to `PackingListViewSet`
- Added `get_permissions()` to `PackingListViewSet`:
  - `hard_delete` returns `[IsAuthenticated(), IsSuperAdmin()]`
  - create/update/partial_update/destroy returns `[IsAuthenticated(), IsMakerOrAdmin()]`
  - reads return `[IsAuthenticated(), IsAnyRole()]`
- Added `get_permissions()` to `ContainerViewSet` (same write/read pattern)
- Changed `ContainerViewSet.copy` `@action` decorator from `permission_classes=[IsAnyRole]` to `permission_classes=[IsAuthenticated, IsMakerOrAdmin]` — copying is a write operation that creates a new Container
- Added `get_permissions()` to `ContainerItemViewSet` (same write/read pattern)

**_check_pl_editable behavior (ContainerViewSet):** Confirmed raises `PermissionDenied("Checkers cannot modify containers.")` for `role == CHECKER`. Retained as second layer.

**ContainerItemViewSet._check_editable behavior:** Confirmed raises `PermissionDenied("Checkers cannot modify container items.")` for `role == CHECKER`. Retained as second layer.

- Commit: `7048c45`

### Task 2: CI and COA viewsets

**apps/commercial_invoice/views.py**

- Added `from rest_framework.permissions import IsAuthenticated` and `IsMakerOrAdmin` to imports
- Added `get_permissions()` to `CommercialInvoiceViewSet`:
  - update/partial_update returns `[IsAuthenticated(), IsMakerOrAdmin()]`
  - all other actions return `[IsAuthenticated(), IsAnyRole()]`
  - Note: `create` and `destroy` are NOT in the IsMakerOrAdmin gate — both raise `ValidationError` for all roles regardless
- Added `get_permissions()` to `CommercialInvoiceLineItemViewSet`:
  - update/partial_update returns `[IsAuthenticated(), IsMakerOrAdmin()]`
  - all other actions return `[IsAuthenticated(), IsAnyRole()]`
- Existing `perform_update` creator checks retained as second layer on both viewsets

**apps/certificate_of_analysis/views.py**

- Added `from rest_framework.permissions import IsAuthenticated` and `IsMakerOrAdmin` to imports
- Added `throttle_scope = "document_creation"` to `CertificateOfAnalysisViewSet`
- Added `get_permissions()` to `CertificateOfAnalysisViewSet`:
  - create/update/partial_update/destroy returns `[IsAuthenticated(), IsMakerOrAdmin()]`
  - all other actions return `[IsAuthenticated(), IsAnyRole()]`
- Updated all `@action` decorators (submit, approve, reject, rework, pdf, audit-log) from `permission_classes=[IsAnyRole]` to `permission_classes=[IsAuthenticated, IsAnyRole]` for CLAUDE.md rule #10 compliance
- WorkflowService validates role internally for submit/approve/rework/reject — `IsAnyRole` is correct here (Checkers need to approve)
- Existing `perform_create` and `perform_update` role guards retained as second layer

- Commit: `d6fb1f4`

---

## _check_editable Behavior Summary

| Class | Method | Raises PermissionDenied for CHECKER? |
|---|---|---|
| `LineItemListCreateView` | `_check_editable` | YES — "Checkers cannot modify line items." |
| `LineItemDetailView` | `_get_objects` | YES — "Checkers cannot modify line items." |
| `ChargeListCreateView` | `_check_editable` | YES — "Checkers cannot modify charges." |
| `ChargeDetailView` | `_get_objects` | YES — "Checkers cannot modify charges." |
| `ContainerViewSet` | `_check_pl_editable` | YES — "Checkers cannot modify containers." |
| `ContainerItemViewSet` | `_check_editable` | YES — "Checkers cannot modify container items." |

All second-layer Checker guards confirmed present and retained.

---

## Test Results

```
605 passed, 0 failures (full suite)
```

PI + PL subset: 234 passed
CI + COA subset: 89 passed

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] IsMakerOrAdmin missing from worktree permissions.py**
- **Found during:** Task 1 (first test run)
- **Issue:** The worktree was branched before plan-01 commits landed. `apps/accounts/permissions.py` in the worktree had no `IsMakerOrAdmin` class, causing `ImportError` across all document app tests.
- **Fix:** Added `IsMakerOrAdmin` class to `apps/accounts/permissions.py` in the worktree, identical to the class defined in plan-01.
- **Files modified:** `apps/accounts/permissions.py`

**2. [Rule 3 - Blocking] ScopedRateThrottle settings missing from worktree settings.py**
- **Found during:** Task 1 (dependency check)
- **Issue:** Same worktree/branch gap — `tradetocs/settings.py` lacked `DEFAULT_THROTTLE_CLASSES` and `DEFAULT_THROTTLE_RATES`.
- **Fix:** Added both keys to `REST_FRAMEWORK` dict in `tradetocs/settings.py`, identical to plan-01 changes.
- **Files modified:** `tradetocs/settings.py`

**3. [Rule 1 - Bug] hard_delete action bypassed IsSuperAdmin when get_permissions() added**
- **Found during:** Task 1 test run (4 failures after initial fix)
- **Issue:** DRF's default `get_permissions()` reads `permission_classes` from the `@action` decorator. Our custom `get_permissions()` bypasses that mechanism — the `hard_delete` action's `permission_classes=[IsSuperAdmin]` was ignored, falling through to `[IsAuthenticated(), IsAnyRole()]` instead. Makers could hard-delete (tests expected 403, got 204).
- **Fix:** Added explicit `if self.action == "hard_delete": return [IsAuthenticated(), IsSuperAdmin()]` branch at the top of `get_permissions()` in both `ProformaInvoiceViewSet` and `PackingListViewSet`.
- **Files modified:** `apps/proforma_invoice/views.py`, `apps/packing_list/views.py`

---

## Known Stubs

None. This plan adds permission enforcement — no UI-facing data flows or new output.

---

## Threat Surface Scan

No new network endpoints introduced. All changes are permission enforcement on existing endpoints.

The `get_permissions()` pattern explicitly returns `IsAuthenticated()` in every branch — anonymous requests now receive 401 before the role check (closes T-3-09). Checker requests to write endpoints now receive 403 at DRF routing layer before `perform_create`/`perform_update` executes (closes T-3-04 through T-3-08). T-3-06 (ContainerViewSet.copy) now uses `[IsAuthenticated, IsMakerOrAdmin]` on the decorator.

No new threat flags.

---

## Self-Check: PASSED

- `apps/proforma_invoice/views.py` modified: FOUND (get_permissions at line 87, throttle_scope at line 79)
- `apps/packing_list/views.py` modified: FOUND (get_permissions at lines 86, 454, 548; throttle_scope at line 78)
- `apps/commercial_invoice/views.py` modified: FOUND (get_permissions at lines 46, 143)
- `apps/certificate_of_analysis/views.py` modified: FOUND (get_permissions at line 52, throttle_scope at line 43)
- Commit `7048c45`: FOUND
- Commit `d6fb1f4`: FOUND
- 605 tests pass, 0 failures
