# Phase 8: Frontend Integration & Security Hardening — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning

**Depends on:** Phase 6 (Tenant model + middleware) and Phase 7 (data isolation + queryset scoping) must be complete.

<domain>
## Phase Boundary

Make the frontend subdomain-aware, wire the login flow to subdomain-resolved tenants, lock down CORS and host settings, and confirm cross-tenant isolation with an end-to-end security audit.

</domain>

<decisions>
## Implementation Decisions

### Frontend API Base URL
- **D-01:** The API base URL in `src/api/` must be derived from `window.location.hostname` at runtime — not hardcoded or sourced from a build-time env var.
- **D-02:** Logic: if hostname is `acme.tradetocs.com`, the API base is `https://acme.tradetocs.com/api/` (same subdomain, same origin). This means the backend must also be served on the same subdomain — no cross-subdomain API calls.

### Login Flow
- **D-03:** The login page resolves the tenant from the current subdomain automatically. The user just enters email + password; the frontend sends the subdomain slug alongside credentials so the backend can validate tenant membership.
- **D-04:** If a user navigates to an unknown subdomain (slug not in DB), show a clear "Company not found" error page — not a generic 404.
- **D-05:** After login, JWT tokens carry `tenant_id` and `tenant_slug` (set in Phase 6). The frontend stores and sends these as normal — no extra tenant-selection UI needed (one user = one company).

### Django Settings Hardening
- **D-06:** `ALLOWED_HOSTS` in `settings.py`: `["*.tradetocs.com", "tradetocs.com", "localhost", "127.0.0.1"]`
- **D-07:** CORS: replace any `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://.*\.tradetocs\.com$"]`
- **D-08:** `SESSION_COOKIE_DOMAIN` and `CSRF_COOKIE_DOMAIN` set to `.tradetocs.com` (leading dot covers all subdomains)

### Security Audit (Required Gate)
- **D-09:** A two-tenant E2E test suite must pass before this phase is marked complete. Tests must cover:
  - Tenant A user's JWT cannot be used on Tenant B's subdomain
  - Direct API calls with Tenant A credentials to Tenant B document IDs return 403 or 404
  - Tenant A's organisations, banks, and audit log are invisible to Tenant B
- **D-10:** These tests live in a new `tests/test_cross_tenant_security.py` at the project root or in `apps/tenants/tests/`.

### Deployment Notes (Out of Scope for This Phase — Document Only)
- **D-11:** Wildcard TLS cert (`*.tradetocs.com`) is required in production — document this as a deployment prerequisite, do not implement certificate provisioning in code.
- **D-12:** Nginx wildcard subdomain routing config must be documented — not implemented in this phase.

### Claude's Discretion
- Exact implementation of subdomain extraction on the frontend (`window.location.hostname.split('.')`)
- Whether "Company not found" is a React route or a pre-React HTML page served by Django

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Context (mandatory reading)
- `.planning/phases/phase-6-tenant-foundation/06-CONTEXT.md` — Tenant model, middleware, JWT claims
- `.planning/phases/phase-7-data-isolation/07-CONTEXT.md` — Queryset scoping and cross-tenant permission checks

### Project Rules
- `CLAUDE.md` — All Axios calls live in `src/api/*.ts`; no component calls Axios directly; status strings from `src/utils/constants.ts`

### Existing Frontend Code (read before planning)
- `frontend/src/api/` — all API client files; base URL config lives here
- `frontend/src/pages/` — login page implementation
- `tradetocs/settings.py` — `ALLOWED_HOSTS`, `CORS_*`, `SESSION_COOKIE_*` settings

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing Axios client in `src/api/` — just update the base URL derivation
- JWT handling already in place — `tenant_id` claim added in Phase 6 flows through automatically

### Established Patterns
- All API calls in `src/api/*.ts` — keep this; no new pattern needed
- Constants in `src/utils/constants.ts` — any tenant-related UI strings go here

### Integration Points
- `frontend/src/api/` base URL config — primary change point
- `tradetocs/settings.py` — `ALLOWED_HOSTS` and CORS settings
- Login page in `frontend/src/pages/` — add "Company not found" branch

</code_context>

<specifics>
## Specific Ideas

- "Company not found" error page should be simple — just a message and a link to the main marketing site, not a full app shell
- The frontend subdomain extraction: `const slug = window.location.hostname.split('.')[0]` — works for `acme.tradetocs.com`, returns `localhost` on local dev (needs a dev fallback)

</specifics>

<deferred>
## Deferred Ideas

- Tenant-branded login pages (custom logo/colour per company) — out of scope for v1
- Wildcard cert auto-provisioning via Let's Encrypt / cert-manager — infrastructure concern, not application code
- Tenant admin portal (COMPANY_ADMIN self-service user management UI) — could be a future phase

</deferred>

---

*Phase: 08-frontend-multitenant*
*Context gathered: 2026-06-20*
