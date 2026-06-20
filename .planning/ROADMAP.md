# TradeDocs — GSD Roadmap

**Last Updated:** 2026-06-20

---

## Phase 0 — Reference Notes & Completed History ✅

**Purpose:** Permanent reference. All notes, permissions, architectural decisions, and completed-feature history that Claude needs to look up when working on TradeDocs.

**Contents:** `.planning/phases/phase-0-reference/`
- `NOTES.md` — permissions matrix, key architectural decisions, known gotchas
- `ci-bug-analysis.md` — CI quantity calculation bug root-cause analysis (pending business decision for fix)

**Status:** Complete (reference only — no implementation tasks)

---

## Phase 1 — CI Quantity Calculation Bug Fix 🔴 PENDING

**Goal:** Fix the Commercial Invoice `total_quantity` calculation so it sums `no_of_packages` (item count) instead of `net_material_weight` (KGS), then update tests.

**Requires:** User business decision — Option A (by item count) or Option B (by weight in UOM). Recommendation is **Option A**.

**Contents:** `.planning/phases/phase-1-ci-quantity-fix/PLAN.md`

**Status:** Awaiting sign-off, then 1-line backend fix + test update

---

## Phase 2 — Code Reliability 🔴 PENDING

**Goal:** Eliminate all broad `except Exception` blocks and silent failure paths across serializers, views, and services; fix null CI reference risk and orphan-CI bugs in destroy operations.

**Scope (from `.planning/codebase/CONCERNS.md`):**
- Replace broad `except Exception` → specific exception types (`ObjectDoesNotExist`, `ProtectedError`) in `apps/packing_list/serializers.py`, `apps/certificate_of_analysis/serializers.py`, `apps/packing_list/views.py`, `apps/workflow/services.py`
- Fix null CI reference risk at `apps/packing_list/views.py` lines 217–242 (AttributeError on `ci.ci_date` after `ci = None`)
- Fix Destroy operations at `apps/packing_list/views.py` lines 256–260, 407 — bare `except Exception: pass` leaves orphan CIs when `ProtectedError` is silently swallowed
- Fix `_get_ci()` serializer pattern (`apps/packing_list/serializers.py` lines 231–236) — add logger.warning on None
- Confirm `WorkflowService.transition_joint()` atomic block covers all PL+CI status paths

**Contents:** `.planning/phases/phase-2-code-reliability/`

**Plans:** 1 plan

Plans:
- [ ] 02-01-PLAN.md — Replace 7 broad `except Exception` blocks with specific types; fix null CI crash in perform_update; confirm transition_joint() atomic coverage

**Status:** Ready to execute

---

## Phase 3 — Security & Permission Hardening 🔴 PENDING

**Goal:** Close the Maker-Checker bypass risk and add rate limiting on document creation endpoints so no authenticated user can accidentally or maliciously exploit loose permission classes.

**Scope (from `.planning/codebase/CONCERNS.md`):**
- Audit `IsAnyRole` vs `IsDocumentOwner` usage — document why each view uses its class, enforce object-level permission where needed (`apps/accounts/permissions.py`, `apps/packing_list/views.py`, etc.)
- Add DRF throttling (`ScopedRateThrottle`) to PI/PL/CI creation endpoints in `apps/proforma_invoice/views.py`, `apps/packing_list/views.py`, `apps/commercial_invoice/views.py`
- Add permission tests: Checker cannot edit/delete documents; only creator or Admin can edit DRAFT; no self-approval (FR-08.2)

**Contents:** `.planning/phases/phase-3-security-permissions/`

**Plans:** 3 plans

Plans:
- [ ] 03-01-PLAN.md — Add IsMakerOrAdmin permission class + ScopedRateThrottle config in settings.py
- [ ] 03-02-PLAN.md — Wire get_permissions() on all document viewsets (PI, PL, CI, COA)
- [ ] 03-03-PLAN.md — Add TestCheckerPermissions and TestSelfApprovalPrevented tests across all 4 apps

**Status:** Ready to execute

---

## Phase 4 — Test Coverage Hardening 🔴 PENDING

**Goal:** Fill the high-priority test gaps identified by the codebase audit — especially around exception paths, workflow cascade failures, and permission enforcement — so silent production failures are caught by CI.

**Scope (from `.planning/codebase/CONCERNS.md`):**
- PL without CI (orphaned state): serializer getters when CI is None, CI deletion triggering PL update
- Joint PL+CI workflow cascade: verify PL and CI statuses always change together; test cascade when linked document is in `PERMANENTLY_REJECTED` state
- Permission enforcement: Checker cannot edit/delete; no self-approval; `IsAnyRole` + manual role check coverage
- PDF edge cases: very long company names/addresses, missing optional fields
- Concurrent document creation: race conditions in `select_for_update()` blocks

**Contents:** `.planning/phases/phase-4-test-coverage/`

**Status:** Planned

---

## Phase 5 — Missing Critical Features 🔴 PENDING

**Goal:** Add the three features that are absent from the system but block operational workflows: audit trail search, bulk document operations, and status-change notifications.

**Scope (from `.planning/codebase/CONCERNS.md`):**
- **Audit trail search:** `AuditLogViewSet` with filtering on `document_id`, `document_type`, `performed_by`, `action` — enables compliance reporting and change tracing
- **Bulk workflow operations:** `POST /proforma-invoices/bulk-workflow/` (and equivalent for PL/CI) — reject/approve multiple documents at once; required for Checker workflows with 100+ documents
- **Change notifications:** Django signals → email (or webhook stub) when document status changes — enables async workflow without manual polling

**Contents:** `.planning/phases/phase-5-critical-features/`

**Status:** Planned

---

## Backlog (Not Yet Phased)

| Item | Source | Priority |
|---|---|---|
| Reports page (currently placeholder) | `requirements/reports.md` | Medium |
| Signed copy upload / download | `technical_architecture.md` Section 5 | Low |
| Performance: batch CI rebuild at commit time (vs per-operation) | `CONCERNS.md` | Low |
| Performance: annotate CI totals instead of serializer computation | `CONCERNS.md` | Low |
| Redis-based document number counter (high-concurrency scale) | `CONCERNS.md` | Low |
