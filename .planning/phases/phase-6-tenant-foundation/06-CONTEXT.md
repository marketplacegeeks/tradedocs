# Phase 6: Tenant Foundation — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the multi-tenant foundation: a `Tenant` model, subdomain resolution middleware, User→Tenant FK, and JWT tenant context. Migrate all existing single-tenant data to Tenant #1.

This phase is backend-only. It does not touch document models or queryset scoping — that is Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Database Strategy
- **D-01:** Use **shared tables with a `tenant_id` FK column** on every tenant-scoped model. No separate schemas or separate databases.
- **D-02:** `SUPER_ADMIN` users are platform-level — their `tenant` FK is `null`. All other roles (COMPANY_ADMIN, CHECKER, MAKER) must have a non-null `tenant`.

### Tenant Model
- **D-03:** New `apps/tenants/` app with a `Tenant` model: `name` (CharField), `slug` (CharField unique — used as subdomain), `is_active` (BooleanField), `created_at` (DateTimeField auto).
- **D-04:** Tenant records are never hard-deleted — set `is_active=False` (same pattern as Organisation and User).

### Subdomain Routing
- **D-05:** Tenants are accessed via **subdomains**: `acme.tradetocs.com`. The slug on the Tenant model is the subdomain key.
- **D-06:** Django middleware reads `HTTP_HOST`, strips the subdomain, looks up the Tenant by slug, and attaches it to `request.tenant`. Returns HTTP 404 for unknown subdomains.
- **D-07:** `ALLOWED_HOSTS` in `settings.py` must accept `*.tradetocs.com` wildcard.

### User → Tenant
- **D-08:** `User` model gains `tenant = ForeignKey('tenants.Tenant', null=True, blank=True, on_delete=models.PROTECT)`. Nullable so SUPER_ADMIN can exist without a tenant.
- **D-09:** One user = one company. A user's email is globally unique and maps to exactly one tenant. No multi-tenant membership in v1.
- **D-10:** The existing `UserRole.SUPER_ADMIN` is the platform-level admin who creates tenants. This role stays. No new role is needed.

### JWT
- **D-11:** Add `tenant_id` as a custom claim in the JWT access token. Use `SIMPLE_JWT`'s `TOKEN_OBTAIN_SERIALIZER` override or a custom `MyTokenObtainPairSerializer` that adds `tenant_id` (and `tenant_slug` for convenience) to the token payload.
- **D-12:** The tenant middleware should also validate that the JWT `tenant_id` matches `request.tenant.id` on every authenticated request — prevents token reuse across subdomains.

### Tenant Provisioning (Onboarding)
- **D-13:** Only a **Platform Super Admin** can create tenants — via the Django admin panel. No self-serve signup in v1.
- **D-14:** When a new tenant is created, the Super Admin also creates the first COMPANY_ADMIN user for that tenant manually (or via a simple Django management command).

### Data Migration
- **D-15:** All existing data (current production state) is migrated to **Tenant #1**. A data migration script will:
  1. Create one `Tenant` record (name and slug to be configured at migration time)
  2. Set `tenant_id` on all existing `User` rows except any SUPER_ADMIN rows

### Claude's Discretion
- Exact middleware class name and placement in `MIDDLEWARE` setting
- Whether to put tenant resolution in middleware or a DRF authentication class
- Management command naming for creating the first tenant admin

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Rules
- `CLAUDE.md` — Non-negotiable technical rules (Section 9), especially: `on_delete=PROTECT` for all FK references to master data, `is_active=False` for soft-deletes, `WorkflowService` for all status transitions.

### Architecture
- `requirements/technical_architecture.md` — Full tech stack and DB schema constraints.

### Existing Code (read before planning)
- `apps/accounts/models.py` — Current `User` model; `tenant` FK must be added here.
- `tradetocs/settings.py` — `ALLOWED_HOSTS`, `SIMPLE_JWT` config, `MIDDLEWARE` list — all need updating.
- `tradetocs/urls.py` — Root URL conf; may need tenant-aware routing.

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `User` model (`apps/accounts/models.py`) — already uses `is_active` soft-delete pattern; `tenant` FK follows the same convention
- `UserRole.SUPER_ADMIN` — already exists as a global admin role; no new role needed, just ensure middleware skips tenant resolution for SUPER_ADMIN requests

### Established Patterns
- Soft-delete: all models use `is_active = BooleanField(default=True)` — Tenant follows this same pattern
- `on_delete=PROTECT` for FK references to master data — apply to `User.tenant` FK
- `db_table` naming: follow `{app}_{model}` convention, e.g. `tenants_tenant`

### Integration Points
- `MIDDLEWARE` in `tradetocs/settings.py` — tenant middleware inserts after `SessionMiddleware`, before `AuthenticationMiddleware`
- `SIMPLE_JWT` in `settings.py` — add `TOKEN_OBTAIN_SERIALIZER` override for custom claims
- `apps/accounts/views.py` login view — will need to validate tenant context on login

</code_context>

<specifics>
## Specific Ideas

- Subdomain example: `acme.tradetocs.com` where `acme` is `Tenant.slug`
- The middleware pattern is similar to `django-tenant-schemas` middleware but simpler — we're not doing schema switching, just attaching a tenant object to the request
- Django admin registration for Tenant model is the provisioning UI for v1

</specifics>

<deferred>
## Deferred Ideas

- Self-serve signup (visitor creates their own company) — explicitly out of scope for v1; could be Phase 9
- Multi-tenant user membership (one user, multiple companies) — out of scope for v1
- Billing / usage limits per tenant — out of scope for v1
- Tenant-level settings/config (e.g. custom logo, branding) — out of scope for v1

</deferred>

---

*Phase: 06-tenant-foundation*
*Context gathered: 2026-06-20*
