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
- [x] 02-01-PLAN.md — Replace 7 broad `except Exception` blocks with specific types; fix null CI crash in perform_update; confirm transition_joint() atomic coverage

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

**Plans:** 3 plans

Plans:
- [x] 04-01-PLAN.md — Checker permission-denial tests (PI + PL edit/delete) + PL-without-CI serializer safety tests
- [x] 04-02-PLAN.md — Create apps/workflow/tests/test_services.py: PI→PL→CI cascade + transition_joint() atomicity
- [x] 04-03-PLAN.md — PL+CI PDF edge-case tests (long names, null fields) + concurrent PI number uniqueness test

**Status:** Ready to execute

---

## Phase 5 — Missing Critical Features 🔴 PENDING

**Goal:** Add the three features that are absent from the system but block operational workflows: audit trail search, bulk document operations, and status-change notifications.

**Scope (from `.planning/codebase/CONCERNS.md`):**
- **Audit trail search:** `AuditLogViewSet` with filtering on `document_id`, `document_type`, `performed_by`, `action` — enables compliance reporting and change tracing
- **Bulk workflow operations:** `POST /proforma-invoices/bulk-workflow/` (and equivalent for PL/CI) — reject/approve multiple documents at once; required for Checker workflows with 100+ documents
- **Change notifications:** Django signals → email (or webhook stub) when document status changes — enables async workflow without manual polling

**Contents:** `.planning/phases/phase-5-critical-features/`

**Plans:** 3 plans

Plans:
- [ ] 05-01-PLAN.md — AuditLogViewSet (read-only, role-filtered, filterable) + frontend/src/api/auditLog.ts
- [ ] 05-02-PLAN.md — bulk-workflow @action on PI/PL/CI viewsets + frontend/src/api/bulkWorkflow.ts
- [ ] 05-03-PLAN.md — Django post_save signal on AuditLog → send_mail notifications + signal tests

**Status:** Ready to execute

---

## Phase 6 — Tenant Foundation 🔴 PENDING

**Goal:** Establish the multi-tenant data model — new Tenant entity, subdomain middleware, User→Tenant FK, and JWT tenant context. Migrate all existing single-tenant data to Tenant #1.

**Scope:**
- New `apps/tenants/` app with `Tenant` model (`name`, `slug`, `is_active`, `created_at`) — slug is the subdomain key (e.g. `acme` → `acme.tradetocs.com`)
- Django middleware: extract subdomain from `HTTP_HOST`, resolve `Tenant` record, attach to `request.tenant`; return 404 for unknown subdomains
- `ALLOWED_HOSTS` updated to accept `*.tradetocs.com` wildcard
- `User` model: add `tenant = ForeignKey(Tenant, null=True, on_delete=PROTECT)` — nullable so SUPER_ADMIN stays platform-level (no tenant)
- JWT: add `tenant_id` claim to token payload via `SIMPLE_JWT` custom serializer
- SUPER_ADMIN tenant management: Django admin interface for creating and disabling tenants
- Data migration script: create Tenant #1 record for existing company, assign all current User rows to it

**Contents:** `.planning/phases/phase-6-tenant-foundation/`

**Status:** Context gathered — ready to plan

---

## Phase 7 — Data Isolation 🔴 PENDING

**Goal:** Scope every tenant-owned model behind a `tenant` FK and enforce isolation at the queryset layer so cross-tenant data leaks are structurally impossible — not just by convention.

**Scope:**
- Add `tenant = ForeignKey(Tenant, on_delete=PROTECT)` to: `ProformaInvoice`, `PackingList`, `CommercialInvoice`, `CertificateOfAnalysis`, `PurchaseOrder`, `Organisation`, `Bank`, `TCTemplate`, `AuditLog`
- `TenantScopedMixin` for all viewsets — overrides `get_queryset()` to always `.filter(tenant=request.tenant)`
- `generate_document_number()` in PI/PL/CI services: scope `select_for_update()` count query to current tenant (each company restarts at 0001 per year)
- `IsDocumentOwner` permission class: add `document.tenant == request.tenant` guard
- Data migration script: assign `tenant_id` to all existing document and master data rows
- Cross-tenant isolation tests: Tenant A user cannot GET/PATCH/DELETE Tenant B documents, organisations, or banks

**Contents:** `.planning/phases/phase-7-data-isolation/`

**Status:** Context gathered — ready to plan

---

## Phase 8 — Frontend Integration & Security Hardening 🔴 PENDING

**Goal:** Make the frontend subdomain-aware, wire the login flow to subdomain-resolved tenants, lock down CORS and host settings, and confirm cross-tenant isolation with an end-to-end audit.

**Scope:**
- Frontend API base URL: derive from `window.location.hostname` at runtime instead of hardcoded env var — `src/api/client.ts`
- Login page: tenant resolved from subdomain; show "Company not found" error page for unknown subdomains
- CORS: add `CORS_ALLOWED_ORIGIN_REGEXES` for `*.tradetocs.com`; remove any wildcard `CORS_ALLOW_ALL_ORIGINS = True`
- Django settings hardening: `ALLOWED_HOSTS = ["*.tradetocs.com", "localhost", "127.0.0.1"]`
- Security audit: two-tenant E2E test suite verifying isolation of documents, orgs, banks, audit logs — must all pass before phase is complete
- Deployment notes: wildcard TLS cert (`*.tradetocs.com`) required; Nginx wildcard subdomain routing config

**Contents:** `.planning/phases/phase-8-frontend-multitenant/`

**Status:** Context gathered — ready to plan

---

## Backlog (Not Yet Phased)

| Item | Source | Priority |
|---|---|---|
| Reports page (currently placeholder) | `requirements/reports.md` | Medium |
| Signed copy upload / download | `technical_architecture.md` Section 5 | Low |
| Performance: batch CI rebuild at commit time (vs per-operation) | `CONCERNS.md` | Low |
| Performance: annotate CI totals instead of serializer computation | `CONCERNS.md` | Low |
| Redis-based document number counter (high-concurrency scale) | `CONCERNS.md` | Low |
