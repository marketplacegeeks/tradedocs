# TradeDocs Permissions Matrix

Generated from source code audit on 2026-03-23.

**Roles in hierarchy order:** SUPER_ADMIN > COMPANY_ADMIN > CHECKER > MAKER

---

## Document Workflow Actions

All four document types (PI, PL+CI, PO) share the same transition table logic. The
allowed-roles sets are defined in `apps/workflow/constants.py` and enforced by
`WorkflowService`. The frontend mirrors these checks in
`frontend/src/components/common/WorkflowActionButton.tsx`.

> Note: The frontend `isCheckerOrAdmin` variable is misleadingly named — it actually
> includes MAKER, CHECKER, COMPANY_ADMIN, and SUPER_ADMIN. This means the frontend
> shows Approve / Permanently Reject buttons to Makers, but the backend
> `APPROVE_ROLES` constant also includes MAKER, so both layers are consistent.

### Proforma Invoice (PI)

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all PIs | ✅ | ✅ | ✅ | ✅ |
| Download PI PDF | ✅ | ✅ | ✅ | ✅ |
| View PI audit log | ✅ | ✅ | ✅ | ✅ |
| Create PI | ✅ | ✅ | ❌ | ✅ |
| Edit PI header (Draft or Rework) — own PI | ✅ | ✅ | ❌ | ✅ |
| Edit PI header (Draft or Rework) — others' PI | ✅ | ✅ | ❌ | ❌ |
| Add / Edit / Delete line items & charges (Draft/Rework) — own PI | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete line items & charges (Draft/Rework) — others' PI | ✅ | ✅ | ❌ | ❌ |
| Submit PI for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PI (Pending Approval) | ✅ | ✅ | ✅ | ✅ |
| Send PI for Rework (Pending Approval) — comment required | ✅ | ✅ | ✅ | ✅ |
| Permanently Reject PI (any non-terminal state) — comment required | ✅ | ✅ | ✅ | ✅ |
| Upload signed copy (Approved only) | ✅ | ✅ | ✅ | ✅ |
| Hard-delete PI from database | ✅ | ❌ | ❌ | ❌ |

**Source:** `apps/proforma_invoice/views.py` (`perform_create`, `perform_update`, `_check_editable`); `apps/workflow/constants.py` (`PI_TRANSITIONS`, `SUBMIT_ROLES`, `APPROVE_ROLES`).

---

### Packing List + Commercial Invoice (PL+CI — created jointly)

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all PL+CIs | ✅ | ✅ | ✅ | ✅ |
| Download PL+CI PDF | ✅ | ✅ | ✅ | ✅ |
| View PL+CI audit log | ✅ | ✅ | ✅ | ✅ |
| Create PL+CI (selects an Approved PI) | ✅ | ✅ | ❌ | ✅ |
| Edit PL+CI header (Draft or Rework) — own document | ✅ | ✅ | ❌ | ✅ |
| Edit PL+CI header (Draft or Rework) — others' document | ✅ | ✅ | ❌ | ❌ |
| Add / Edit / Delete containers & items (Draft/Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete containers & items (Draft/Rework) — others' | ✅ | ✅ | ❌ | ❌ |
| Copy container | ✅ | ✅ | ❌ | ✅ (own PL only) |
| Delete PL+CI (Draft state only) — own | ✅ | ✅ | ❌ | ✅ |
| Delete PL+CI (Draft state only) — others' | ✅ | ✅ | ❌ | ❌ |
| Submit PL+CI for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PL+CI (Pending Approval) | ✅ | ✅ | ✅ | ✅ |
| Send PL+CI for Rework (Pending Approval) — comment required | ✅ | ✅ | ✅ | ✅ |
| Permanently Reject PL+CI (any non-terminal state) — comment required | ✅ | ✅ | ✅ | ✅ |
| Upload signed copy (Approved only) | ✅ | ✅ | ✅ | ✅ |
| Hard-delete PL+CI from database | ✅ | ❌ | ❌ | ❌ |

**Source:** `apps/packing_list/views.py` (`perform_create`, `perform_update`, `perform_destroy`, `_check_pl_editable`); `apps/workflow/constants.py` (`PLCI_TRANSITIONS`).

---

### Purchase Order (PO)

> Note: PO creation is open to **all authenticated users** (any role). This differs from PI
> and PL+CI where CHECKER is blocked from creating. Source: `perform_create` in
> `apps/purchase_order/views.py` has no role check — it calls `serializer.save()` directly.
> The frontend list page also renders the "New Purchase Order" button without a `canCreate`
> role guard (unlike PI and PL+CI pages).

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all POs | ✅ | ✅ | ✅ | ⚠️ own only (frontend filter) |
| Download PO PDF | ✅ | ✅ | ✅ | ✅ |
| View PO audit log | ✅ | ✅ | ✅ | ✅ |
| Create PO | ✅ | ✅ | ✅ | ✅ |
| Edit PO header (Draft or Rework) — own PO | ✅ | ✅ | ✅ | ✅ |
| Edit PO header (Draft or Rework) — others' PO | ✅ | ✅ | ❌ | ❌ |
| Add / Edit / Delete line items (Draft/Rework) — own | ✅ | ✅ | ✅ | ✅ |
| Add / Edit / Delete line items (Draft/Rework) — others' | ✅ | ✅ | ❌ | ❌ |
| Submit PO for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PO (Pending Approval) | ✅ | ✅ | ✅ | ✅ |
| Send PO for Rework (Pending Approval) — comment required | ✅ | ✅ | ✅ | ✅ |
| Permanently Reject PO (any non-terminal state) — comment required | ✅ | ✅ | ✅ | ✅ |
| Hard-delete PO from database | ✅ | ❌ | ❌ | ❌ |

**Source:** `apps/purchase_order/views.py`; `apps/workflow/constants.py` (`PO_TRANSITIONS`); `frontend/src/pages/purchase-order/PurchaseOrderListPage.tsx`.

---

## Workflow Constraints (All Document Types)

| Constraint | Detail |
|-----------|--------|
| REWORK and PERMANENTLY_REJECT actions | Comment field is mandatory (non-empty). Backend enforces via `COMMENT_REQUIRED_ACTIONS` in `constants.py`. |
| Edit window | Documents can only be edited when status is DRAFT or REWORK (`EDITABLE_STATES`). |
| Submit requirement | At least one line item must exist before submission (PI and PO enforce this; PL+CI does not check explicitly). |
| Permanently Rejected | Terminal state — no further transitions allowed. |

---

## Master Data

Backend permission class for writes: `IsCheckerOrAdmin` (CHECKER + COMPANY_ADMIN + SUPER_ADMIN).
Backend permission class for reads: `IsAnyRole` (all authenticated users).

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| **Organisations** | | | | |
| View / list | ✅ | ✅ | ✅ | ✅ |
| Create new organisation | ✅ | ✅ | ✅ | ❌ |
| Edit organisation | ✅ | ✅ | ✅ | ❌ |
| Deactivate organisation (soft-delete) | ✅ | ✅ | ✅ | ❌ |
| **Banks** | | | | |
| View / list | ✅ | ✅ | ✅ | ✅ |
| Create bank account | ✅ | ✅ | ✅ | ❌ |
| Edit bank account | ✅ | ✅ | ✅ | ❌ |
| Deactivate bank account (soft-delete) | ✅ | ✅ | ✅ | ❌ |
| **T&C Templates** | | | | |
| View / list | ✅ | ✅ | ✅ | ✅ |
| Create T&C template | ✅ | ✅ | ✅ | ❌ |
| Edit T&C template | ✅ | ✅ | ✅ | ❌ |
| Deactivate T&C template (soft-delete) | ✅ | ✅ | ✅ | ❌ |
| **Reference Data** (Countries, Incoterms, UOM, Payment Terms, Ports, Locations, Pre-Carriage By, Currencies) | | | | |
| View / list all reference data | ✅ | ✅ | ✅ | ✅ |
| Create reference data records | ✅ | ✅ | ✅ | ❌ |
| Edit reference data records | ✅ | ✅ | ✅ | ❌ |
| Deactivate reference data records (soft-delete) | ✅ | ✅ | ✅ | ❌ |

**Source:** `apps/accounts/permissions.py`; `frontend/src/pages/master-data/OrganisationListPage.tsx`, `BankListPage.tsx`, `TCTemplateListPage.tsx`, `ReferenceDataPage.tsx` — all use `canWrite = role === CHECKER || COMPANY_ADMIN || SUPER_ADMIN`.

---

## User Management

The `/api/v1/users/` endpoint is guarded by `IsCompanyAdmin` (COMPANY_ADMIN + SUPER_ADMIN).
The frontend page at `/users` is only shown in the nav for COMPANY_ADMIN and SUPER_ADMIN.

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| View user list | ✅ | ✅ | ❌ | ❌ |
| Invite (create) a MAKER user | ✅ | ✅ | ❌ | ❌ |
| Invite (create) a CHECKER user | ✅ | ✅ | ❌ | ❌ |
| Invite (create) a COMPANY_ADMIN user | ✅ | ❌ | ❌ | ❌ |
| Edit another user's role (MAKER ↔ CHECKER only) | ✅ | ✅ | ❌ | ❌ |
| Deactivate / reactivate another user | ✅ | ✅ | ❌ | ❌ |
| Edit own role | ❌ | ❌ | ❌ | ❌ |
| Deactivate own account | ❌ | ❌ | ❌ | ❌ |
| Deactivate / demote last active COMPANY_ADMIN | ❌ | ❌ | ❌ | ❌ |

**Notes:**
- Only SUPER_ADMIN can invite COMPANY_ADMIN users. This is enforced in the frontend invite modal (role dropdown conditionally includes COMPANY_ADMIN only when `currentUser.role === SUPER_ADMIN`). The backend does not enforce this separately — it relies on the `IsCompanyAdmin` gate and the frontend UI restriction.
- SUPER_ADMIN and COMPANY_ADMIN cannot change their own role. This is enforced by `UserUpdateSerializer` Guard 1.
- The last active COMPANY_ADMIN cannot be deactivated or demoted. Enforced by `UserUpdateSerializer` Guard 2.

**Source:** `apps/accounts/views.py` (`UserListCreateView`, `UserDetailView`); `apps/accounts/serializers.py` (`UserUpdateSerializer`); `frontend/src/pages/users/UserListPage.tsx`.

---

## Navigation / Pages

Controlled by the `roles` array in `NAV_ITEMS` in `frontend/src/components/AppLayout.tsx`.

| Page / Section | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|----------------|:-----------:|:-------------:|:-------:|:-----:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Proforma Invoice (list + detail) | ✅ | ✅ | ✅ | ✅ |
| Packing List & Commercial Invoice | ✅ | ✅ | ✅ | ✅ |
| Purchase Orders | ✅ | ✅ | ✅ | ✅ |
| Master Data (dropdown group) | ✅ | ✅ | ✅ | ❌ |
| → Organisations | ✅ | ✅ | ✅ | ❌ |
| → Banks | ✅ | ✅ | ✅ | ❌ |
| → T&C Templates | ✅ | ✅ | ✅ | ❌ |
| → Reference Data | ✅ | ✅ | ✅ | ❌ |
| User Management | ✅ | ✅ | ❌ | ❌ |
| Reports | ✅ | ✅ | ✅ | ❌ |
| Training | ✅ | ✅ | ✅ | ✅ |

> Note: "Master Data" routes are accessible to MAKER via direct URL (the backend APIs
> allow read access to all authenticated users), but the sidebar link is hidden.

---

## Notable Anomalies / Items to Review

1. **PO creation is open to CHECKER** — Unlike PI and PL+CI where `perform_create` explicitly blocks CHECKERs, the PO `perform_create` has no role guard. A CHECKER can therefore create a Purchase Order via the API (and the frontend shows the "New Purchase Order" button to all roles with no `canCreate` guard). This may be intentional or an oversight.

2. **MAKER can Approve documents** — `APPROVE_ROLES` in `constants.py` includes MAKER. The frontend `WorkflowActionButton` mirrors this. This means a Maker who did not create a document could approve it. Typical maker-checker separation would restrict approve to CHECKER+ADMIN only.

3. **MAKER can Permanently Reject** — Same as above. `APPROVE_ROLES` (which governs Permanently Reject) includes MAKER.

4. **SUPER_ADMIN invite restriction is frontend-only** — The backend `IsCompanyAdmin` permission allows any COMPANY_ADMIN or SUPER_ADMIN to POST to `/api/v1/users/` with any role value. Only the frontend hides the COMPANY_ADMIN role option for non-SUPER_ADMIN users. A COMPANY_ADMIN could call the API directly to create another COMPANY_ADMIN.

5. **PO Maker visibility is frontend-only** — Makers see only their own POs because the frontend passes `created_by=user.id` as a query filter. The backend does not enforce this restriction — a MAKER can query all POs by calling the API without that filter.
