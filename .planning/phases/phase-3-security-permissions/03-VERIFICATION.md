---
phase: 03-security-permissions
verified: 2026-06-20T12:00:00Z
status: passed
score: 12/12 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 11/12
  gaps_closed:
    - "SUPER_ADMIN can edit Commercial Invoice and CI line items (no object-level bypass)"
  gaps_remaining: []
  regressions: []
---

# Phase 3: Security & Permission Hardening Verification Report

**Phase Goal:** Close the Maker-Checker bypass risk and add rate limiting on document creation endpoints so no authenticated user can accidentally or maliciously exploit loose permission classes.
**Verified:** 2026-06-20
**Status:** passed
**Re-verification:** Yes — after gap closure (CR-01 fix applied)

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | IsMakerOrAdmin permission class exists and is importable | VERIFIED | `apps/accounts/permissions.py` line 47 — class body correctly enforces MAKER + COMPANY_ADMIN + SUPER_ADMIN |
| 2  | DRF ScopedRateThrottle configured globally with document_creation scope at 100/day | VERIFIED | `tradetocs/settings.py` lines 100–105 — DEFAULT_THROTTLE_CLASSES and DEFAULT_THROTTLE_RATES both present |
| 3  | WorkflowService.transition() enforces FR-08.2 self-approval guard | VERIFIED | `apps/workflow/services.py` line 81 — `PermissionDenied("You cannot approve a document you created.")` |
| 4  | WorkflowService.transition_joint() also enforces FR-08.2 self-approval guard | VERIFIED | `apps/workflow/services.py` line 162 — same guard present |
| 5  | Checker calling POST /api/v1/proforma-invoices/ receives 403 | VERIFIED | `TestCheckerPermissions::test_checker_cannot_create_pi` PASSED |
| 6  | Checker calling PATCH /api/v1/packing-lists/{id}/ receives 403 | VERIFIED | `TestCheckerPermissions::test_checker_cannot_patch_pl` PASSED |
| 7  | Checker calling PATCH /api/v1/commercial-invoices/{id}/ receives 403 | VERIFIED | `TestCheckerPermissions::test_checker_cannot_patch_ci` PASSED |
| 8  | Checker calling POST /api/v1/coas/ receives 403 | VERIFIED | `TestCheckerPermissions::test_checker_cannot_create_coa` PASSED |
| 9  | GET/list endpoints return 200 for all authenticated roles | VERIFIED | `test_checker_can_list_pi`, `test_checker_can_list_pl`, `test_checker_can_list_ci`, `test_checker_can_list_coa` all PASSED |
| 10 | Maker cannot self-approve (WorkflowService raises 403) | VERIFIED | `TestSelfApprovalPrevented::test_maker_cannot_self_approve` PASSED |
| 11 | All 605+ pre-existing tests still pass after additions | VERIFIED | Full suite: 626 passed, 0 failures |
| 12 | SUPER_ADMIN can edit Commercial Invoice and CI line items (no object-level bypass) | VERIFIED | `apps/commercial_invoice/views.py` lines 86 and 171 — `role not in (UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN)` — SUPER_ADMIN now correctly bypasses creator check. `test_super_admin_can_patch_ci` PASSED. |

**Score: 12/12 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/accounts/permissions.py` | IsMakerOrAdmin permission class | VERIFIED | Line 47 — class exists, has_permission() checks MAKER + _ADMIN_ROLES tuple correctly |
| `tradetocs/settings.py` | ScopedRateThrottle config with document_creation: 100/day | VERIFIED | Lines 100–105 — DEFAULT_THROTTLE_CLASSES and DEFAULT_THROTTLE_RATES present |
| `apps/workflow/services.py` | Self-approval guard in both transition methods | VERIFIED | Lines 81 and 162 — grep -c returns 2 |
| `apps/proforma_invoice/views.py` | get_permissions() on ProformaInvoiceViewSet + throttle_scope | VERIFIED | Line 79 throttle_scope; lines 86–94 get_permissions() — hard_delete, write, and read cases all handled |
| `apps/packing_list/views.py` | get_permissions() on PackingListViewSet, ContainerViewSet, ContainerItemViewSet + throttle_scope | VERIFIED | Line 79 throttle_scope; lines 86, 468, 567 get_permissions(); ContainerViewSet.copy action uses [IsAuthenticated, IsMakerOrAdmin] |
| `apps/commercial_invoice/views.py` | get_permissions() on CommercialInvoiceViewSet and CommercialInvoiceLineItemViewSet; SUPER_ADMIN bypass in perform_update() | VERIFIED | Lines 46 and 143 get_permissions() correct; lines 86 and 171 now use `not in (UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN)` |
| `apps/certificate_of_analysis/views.py` | get_permissions() on CertificateOfAnalysisViewSet + throttle_scope | VERIFIED | Line 43 throttle_scope; line 52 get_permissions(); workflow @action decorators updated to [IsAuthenticated, IsAnyRole] |
| `apps/proforma_invoice/tests/test_views.py` | TestCheckerPermissions + TestSelfApprovalPrevented | VERIFIED | Lines 1658 and 1709 — 6 + 2 = 8 new tests, all PASSED |
| `apps/packing_list/tests/test_views.py` | TestCheckerPermissions | VERIFIED | Line 994 — 4 new tests, all PASSED |
| `apps/commercial_invoice/tests/test_views.py` | TestCheckerPermissions (including test_super_admin_can_patch_ci) | VERIFIED | 5 tests total in TestCheckerPermissions — all PASSED |
| `apps/certificate_of_analysis/tests/test_views.py` | TestCheckerPermissions | VERIFIED | Line 576 — 4 new tests, all PASSED |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `apps/accounts/permissions.py` | `apps/proforma_invoice/views.py` | `from apps.accounts.permissions import IsAnyRole, IsMakerOrAdmin, IsSuperAdmin` | WIRED | Line 24 of PI views |
| `apps/accounts/permissions.py` | `apps/packing_list/views.py` | `from apps.accounts.permissions import IsAnyRole, IsMakerOrAdmin, IsSuperAdmin` | WIRED | Line 21 of PL views |
| `apps/accounts/permissions.py` | `apps/commercial_invoice/views.py` | `from apps.accounts.permissions import IsAnyRole, IsMakerOrAdmin` | WIRED | Line 19 of CI views |
| `apps/accounts/permissions.py` | `apps/certificate_of_analysis/views.py` | `from apps.accounts.permissions import IsAnyRole, IsMakerOrAdmin` | WIRED | Line 16 of COA views |
| `tradetocs/settings.py` | `ProformaInvoiceViewSet` | `throttle_scope = "document_creation"` | WIRED | Line 79 of PI views |
| `tradetocs/settings.py` | `PackingListViewSet` | `throttle_scope = "document_creation"` | WIRED | Line 79 of PL views |
| `tradetocs/settings.py` | `CertificateOfAnalysisViewSet` | `throttle_scope = "document_creation"` | WIRED | Line 43 of COA views |
| `ProformaInvoiceViewSet.get_permissions()` | `IsMakerOrAdmin` | Returns `[IsAuthenticated(), IsMakerOrAdmin()]` for write actions | WIRED | Lines 92–93 of PI views |
| `WorkflowService.transition() self-approval guard` | `FR-08.2` | `PermissionDenied` when `action==APPROVE and created_by==performed_by` | WIRED | Lines 76–82 of services.py |
| `TestCheckerPermissions::test_checker_cannot_create_pi` | `IsMakerOrAdmin in get_permissions()` | HTTP POST returning 403 confirmed | WIRED | Test passes — `assert resp.status_code == 403` |
| `test_maker_cannot_self_approve` | `WorkflowService.transition() self-approval guard` | HTTP POST to workflow returning 403 confirmed | WIRED | Test passes — `assert resp.status_code == 403` |
| `test_super_admin_can_patch_ci` | `perform_update() SUPER_ADMIN bypass` | HTTP PATCH by SUPER_ADMIN returning 200 | WIRED | Test passes — confirms CR-01 fix is effective |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase adds permission enforcement infrastructure and tests only. No UI-facing data flows or dynamic data rendering were introduced.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| IsMakerOrAdmin importable from accounts.permissions | `python -c "from apps.accounts.permissions import IsMakerOrAdmin; print('ok')"` | ok | PASS |
| ScopedRateThrottle config present in settings | `grep "ScopedRateThrottle" tradetocs/settings.py` | Match at line 101 | PASS |
| Self-approval guard count = 2 | `grep -c "You cannot approve a document you created" apps/workflow/services.py` | 2 | PASS |
| CI views.py uses `not in (COMPANY_ADMIN, SUPER_ADMIN)` on both perform_update lines | `grep -c "not in (UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN)" apps/commercial_invoice/views.py` | 2 | PASS |
| All TestCheckerPermissions tests pass (21 tests including new CI test) | `pytest -k "TestCheckerPermissions or TestSelfApprovalPrevented" -q` | 21 passed | PASS |
| Full test suite | `pytest --tb=short -q` | 626 passed, 0 failures | PASS |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| SEC-PERM-01 (internal planning ID) | 03-01, 03-02, 03-03 | Checkers blocked from write actions on all document viewsets | SATISFIED | IsMakerOrAdmin class enforces write restriction; get_permissions() wired on all 4 viewsets; Checker-denial tests pass. SUPER_ADMIN object-level bypass now correct on CI. |
| SEC-THROTTLE-01 (internal planning ID) | 03-01, 03-02, 03-03 | ScopedRateThrottle at 100/day on document creation endpoints | SATISFIED | settings.py configured; throttle_scope declared on PI, PL, COA viewsets |
| SEC-SELF-APPROVAL-01 (internal planning ID) | 03-03 | Maker cannot self-approve a document (FR-08.2) | SATISFIED | WorkflowService guard confirmed at lines 81 + 162; TestSelfApprovalPrevented passes |
| FR-08.2 (formal requirement) | 03-01, 03-03 | Common workflow rule: creator cannot approve own document | SATISFIED | WorkflowService.transition() and transition_joint() both enforce this; tests confirm |

**Note:** SEC-PERM-01, SEC-THROTTLE-01, and SEC-SELF-APPROVAL-01 are internal planning IDs derived from `.planning/codebase/CONCERNS.md` security findings — they do not appear in `requirements/requirements.md`. The formal backing requirement is FR-08.2. No orphaned requirements were found.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `apps/proforma_invoice/views.py` | 146, 176, 197, 256 | `permission_classes=[IsAnyRole]` on @action decorators (not `[IsAuthenticated, IsAnyRole]`) | Warning | CLAUDE.md rule #10 requires explicit permission_classes on every view. IsAnyRole already requires is_authenticated, so no security bypass — but the COA actions were updated to `[IsAuthenticated, IsAnyRole]` while PI and PL actions were not. Not a gap. |
| `apps/packing_list/views.py` | 289, 313, 349, 381, 440 | Same as above — @action decorators use `[IsAnyRole]` not `[IsAuthenticated, IsAnyRole]` | Warning | Same as PI — IsAnyRole checks authentication internally, so no bypass, but inconsistent with COA. Not a gap. |

No blockers remain. The CR-01 blocker from the initial verification has been closed.

---

### Human Verification Required

None. All verification points were checkable programmatically via grep, file inspection, and test execution.

---

### Gaps Summary

No gaps. All 12 must-have truths are verified.

The single gap from the initial verification (CR-01: SUPER_ADMIN blocked from editing Commercial Invoice and CI line items by an incomplete object-level role check) has been closed:

- `apps/commercial_invoice/views.py` line 86: changed to `not in (UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN)`
- `apps/commercial_invoice/views.py` line 171: same fix applied
- `test_super_admin_can_patch_ci` added to `TestCheckerPermissions` and PASSES (HTTP 200)
- Full suite: 626 passed, 0 failures (up from 625 before the new test was added)

---

_Verified: 2026-06-20T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
