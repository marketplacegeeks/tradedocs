# Phase 0 — Reference Notes

Permanent reference for Claude. Look here before touching permissions, workflow rules, or architectural patterns.

---

## Permissions Matrix

Source-of-truth is `apps/workflow/constants.py` (backend) and `frontend/src/components/common/WorkflowActionButton.tsx` (frontend).

**Role hierarchy:** SUPER_ADMIN > COMPANY_ADMIN > CHECKER > MAKER

### Proforma Invoice

| Action | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:---:|:---:|:---:|
| List / View / PDF / Audit log | ✅ | ✅ | ✅ |
| Create PI | ✅ | ❌ | ✅ |
| Edit header / line items / charges (Draft or Rework) | ✅ | ❌ | ✅ |
| Submit for approval | ✅ | ❌ | ✅ |
| Approve (Pending Approval) | ✅ | ✅ | ❌ |
| Send for Rework — comment required | ✅ | ✅ | ❌ |
| Permanently Reject — comment required | ✅ | ✅ | ❌ |
| Upload signed copy (Approved only) | ✅ | ✅ | ✅ |

### Packing List + Commercial Invoice

| Action | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:---:|:---:|:---:|
| List / View / PDF / Audit log | ✅ | ✅ | ✅ |
| Create PL+CI (from Approved PI) | ✅ | ❌ | ✅ |
| Edit header / containers / items (Draft or Rework) | ✅ | ❌ | ✅ |
| Delete PL+CI (Draft only) | ✅ | ❌ | ✅ |
| Submit for approval | ✅ | ❌ | ✅ |
| Approve (Pending Approval) | ✅ | ✅ | ❌ |
| Send for Rework — comment required | ✅ | ✅ | ❌ |
| Permanently Reject — comment required | ✅ | ✅ | ❌ |

### Purchase Order

Same pattern as PI: MAKER creates/edits/submits, CHECKER/ADMIN approves.

### Master Data

- **Reads:** any authenticated user (`IsAnyRole`)
- **Writes (create/edit/deactivate):** CHECKER + COMPANY_ADMIN only (`IsCheckerOrAdmin`)

### User Management (`/api/v1/users/`)

Guarded by `IsCompanyAdmin`.

| Action | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:---:|:---:|:---:|
| View user list | ✅ | ❌ | ❌ |
| Invite MAKER or CHECKER | ✅ | ❌ | ❌ |
| Invite COMPANY_ADMIN | ❌ | ❌ | ❌ |
| Edit role / deactivate users | ✅ | ❌ | ❌ |
| Reset another user's password | ✅ | ❌ | ❌ |

> COMPANY_ADMIN **cannot** invite another COMPANY_ADMIN — enforced on backend (`UserCreateSerializer`) and frontend (invite modal role dropdown).

### Navigation Visibility

| Page | COMPANY_ADMIN | CHECKER | MAKER |
|------|:---:|:---:|:---:|
| Dashboard, PI, PL+CI, PO, COA | ✅ | ✅ | ✅ |
| Master Data (Orgs, Banks, T&C, Ref Data) | ✅ | ✅ | ❌ |
| User Management | ✅ | ❌ | ❌ |
| Reports | ✅ | ✅ | ❌ |
| Training | ✅ | ✅ | ✅ |

### Workflow Constraints (All Document Types)

| Constraint | Detail |
|---|---|
| REWORK and PERMANENTLY_REJECT | Comment is mandatory. Backend blocks if empty. |
| Edit window | Documents editable only in DRAFT or REWORK state. |
| Self-approve | MAKER and CHECKER cannot approve their own documents. COMPANY_ADMIN can. |
| Permanently Rejected | Terminal state — no further transitions. |

---

## Key Architectural Decisions

### Document Number Generation
Generated inside `select_for_update()` in `apps/{app}/services.py → generate_document_number()`.
Format: `PI-YYYY-NNNN`, `PL-YYYY-NNNN`, `CI-YYYY-NNNN`, `COA-YYYY-NNNN` (4-digit zero-padded).

### Workflow Service
ALL status transitions go through `apps/workflow/services.py → WorkflowService`. Never update `status` in serializers, signals, or management commands. Every transition writes an `AuditLog` in the same `transaction.atomic()`.

### PDF Generation
Always in-memory. Never written to disk. Use `FileResponse` or `StreamingHttpResponse` with `content_type='application/pdf'`.
PDF watermark rule: DRAFT watermark on all states except APPROVED.

### COA Spec Fields (as of 2026-06-20)
`COAParameter.spec_min`, `spec_max`, `result_value` are `CharField(max_length=50)` — **not** `DecimalField`. Reason: analysts enter values like `"< 5.0"`, `"> 99"`, `"NMT 5 ppm"`. Migration `0005_coaparameter_text_spec_fields` covers this.

### Currency
PI has a `currency` FK to `master_data.Currency`. Currency is mandatory on create, cannot be changed once line items exist. CI inherits currency from linked PI via `packing_list.proforma_invoice`. Fields are named `rate` and `amount` (not `rate_usd`/`amount_usd`).

### Container Gross Weight
`gross_weight` on `Container` is always stored (never computed on-the-fly). Recomputed and saved whenever `net_weight` or `tare_weight` changes via `Container.save()` override.

---

## Known Gotchas (factory-boy / testing)

- Custom User model uses `.full_name` NOT `.get_full_name()` — fix serializers accordingly.
- `AuditLog` uses `performed_at` field NOT `created_at`.
- `CountryFactory` iso2/iso3 sequences: use `chr(65 + (n//26)%26) + chr(65 + n%26)` — never use string slicing `[:2]` (collisions when n≥10).
- factory-boy `@factory.post_generation` with explicit `self.save()` needed for password setting.
- COA uses `PI_TRANSITIONS` (same workflow state machine as PI) — registered in WorkflowService.
- `OrganisationAddress` has IEC + tax fields inlined (not a separate `OrganisationTaxCode` model).
- `container_ref` is optional — `required=False, allow_blank=True` in `ContainerSerializer`.

---

## Completed Feature History

| Feature | Commit / Date | Notes |
|---|---|---|
| Multi-currency support | 2026-04-17 | PI gets currency FK; fields renamed from `rate_usd` → `rate`; 3-step migration |
| COA feature (FR-COA-01–13) | 2026-06 | 6 stages: master data, model, API, PDF, frontend, tests (56 tests) |
| COA spec fields → CharField | 2026-06-20 | Migration 0005; allows `"< 5.0"` style values |
| PDF layout fixes | 2026-06-20 | `splitByRow=False` on all tables; `KeepTogether` on PI header |
