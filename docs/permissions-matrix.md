# TradeDocs Permissions Matrix

Generated from source code audit on 2026-03-23. Updated 2026-03-23.

**Roles in hierarchy order:** SUPER_ADMIN > COMPANY_ADMIN > CHECKER > MAKER

---

## Document Workflow Actions

Transition rules are defined in `apps/workflow/constants.py` and enforced by `WorkflowService`.
The frontend mirrors these in `frontend/src/components/common/WorkflowActionButton.tsx`.

### Proforma Invoice (PI)

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all PIs | ✅ | ✅ | ✅ | ✅ |
| Download PI PDF | ✅ | ✅ | ✅ | ✅ |
| View PI audit log | ✅ | ✅ | ✅ | ✅ |
| Create PI | ✅ | ✅ | ❌ | ✅ |
| Edit PI header (Draft or Rework) — own PI | ✅ | ✅ | ❌ | ✅ |
| Edit PI header (Draft or Rework) — others' PI | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete line items & charges (Draft/Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete line items & charges (Draft/Rework) — others' | ✅ | ✅ | ❌ | ✅ |
| Submit PI for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PI (Pending Approval) | ✅ | ✅ | ✅ | ❌ |
| Send PI for Rework (Pending Approval) — comment required | ✅ | ✅ | ✅ | ❌ |
| Permanently Reject PI — comment required | ✅ | ✅ | ✅ | ❌ |
| Upload signed copy (Approved only) | ✅ | ✅ | ✅ | ✅ |
| Hard-delete PI from database | ✅ | ❌ | ❌ | ❌ |

---

### Packing List + Commercial Invoice (PL+CI)

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all PL+CIs | ✅ | ✅ | ✅ | ✅ |
| Download PL+CI PDF | ✅ | ✅ | ✅ | ✅ |
| View PL+CI audit log | ✅ | ✅ | ✅ | ✅ |
| Create PL+CI (selects an Approved PI) | ✅ | ✅ | ❌ | ✅ |
| Edit PL+CI header (Draft or Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Edit PL+CI header (Draft or Rework) — others' | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete containers & items (Draft/Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete containers & items (Draft/Rework) — others' | ✅ | ✅ | ❌ | ✅ |
| Delete PL+CI (Draft state only) — own | ✅ | ✅ | ❌ | ✅ |
| Delete PL+CI (Draft state only) — others' | ✅ | ✅ | ❌ | ✅ |
| Submit PL+CI for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PL+CI (Pending Approval) | ✅ | ✅ | ✅ | ❌ |
| Send PL+CI for Rework — comment required | ✅ | ✅ | ✅ | ❌ |
| Permanently Reject PL+CI — comment required | ✅ | ✅ | ✅ | ❌ |
| Upload signed copy (Approved only) | ✅ | ✅ | ✅ | ✅ |
| Hard-delete PL+CI from database | ✅ | ❌ | ❌ | ❌ |

---

### Purchase Order (PO)

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| List / View all POs | ✅ | ✅ | ✅ | ✅ |
| Download PO PDF | ✅ | ✅ | ✅ | ✅ |
| View PO audit log | ✅ | ✅ | ✅ | ✅ |
| Create PO | ✅ | ✅ | ❌ | ✅ |
| Edit PO header (Draft or Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Edit PO header (Draft or Rework) — others' | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete line items (Draft/Rework) — own | ✅ | ✅ | ❌ | ✅ |
| Add / Edit / Delete line items (Draft/Rework) — others' | ✅ | ✅ | ❌ | ✅ |
| Submit PO for approval (Draft/Rework) | ✅ | ✅ | ❌ | ✅ |
| Approve PO (Pending Approval) | ✅ | ✅ | ✅ | ❌ |
| Send PO for Rework — comment required | ✅ | ✅ | ✅ | ❌ |
| Permanently Reject PO — comment required | ✅ | ✅ | ✅ | ❌ |
| Hard-delete PO from database | ✅ | ❌ | ❌ | ❌ |

---

## Workflow Constraints (All Document Types)

| Constraint | Detail |
|-----------|--------|
| REWORK and PERMANENTLY_REJECT | Comment is mandatory. Backend blocks if empty. |
| Edit window | Documents editable only in DRAFT or REWORK state. |
| Self-approve | MAKER and CHECKER cannot approve their own documents. COMPANY_ADMIN and SUPER_ADMIN can. |
| Permanently Rejected | Terminal state — no further transitions. |

---

## Master Data

Backend: writes require `IsCheckerOrAdmin` (CHECKER + COMPANY_ADMIN + SUPER_ADMIN). Reads require any authenticated user (`IsAnyRole`).

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| View Organisations | ✅ | ✅ | ✅ | ✅ |
| Create / Edit / Deactivate Organisations | ✅ | ✅ | ✅ | ❌ |
| View Banks | ✅ | ✅ | ✅ | ✅ |
| Create / Edit / Deactivate Banks | ✅ | ✅ | ✅ | ❌ |
| View T&C Templates | ✅ | ✅ | ✅ | ✅ |
| Create / Edit / Deactivate T&C Templates | ✅ | ✅ | ✅ | ❌ |
| View Reference Data | ✅ | ✅ | ✅ | ✅ |
| Create / Edit / Deactivate Reference Data | ✅ | ✅ | ✅ | ❌ |

---

## User Management

The `/api/v1/users/` endpoint is guarded by `IsCompanyAdmin` (COMPANY_ADMIN + SUPER_ADMIN).

| Action | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|--------|:-----------:|:-------------:|:-------:|:-----:|
| View user list | ✅ | ✅ | ❌ | ❌ |
| Invite MAKER user | ✅ | ✅ | ❌ | ❌ |
| Invite CHECKER user | ✅ | ✅ | ❌ | ❌ |
| Invite COMPANY_ADMIN user | ✅ | ❌ | ❌ | ❌ |
| Edit another user's role | ✅ | ✅ | ❌ | ❌ |
| Deactivate / reactivate another user | ✅ | ✅ | ❌ | ❌ |
| Reset another user's password | ✅ | ✅ | ❌ | ❌ |
| Edit own role | ❌ | ❌ | ❌ | ❌ |
| Deactivate own account | ❌ | ❌ | ❌ | ❌ |
| Deactivate last active COMPANY_ADMIN | ❌ | ❌ | ❌ | ❌ |

> COMPANY_ADMIN cannot invite another COMPANY_ADMIN — enforced on both backend (`UserCreateSerializer`) and frontend (invite modal role dropdown).

---

## Navigation / Pages

Controlled by the `roles` array in `NAV_ITEMS` in `frontend/src/components/AppLayout.tsx`.

| Page | SUPER_ADMIN | COMPANY_ADMIN | CHECKER | MAKER |
|------|:-----------:|:-------------:|:-------:|:-----:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Proforma Invoice | ✅ | ✅ | ✅ | ✅ |
| Packing List & Commercial Invoice | ✅ | ✅ | ✅ | ✅ |
| Purchase Orders | ✅ | ✅ | ✅ | ✅ |
| Master Data (dropdown) | ✅ | ✅ | ✅ | ❌ |
| → Organisations | ✅ | ✅ | ✅ | ❌ |
| → Banks | ✅ | ✅ | ✅ | ❌ |
| → T&C Templates | ✅ | ✅ | ✅ | ❌ |
| → Reference Data | ✅ | ✅ | ✅ | ❌ |
| User Management | ✅ | ✅ | ❌ | ❌ |
| Reports | ✅ | ✅ | ✅ | ❌ |
| Training | ✅ | ✅ | ✅ | ✅ |
