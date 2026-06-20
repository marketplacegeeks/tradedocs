# Phase 6: Tenant Foundation — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-20
**Phase:** 06-tenant-foundation (covers scoping discussion for phases 6, 7, 8)
**Areas discussed:** DB Strategy, Tenant Routing, User Membership, Tenant Provisioning, Data Migration, Phase Breakdown

---

## DB Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Shared tables + tenant_id column | One DB, one set of tables, tenant FK on scoped models | ✓ |
| Separate Postgres schema per tenant | Each tenant gets its own schema; stronger isolation but much more complex | |
| Separate database per tenant | Complete physical isolation; expensive to operate | |

**User's choice:** Shared tables + tenant_id column
**Notes:** Simplest to build and maintain; appropriate for current scale.

---

## Tenant Routing

| Option | Description | Selected |
|--------|-------------|----------|
| Login screen — user picks their company | Single URL, tenant resolved from email | |
| Subdomain per tenant (acme.tradetocs.com) | Each company gets a subdomain; DNS + middleware resolves tenant | ✓ |
| URL path prefix (/acme/dashboard) | Tenant slug in URL path | |

**User's choice:** Subdomain per tenant
**Notes:** `acme.tradetocs.com` pattern. Requires wildcard TLS cert and Nginx wildcard routing in production.

---

## User Membership

| Option | Description | Selected |
|--------|-------------|----------|
| No — one user, one company (v1) | Email maps to exactly one tenant | ✓ |
| Yes — one user, multiple companies | Requires membership table and tenant switcher UI | |

**User's choice:** One user, one company for v1
**Notes:** Multi-tenant membership deferred to a future phase if needed.

---

## Tenant Provisioning

| Option | Description | Selected |
|--------|-------------|----------|
| Platform Super Admin only | Manual provisioning via Django admin or internal API | ✓ |
| Self-serve signup | Public /signup page; creates tenant on registration | |

**User's choice:** Platform Super Admin only
**Notes:** Managed B2B product; no self-serve in v1.

---

## Data Migration

| Option | Description | Selected |
|--------|-------------|----------|
| Migrate as Tenant #1 | All existing data assigned a tenant_id; zero data loss | ✓ |
| Start fresh | New multi-tenant instance; old data archived | |

**User's choice:** Migrate existing data as Tenant #1
**Notes:** Requires data migration scripts in both Phase 6 (users) and Phase 7 (documents + master data).

---

## Phase Breakdown

| Option | Description | Selected |
|--------|-------------|----------|
| 3 phases (6: Foundation, 7: Data Isolation, 8: Frontend) | Separate backend foundation, model scoping, and frontend work | ✓ |
| Combine 6+7 into one phase | Full backend in one phase | |

**User's choice:** 3-phase breakdown as proposed
**Notes:** Phase 6 = Tenant model + middleware + User FK. Phase 7 = all document/data model scoping. Phase 8 = frontend + security hardening.

---

## Claude's Discretion

- Exact middleware class name and placement
- Whether to put tenant resolution in middleware or DRF authentication class
- Management command naming for creating the first tenant admin
- TenantScopedMixin location (`apps/tenants/mixins.py` vs shared `utils/`)
- Index strategy for tenant FK columns

## Deferred Ideas

- Self-serve signup — future phase
- Multi-tenant user membership — future phase
- Billing/usage limits per tenant — future phase
- Tenant-branded login pages — future phase
- Wildcard cert auto-provisioning — infrastructure concern
