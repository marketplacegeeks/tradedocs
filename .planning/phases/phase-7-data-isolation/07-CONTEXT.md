# Phase 7: Data Isolation — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning

**Depends on:** Phase 6 must be complete — `Tenant` model, middleware, and `User.tenant` FK must exist before this phase starts.

<domain>
## Phase Boundary

Add `tenant` FK to every tenant-owned model, enforce isolation at the queryset layer via a shared mixin, fix per-tenant document number sequences, and verify no cross-tenant data leaks exist.

This phase does not touch the frontend or subdomain routing — that is Phase 8.

</domain>

<decisions>
## Implementation Decisions

### Models That Get tenant FK
- **D-01:** The following models each get `tenant = ForeignKey('tenants.Tenant', on_delete=models.PROTECT)`:
  - `ProformaInvoice` (`apps/proforma_invoice/models.py`)
  - `PackingList` (`apps/packing_list/models.py`)
  - `CommercialInvoice` (`apps/commercial_invoice/models.py`)
  - `CertificateOfAnalysis` (`apps/certificate_of_analysis/models.py`)
  - `PurchaseOrder` (`apps/purchase_order/models.py`)
  - `Organisation` (`apps/master_data/models.py`)
  - `Bank` (`apps/master_data/models.py`)
  - `TCTemplate` (`apps/master_data/models.py`)
  - `AuditLog` (`apps/workflow/models.py`)
- **D-02:** `on_delete=PROTECT` on all `tenant` FKs — consistent with all other FK constraints in the codebase (Section 9 rule #3).

### Global Master Data (No Tenant FK)
- **D-03:** The following remain global (shared across all tenants — no tenant FK added):
  - `Country`, `Port`, `Location`, `Currency`, `Incoterm`, `UOM`, `PaymentTerm`, `PreCarriageBy`, `TypeOfPackage`
  - `Product`, `ProductGrade`, `TestParameter`, `TestMethod`, `ProductTestTemplate`, `ProductTestTemplateRow`
  These are reference data — identical for all companies.

### Queryset Scoping
- **D-04:** Create a `TenantScopedMixin` (location TBD by planner — likely `apps/tenants/mixins.py`) that overrides `get_queryset()` to always call `.filter(tenant=self.request.tenant)`.
- **D-05:** Every viewset that operates on a tenant-scoped model must inherit `TenantScopedMixin`. No exceptions — a missing mixin is a data leak.

### Document Number Sequences
- **D-06:** `generate_document_number()` in PI, PL, and CI services currently counts all documents globally. It must be changed to count only documents belonging to `request.tenant` so each company's sequence starts at 0001 per year and is independent of other tenants.
- **D-07:** The `select_for_update()` lock pattern must be preserved — only the filter scope changes.

### Permission Classes
- **D-08:** `IsDocumentOwner` (and any object-level permission class) must add a tenant ownership check: `obj.tenant == request.tenant`. A user cannot access another tenant's document even if they somehow have the correct document ID.

### Data Migration
- **D-09:** A data migration script assigns `tenant_id` to all existing rows for each model listed in D-01. All existing rows get the Tenant #1 ID created in Phase 6.

### Testing
- **D-10:** Cross-tenant isolation tests are required before this phase is marked complete:
  - Create two tenants and two users (one per tenant)
  - Tenant A user attempts GET/POST/PATCH/DELETE on Tenant B's documents, orgs, banks — must all return 403 or 404
  - Tests live in each app's `tests/` directory

### Claude's Discretion
- Whether `TenantScopedMixin` lives in `apps/tenants/mixins.py` or a shared `utils/` module
- Whether to enforce the tenant FK at the serializer level (auto-set on create) or the view level
- Index strategy for `tenant` FK columns (planner decides based on query patterns)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Context (mandatory reading)
- `.planning/phases/phase-6-tenant-foundation/06-CONTEXT.md` — Tenant model design and middleware; this phase builds directly on it

### Project Rules
- `CLAUDE.md` — `on_delete=PROTECT` for all FK references; `WorkflowService` for all status transitions; `select_for_update()` for document number generation

### Existing Code (read before planning)
- `apps/proforma_invoice/models.py` — PI model; add `tenant` FK here
- `apps/packing_list/models.py` — PL model
- `apps/commercial_invoice/models.py` — CI model
- `apps/master_data/models.py` — Organisation, Bank, TCTemplate
- `apps/workflow/models.py` — AuditLog
- `apps/accounts/permissions.py` — `IsDocumentOwner` and `IsAnyRole`; both need tenant-awareness
- `apps/proforma_invoice/services.py` (or equivalent) — `generate_document_number()` needs tenant scoping

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing `on_delete=PROTECT` pattern — apply identically to all new `tenant` FKs
- `IsDocumentOwner` in `apps/accounts/permissions.py` — extend, don't replace

### Established Patterns
- `select_for_update()` in document number generation — preserve, only add `.filter(tenant=tenant)` to the count query
- Test factories in each app's `tests/factories.py` — will need a `TenantFactory` from Phase 6 as a `SubFactory`

### Integration Points
- Every viewset in `apps/proforma_invoice/views.py`, `apps/packing_list/views.py`, `apps/commercial_invoice/views.py`, `apps/certificate_of_analysis/views.py`, `apps/purchase_order/views.py`, `apps/master_data/views.py`, `apps/workflow/views.py` — all get `TenantScopedMixin`

</code_context>

<specifics>
## Specific Ideas

- `TenantScopedMixin.get_queryset()` should call `super().get_queryset().filter(tenant=self.request.tenant)` so it composes with any base queryset filtering already in the viewset
- On document create, `tenant` should be set automatically from `request.tenant` in the serializer's `create()` method — never passed from the client

</specifics>

<deferred>
## Deferred Ideas

- Row-level security at the Postgres level (in addition to Django queryset filtering) — out of scope for v1; could be added as a hardening layer later
- Tenant-specific master data overrides (e.g., a tenant adds custom UOMs) — out of scope

</deferred>

---

*Phase: 07-data-isolation*
*Context gathered: 2026-06-20*
