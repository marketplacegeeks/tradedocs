# Product Requirements Document — Purchase Order

**Version:** 1.4
**Status:** Active
**Last Updated:** 2026-03-22

---

## 1. Overview

A **Purchase Order (PO)** is an internal procurement document issued by the trading house to a vendor, authorising the purchase of goods at agreed terms. Unlike the Proforma Invoice, Packing List, and Commercial Invoice (which are outward-facing trade documents), the Purchase Order is an inward-facing document the company creates for its own supply chain.

The Purchase Order follows the same maker–checker approval workflow as all other documents in TradeDocs. All workflow rules from **FR-08** apply without modification.

---

## 2. Development Sequence

| Stage | What gets built |
| --- | --- |
| **Stage 1** | Currency master — add `is_active` + Reference Data page tab |
| **Stage 2** | Organisation master changes — Vendor tag + Delivery address type |
| **Stage 3** | User model — add phone number fields |
| **Stage 4** | Backend Django app — PO model, number generation, API, workflow |
| **Stage 5** | Frontend navigation and list page |
| **Stage 6** | Frontend create / edit form |
| **Stage 7** | Frontend detail / review page and PDF endpoint |

---

## Stage 1 — Currency Master

### FR-PO-01 — Make Currency Manageable in Reference Data

Currency already exists in the system (used by the Bank master) but currently has no `is_active` field and cannot be managed from the Reference Data page. The Purchase Order requires a currency selection, so currencies must be creatable and manageable by admins.

**Backend changes (****`apps/master_data/`****):**
- Add `is_active = BooleanField(default=True)` to the `Currency` model.
- Add a migration.
- Update `CurrencyViewSet` to use the same `ReferenceDataViewSet` base class as other reference entities. Remove the existing `get_queryset()` override that bypassed `is_active`.

**Frontend changes:**
- Add a **"Currency"** tab to `ReferenceDataPage.tsx` alongside existing tabs.
- Fields: Currency Name, Currency Code (e.g. USD, EUR, AED). Same add/edit/deactivate pattern as other tabs.
- Add `"CURRENCY"` to `src/utils/constants.ts` if not already present.

**Seed data:** Ensure at minimum USD, EUR, GBP, AED, INR are present as active currencies.

### Wireframe — Reference Data Page (Currency tab added)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Reference Data                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ [Countries] [Ports] [Locations] [Incoterms] [UOM] [Payment Terms]  │
│ [Pre-Carriage] [Currency]  ← new tab                               │
├─────────────────────────────────────────────────────────────────────┤
│ Currency                                       [+ Add Currency]    │
│                                                                     │
│  Name             Code     Status    Actions                        │
│  ─────────────────────────────────────────────────────────────      │
│  US Dollar        USD      Active    [Edit] [Deactivate]            │
│  Euro             EUR      Active    [Edit] [Deactivate]            │
│  UAE Dirham       AED      Active    [Edit] [Deactivate]            │
│  Pound Sterling   GBP      Active    [Edit] [Deactivate]            │
│  Indian Rupee     INR      Active    [Edit] [Deactivate]            │
└─────────────────────────────────────────────────────────────────────┘

  Add / Edit Currency modal:
  ┌──────────────────────────────┐
  │ Add Currency                 │
  │                              │
  │ Currency Name *              │
  │ ┌──────────────────────────┐ │
  │ │ e.g. US Dollar           │ │
  │ └──────────────────────────┘ │
  │                              │
  │ Currency Code *              │
  │ ┌──────────────────────────┐ │
  │ │ e.g. USD                 │ │
  │ └──────────────────────────┘ │
  │                              │
  │         [Cancel] [Save]      │
  └──────────────────────────────┘
```

---

## Stage 2 — Organisation Master Changes

### FR-PO-02 — New Organisation Tag: Vendor

Add a **Vendor** tag to the Organisation tagging system.

| Tag | Dropdown it populates |
| --- | --- |
| Vendor | Vendor field on the Purchase Order creation form |

**Rules:**
- An organisation may hold Vendor alongside any other tag. Tags are not mutually exclusive.
- No existing tag is renamed or removed.

**Backend change:**
- Add `VENDOR` to the `OrganisationTag.tag` choice list in `apps/master_data/models.py`.
- Add a migration.

**Frontend change:**
- Add `VENDOR: "VENDOR"` to organisation tag constants in `src/utils/constants.ts`.
- Add "Vendor" as a selectable option in `OrganisationFormPage.tsx`.

---

### FR-PO-03 — New Organisation Address Type: Delivery

Add a **Delivery** address type alongside Registered, Factory, and Office.

**Rules:**
- An organisation may have multiple Delivery addresses.
- Existing address types are unaffected.

**Backend change:**
- Add `DELIVERY` to the `OrganisationAddress.address_type` choice list in `apps/master_data/models.py`.
- Add a migration.

**Frontend change:**
- Add "Delivery" to the Address Type dropdown in `OrganisationFormPage.tsx`.
- Add `DELIVERY: "DELIVERY"` to address type constants in `src/utils/constants.ts`.

### Wireframe — Organisation Form (showing the two additions only)

```
  Document Role Tags (multi-select) *
  ┌─────────────────────────────────────────────────┐
  │ [x] Exporter   [x] Consignee   [ ] Buyer        │
  │ [ ] Notify Party   [x] Vendor  ← new option     │
  └─────────────────────────────────────────────────┘

  Address Type *
  ┌──────────────────────┐
  │ Registered         ▼ │   ← existing options unchanged
  │ ─────────────────    │
  │ Registered           │
  │ Factory              │
  │ Office               │
  │ Delivery           ← new option
  └──────────────────────┘
```

### 
---

## Stage 3 — User Model: Phone Number

### FR-PO-04 — Add Phone Number to User

The Purchase Order displays the internal contact's phone number. This requires phone number fields on the User model.

**Backend changes (****`apps/accounts/models.py`****):**

| Field | Type | Notes |
| --- | --- | --- |
| `phone_country_code` | `CharField(max_length=10, blank=True)` | E.164 dial code, e.g. `+91`, `+1` |
| `phone_number` | `CharField(max_length=20, blank=True)` | Local number without country code |

- Both fields are optional. If only one is provided, raise a validation error.
- Phone validation uses the `phonenumbers` library (already installed).
- Add a migration.

**API changes:**
- `UserUpdateSerializer`: accept both phone fields as optional writable fields.
- `GET /api/v1/auth/me/`: include both phone fields in the response.
- `GET /api/v1/users/` and `GET /api/v1/users/{id}/`: include both phone fields.

**Frontend changes (****`UserListPage.tsx`****):**
- Add phone fields to the Edit User modal. Same two-field pattern (country code dropdown + number input) as Organisation address phone.

### Wireframe — Edit User Modal (phone fields added)

```
  ┌──────────────────────────────────────────────┐
  │ Edit User                                    │
  │                                              │
  │ Full Name *                                  │
  │ ┌────────────────────────────────────────┐   │
  │ │ Aniket Shah                            │   │
  │ └────────────────────────────────────────┘   │
  │                                              │
  │ Role *                                       │
  │ ┌────────────────────────────────────────┐   │
  │ │ Maker                               ▼  │   │
  │ └────────────────────────────────────────┘   │
  │                                              │
  │ Status *                                     │
  │ ┌────────────────────────────────────────┐   │
  │ │ Active                              ▼  │   │
  │ └────────────────────────────────────────┘   │
  │                                              │
  │ Phone Number (optional)                      │
  │ ┌──────────┐  ┌─────────────────────────┐   │
  │ │ +91    ▼ │  │ 98765 43210             │   │
  │ └──────────┘  └─────────────────────────┘   │
  │  country code    local number               │
  │                                              │
  │                      [Cancel]  [Save]        │
  └──────────────────────────────────────────────┘
```

---

## Stage 4 — Backend: Purchase Order Django App

### FR-PO-05 — New Django App

Create `apps/purchase_order/` with the standard structure:

```
apps/purchase_order/
  __init__.py
  models.py
  serializers.py
  views.py
  urls.py
  services.py       ← generate_document_number() lives here
  admin.py
  apps.py
  tests/
    __init__.py
    factories.py
    test_models.py
    test_views.py
```

Register the app in `INSTALLED_APPS` in `tradetocs/settings.py`.

---

### FR-PO-06 — Data Models

#### PurchaseOrder (header)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `po_number` | `CharField(unique=True)` | Auto | Auto-generated on creation. Format: `PO-YYYY-NNNN`. Uses `select_for_update()` lock. |
| `po_date` | `DateField` | Yes | Defaults to today; editable by Maker |
| `customer_no` | `CharField(blank=True)` | No | Reference number this vendor uses for the buyer |
| `vendor` | `ForeignKey(Organisation, on_delete=PROTECT)` | Yes | Must be tagged `VENDOR` |
| `internal_contact` | `ForeignKey(User, on_delete=PROTECT)` | Yes | Any active user; internal point of contact for this PO |
| `delivery_address` | `ForeignKey(OrganisationAddress, on_delete=PROTECT)` | Yes | Must belong to `vendor` with `address_type=DELIVERY` |
| `bank` | `ForeignKey(Bank, on_delete=PROTECT, null=True, blank=True)` | No | Issuing company's bank; prints on the document |
| `currency` | `ForeignKey(Currency, on_delete=PROTECT)` | Yes | Currency for all monetary fields on this PO |
| `payment_terms` | `ForeignKey(PaymentTerm, on_delete=PROTECT, null=True, blank=True)` | No | From PaymentTerm master |
| `country_of_origin` | `ForeignKey(Country, on_delete=PROTECT, null=True, blank=True)` | No | Country where goods are produced |
| `transaction_type` | `CharField` | Yes | Controls which tax columns appear on line items. Choices: `IGST` (Inter State), `CGST_SGST` (Same State), `ZERO_RATED` (Export). |
| `time_of_delivery` | `CharField(blank=True)` | No | Free text, e.g. "prompt / August 2025" |
| `tc_template` | `ForeignKey(TCTemplate, on_delete=PROTECT, null=True, blank=True)` | No | Selected from T&C Templates master |
| `tc_content` | `TextField(blank=True)` | No | Snapshot of T&C body at time of selection |
| `remarks` | `TextField(blank=True)` | No | Free text; no character limit |
| `status` | `CharField` | Auto | Managed by `WorkflowService` only. Values: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REWORK`, `PERMANENTLY_REJECTED` |
| `created_by` | `ForeignKey(User, on_delete=PROTECT, related_name='purchase_orders_created')` | Auto | Set on creation; never editable |
| `created_at` | `DateTimeField(auto_now_add=True)` | Auto | — |
| `updated_at` | `DateTimeField(auto_now=True)` | Auto | — |

**Indexes:** `status`, `created_by`, `vendor`.

Monetary totals are **not stored on the header** — computed from line items on read.

---

#### PurchaseOrderLineItem

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `purchase_order` | `ForeignKey(PurchaseOrder, on_delete=CASCADE, related_name='line_items')` | Yes | Parent document |
| `description` | `TextField` | Yes | Product / goods description |
| `item_code` | `CharField(blank=True)` | No | Internal item code, e.g. `3004` |
| `hsn_code` | `CharField(blank=True)` | No | HSN classification code, e.g. `2815.11.00` |
| `manufacturer` | `CharField(blank=True)` | No | Name of the manufacturer |
| `uom` | `ForeignKey(UOM, on_delete=PROTECT)` | Yes | Unit of measurement; drives dynamic column header label |
| `quantity` | `DecimalField(max_digits=15, decimal_places=6)` | Yes | Numeric quantity in the selected UOM. Stores exactly what the user types (up to 6dp). Maps to the "Unit (mt)" column in the PDF. |
| `packaging_description` | `TextField(blank=True)` | No | Free text packing detail, e.g. "4,320 25kg bags without pallets". Maps to the "Quantity" column in the PDF. |
| `unit_price` | `DecimalField(max_digits=15, decimal_places=2)` | Yes | Price per UOM in the PO currency |
| `taxable_amount` | `DecimalField(max_digits=15, decimal_places=2)` | Auto | Computed on save: `quantity × unit_price`. Stored. |
| `igst_percent` | `DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)` | Conditional | Required when header `transaction_type = IGST`; null otherwise |
| `igst_amount` | `DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)` | Auto | Computed on save: `taxable_amount × (igst_percent / 100)`. Null when not IGST. |
| `cgst_percent` | `DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)` | Conditional | Required when header `transaction_type = CGST_SGST`; null otherwise |
| `cgst_amount` | `DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)` | Auto | Computed on save: `taxable_amount × (cgst_percent / 100)`. Null when not CGST_SGST. |
| `sgst_percent` | `DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)` | Conditional | Required when header `transaction_type = CGST_SGST`; null otherwise. Must equal `cgst_percent`. |
| `sgst_amount` | `DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)` | Auto | Computed on save: `taxable_amount × (sgst_percent / 100)`. Null when not CGST_SGST. |
| `total_tax` | `DecimalField(max_digits=15, decimal_places=2)` | Auto | Computed on save: `igst_amount` OR `cgst_amount + sgst_amount` OR `0` for ZERO_RATED. Stored. |
| `total` | `DecimalField(max_digits=15, decimal_places=2)` | Auto | Computed on save: `taxable_amount + total_tax`. Stored. |
| `sort_order` | `PositiveIntegerField(default=0)` | No | Display order; auto-incremented on add |

**`PurchaseOrderLineItem.save()`**** compute logic by transaction type:**
- `IGST` → compute `igst_amount`; set `cgst_percent`, `cgst_amount`, `sgst_percent`, `sgst_amount` to null; `total_tax = igst_amount`
- `CGST_SGST` → compute `cgst_amount`, `sgst_amount`; set `igst_percent`, `igst_amount` to null; `total_tax = cgst_amount + sgst_amount`
- `ZERO_RATED` → set all tax fields to null; `total_tax = 0`
- Always: `taxable_amount = quantity × unit_price`; `total = taxable_amount + total_tax`

---

### FR-PO-07 — Document Number Generation

In `apps/purchase_order/services.py`, implement `generate_document_number()`:

- Acquire a `select_for_update()` lock on `PurchaseOrder`.
- Count existing records in the current calendar year.
- Generate: `PO-{YYYY}-{NNNN}` (e.g. `PO-2026-0001`).
- Called inside `PurchaseOrderViewSet.perform_create()` before saving.

---

### FR-PO-08 — Workflow Registration

Register `PurchaseOrder` in `WorkflowService` (`apps/workflow/services.py`):

- `document_type` string for `AuditLog`: `"purchase_order"`.
- No cascading rules — PO is not linked upstream to PI/PL/CI.

| From | Action | To | Who | Comment required |
| --- | --- | --- | --- | --- |
| `DRAFT` | SUBMIT | `PENDING_APPROVAL` | Maker | No |
| `PENDING_APPROVAL` | APPROVE | `APPROVED` | Checker / Admin | No |
| `PENDING_APPROVAL` | REWORK | `REWORK` | Checker / Admin | **Yes** |
| `REWORK` | SUBMIT | `PENDING_APPROVAL` | Maker | No |
| Any | PERMANENTLY_REJECT | `PERMANENTLY_REJECTED` | Checker / Admin | **Yes** |

---

### FR-PO-09 — API Endpoints

All endpoints prefixed with `/api/v1/`.

```
purchase-orders/                          GET (list), POST (create)
purchase-orders/{id}/                     GET (detail), PUT, PATCH
purchase-orders/{id}/line-items/          GET, POST
purchase-orders/{id}/line-items/{lid}/    PUT, DELETE
purchase-orders/{id}/workflow/            POST — body: { action, comment }
purchase-orders/{id}/pdf/                 GET — streams PDF
purchase-orders/{id}/audit-log/           GET
```

Register in `apps/purchase_order/urls.py` and include in `tradetocs/urls.py`.

---

### FR-PO-10 — Serializers

**PurchaseOrderSerializer**
- **List**: return `id`, `po_number`, `po_date`, `vendor` (name), `currency` (code), `status`, `created_by` (name), `total` (sum of all line item totals).
- **Detail**: return all header fields plus nested `line_items` and `tc_content`.
- **Create**: `po_number`, `status`, `created_by` are `read_only`.
- **State-aware**: when `status` is not `DRAFT` or `REWORK`, all fields become `read_only` (constraint 18, `technical_architecture.md` Section 9).

**PurchaseOrderLineItemSerializer**
- `taxable_amount`, `igst_amount`, `cgst_amount`, `sgst_amount`, `total_tax`, and `total` are `read_only` — computed on save, never accepted from the client.

**Filtering (via ****`django-filter`****):** `status`, `created_by`, `vendor` (exact); `po_number` (partial search).

Default ordering: `-created_at`.

---

### FR-PO-11 — Permissions

| Action | Permission |
| --- | --- |
| List / Detail | `IsAnyRole` |
| Create | `IsAnyRole` |
| Update / PATCH (DRAFT or REWORK only) | `IsDocumentOwner` |
| Workflow actions | Validated inside `WorkflowService` |
| Audit log | `IsAnyRole` |
| PDF download | `IsAnyRole` |

Every view must explicitly declare `permission_classes` (constraint 29, Section 9).

---

### FR-PO-12 — Tests

**`tests/factories.py`****:**
- `PurchaseOrderFactory` — DRAFT PO with vendor (tagged VENDOR), delivery address, internal contact, currency, one line item.
- `PurchaseOrderLineItemFactory` — single line item with realistic decimal values.

**`tests/test_models.py`****:**
- `po_number` is auto-generated on create.
- `PurchaseOrderLineItem.save()` correctly computes `tax_amount` and `total`.

**`tests/test_views.py`** (minimum):
- Maker creates a PO → 201 with `po_number`.
- Unauthenticated request → 401.
- Submit → Approve full round-trip.
- Submit → Rework → resubmit round-trip.
- Checker cannot edit content fields after `PENDING_APPROVAL`.
- REWORK blocked if comment is empty.
- PERMANENTLY_REJECT blocked if comment is empty.

```
pytest --cov=apps/purchase_order --cov-report=term-missing
```

---

## Stage 5 — Frontend: Navigation and List Page

### FR-PO-13 — Sidebar Entry

Add **Purchase Order** to the sidebar in `AppLayout.tsx`.

- Visible to: All roles
- Route: `/purchase-orders`
- Position: After "Commercial Invoice", before "Master Data"
- Icon: `FileProtectOutlined` (Ant Design)

Add the route to `App.tsx` wrapped in `ProtectedRoute` (no role restriction).

### Wireframe — Sidebar (Purchase Order entry highlighted)

```
┌──────────────────────┐
│  TradeDocs           │
├──────────────────────┤
│ 📊 Dashboard         │
│                      │
│ 📄 Proforma Invoice  │
│ 📦 Packing List      │
│ 🧾 Commercial Invoice│
│ ▶ Purchase Order  ←  │  new entry
│                      │
│ ▼ Master Data        │
│   Organisations      │
│   Banks              │
│   Reference Data     │
│   T&C Templates      │
│                      │
│ 👥 User Management   │
│ 📈 Reports           │
└──────────────────────┘
```

---

### FR-PO-14 — PurchaseOrderListPage

File: `frontend/src/pages/purchase-order/PurchaseOrderListPage.tsx`
API file: `frontend/src/api/purchaseOrders.ts`

**Rules:**
- Page title: "Purchase Orders"
- Primary button: "+ New Purchase Order" → `/purchase-orders/new`
- Visible to all roles. Makers see only their own documents; Checkers and Admins see all.
- Default sort: newest PO date first.

**Table columns:**

| Column | Sortable | Notes |
| --- | --- | --- |
| PO Number | Yes | Links to `/purchase-orders/{id}` |
| PO Date | Yes | Formatted `DD MMM YYYY` |
| Vendor | Yes | Organisation name |
| Currency | No | Currency code, e.g. USD |
| Total | Yes | Sum of all line item totals; 2 decimal places |
| Status | Yes | `StatusBadge` component |
| Actions | No | "View" link; Edit icon only in DRAFT/REWORK and only to document owner |

**Search and filters:**
- Search box: `po_number` partial match
- Status filter: All / Draft / Pending Approval / Approved / Rework / Permanently Rejected
- Vendor filter: dropdown of active Vendor-tagged organisations
- Date range: PO Date from / to

**Empty state:** *"No purchase orders found. Create your first one."* with a "New Purchase Order" button.

### Wireframe — List Page

```
┌──────────────────────────────────────────────────────────────────────┐
│ Purchase Orders                          [+ New Purchase Order]      │
├──────────────────────────────────────────────────────────────────────┤
│ [Search by PO number...]  [Status ▼]  [Vendor ▼]  [Date from][to]  │
├────────────┬────────────┬──────────────┬──────┬───────────┬─────────┤
│ PO Number ↕│ PO Date  ↕ │ Vendor      ↕│ Curr │ Total   ↕ │ Status  │
├────────────┼────────────┼──────────────┼──────┼───────────┼─────────┤
│ PO-2026-   │ 22 Mar     │ Shreas       │ USD  │ 61,884.00 │ [DRAFT] │
│ 0003       │ 2026       │ Industries   │      │           │         │
│            │            │              │      │    [View] [Edit]    │
├────────────┼────────────┼──────────────┼──────┼───────────┼─────────┤
│ PO-2026-   │ 18 Mar     │ ABC Chem     │ EUR  │ 24,500.00 │[PENDING]│
│ 0002       │ 2026       │ GmbH         │      │           │         │
│            │            │              │      │       [View]        │
├────────────┼────────────┼──────────────┼──────┼───────────┼─────────┤
│ PO-2026-   │ 10 Mar     │ Global       │ USD  │ 98,200.00 │[APPRVD] │
│ 0001       │ 2026       │ Suppliers    │      │           │         │
│            │            │              │      │[View][PDF]          │
└────────────┴────────────┴──────────────┴──────┴───────────┴─────────┘
```

---

## Stage 6 — Frontend: Create / Edit Form

### FR-PO-15 — PurchaseOrderFormPage

File: `frontend/src/pages/purchase-order/PurchaseOrderFormPage.tsx`

Handles both **create** mode (`/purchase-orders/new`) and **edit** mode (`/purchase-orders/{id}/edit`). Single scrollable page with four sections.

---

#### Section 1 — Purchase Order Header

| Field | UI Control | Required | Notes |
| --- | --- | --- | --- |
| PO Number | Read-only text | — | `[Auto-generated]` before first save; shows `PO-YYYY-NNNN` after |
| PO Date | Date picker | Yes | Defaults to today |
| Customer No. | Text input | No | Vendor's reference number for this buyer |
| Vendor | Dropdown | Yes | Active organisations tagged `VENDOR` |
| Internal Contact | Dropdown | Yes | All active users; shows full name + role |
| Internal Contact Phone | Read-only text | — | Auto-populated after contact is selected; not editable here |
| Delivery Address | Dropdown | Yes | Loaded after Vendor is selected; shows all `DELIVERY` addresses for that vendor. Auto-selected if only one exists. Shows inline warning if none: *"This vendor has no delivery addresses. Add one in Organisation master."* |
| Bank | Dropdown | No | All active banks; shown as "Bank Name – Beneficiary Name" |
| Currency | Dropdown | Yes | All active currencies |
| Transaction Type | Dropdown | Yes | Controls tax columns on line items. Options: **Same State Transaction (CGST+SGST)**, **Inter State Transaction (IGST)**, **Procurement for Export (Zero-Rated)**. Changing this clears all tax values on existing line items. |
| Payment Terms | Dropdown | No | All active payment terms |
| Country of Origin | Dropdown | No | All active countries |
| Time of Delivery | Text input | No | Free text |

**Vendor → Delivery Address dependency:** Changing the Vendor resets and reloads the Delivery Address dropdown.

### Wireframe — Section 1 (Header)

```
┌──────────────────────────────────────────────────────────────────────┐
│ New Purchase Order                                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PO Number               PO Date                                    │
│  [Auto-generated]        [22/03/2026        📅]                     │
│                                                                      │
│  Vendor *                Customer No.                                │
│  [Select vendor...    ▼] [e.g. 71931              ]                  │
│                                                                      │
│  Internal Contact *                                                  │
│  [Select contact...   ▼]                                             │
│  📞 +91 98765 43210  ← auto-populated, read-only                    │
│                                                                      │
│  Delivery Address *                                                  │
│  [Select delivery address...                   ▼]                   │
│  ⚠ This vendor has no delivery addresses. Add one in Org master.    │
│    (shown only when vendor has no DELIVERY addresses)               │
│                                                                      │
│  Bank                    Currency *                                  │
│  [Select bank...      ▼] [USD                  ▼]                   │
│                                                                      │
│  Transaction Type *                                                  │
│  [Inter State Transaction (IGST)               ▼]                   │
│   ○ Same State Transaction (CGST+SGST)                              │
│   ● Inter State Transaction (IGST)                                  │
│   ○ Procurement for Export (Zero-Rated)                             │
│  ⚠ Changing transaction type will clear all tax values on          │
│    existing line items.                                              │
│                                                                      │
│  Payment Terms           Country of Origin                          │
│  [Select terms...     ▼] [Select country...    ▼]                   │
│                                                                      │
│  Time of Delivery                                                    │
│  [prompt / August 2025                              ]               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

#### Section 2 — Line Items

A single inline table. Each row is one `PurchaseOrderLineItem`. The tax columns in the table change based on the **Transaction Type** selected in Section 1. All other columns are always visible.

**Always-visible columns:**

| Column | Control | Required | Notes |
| --- | --- | --- | --- |
| # | Read-only | — | Row number |
| Description | Text input | Yes | Product / goods name |
| Item Code | Text input | No | Internal code |
| NCM / HSN | Text input | No | NCM / HSN classification code |
| Manufacturer | Text input | No | Manufacturer name |
| FCL | Text input | No | Container count or type |
| UOM | Dropdown | Yes | Active UOM records; column header label shows selected UOM dynamically, e.g. "Unit (MT)" |
| Unit (UOM) | Number input | Yes | Up to 6dp; stores exactly what the user types |
| Packaging Qty | Text input | No | Free text, e.g. "4,320 25kg bags without pallets" |
| Unit Price | Number input (2dp) | Yes | In selected PO currency |
| Taxable Amt | Read-only | — | `Unit (UOM) × Unit Price`; updates live |

**Dynamic tax columns (controlled by Transaction Type):**

| Transaction Type | Columns shown after Taxable Amt |
| --- | --- |
| Inter State (IGST) | IGST% (input) → IGST Amt (read-only) → Total Tax (read-only) |
| Same State (CGST+SGST) | CGST% (input) → CGST Amt (read-only) → SGST% (input) → SGST Amt (read-only) → Total Tax (read-only) |
| Procurement for Export (Zero-Rated) | *(no tax columns)* |

**Last column (always visible):** Line Total (read-only) = `Taxable Amt + Total Tax`

**Validation:**
- IGST: `igst_percent` required if transaction type is IGST.
- CGST_SGST: both `cgst_percent` and `sgst_percent` required; they must be equal.
- ZERO_RATED: no tax input required; all tax fields set to zero automatically.
- Changing Transaction Type clears all tax inputs on all rows and shows a confirmation: *"Changing the transaction type will clear all tax values. Continue?"*

**Summary row (live-calculated):** One row — **Total [Currency]** — sum of all line item `total` values.

**"+ Add Item"** appends a new blank row. At least one line item must exist before the PO can be submitted.

### Wireframe — Section 2: Inter State Transaction (IGST)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Line Items                                                                                        │
├───┬──────────────┬──────────┬──────────┬──────────┬─────┬──────┬──────────┬──────────┬───────────┤
│ # │ Description  │Item Code │ NCM/HSN  │  Mfr     │ FCL │ UOM  │Unit (MT) │Pkg Qty   │Unit Price │
├───┼──────────────┼──────────┼──────────┼──────────┼─────┼──────┼──────────┼──────────┼───────────┤
│ 1 │[Caustic Soda]│[3004    ]│[2815.11 ]│[Shreas  ]│[4  ]│[MT▼] │[108.00  ]│[4320 bags│[573.00   ]│
│   │              │          │          │          │     │      │          │ no pall. ]│           │
├───┴──────────────┴──────────┴──────────┴──────────┴─────┴──────┴──────────┴──────────┴───────────┤
│  Taxable Amt    IGST %      IGST Amt   Total Tax  Line Total                           [🗑]       │
│  61,884.00      [18.00]     11,139.12  11,139.12  73,023.12                                       │
├───┬──────────────┬──────────┬──────────┬──────────┬─────┬──────┬──────────┬──────────┬───────────┤
│ 2 │[             ]│[       ]│[        ]│[        ]│[   ]│[   ▼]│[        ]│[         │[         ]│
├───┴──────────────┴──────────┴──────────┴──────────┴─────┴──────┴──────────┴──────────┴───────────┤
│  Taxable Amt    IGST %      IGST Amt   Total Tax  Line Total                           [🗑]       │
│  0.00           [      ]    0.00       0.00       0.00                                            │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [+ Add Item]                                                                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                              Total USD        73,023.12           │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Wireframe — Section 2: Same State Transaction (CGST+SGST)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Line Items                                                                                        │
├───┬──────────────┬──────────┬──────────┬──────────┬─────┬──────┬──────────┬──────────┬───────────┤
│ # │ Description  │Item Code │ NCM/HSN  │  Mfr     │ FCL │ UOM  │Unit (MT) │Pkg Qty   │Unit Price │
├───┼──────────────┼──────────┼──────────┼──────────┼─────┼──────┼──────────┼──────────┼───────────┤
│ 1 │[Caustic Soda]│[3004    ]│[2815.11 ]│[Shreas  ]│[4  ]│[MT▼] │[108.00  ]│[4320 bags│[573.00   ]│
├───┴──────────────┴──────────┴──────────┴──────────┴─────┴──────┴──────────┴──────────┴───────────┤
│  Taxable Amt  CGST%    CGST Amt  SGST%    SGST Amt  Total Tax  Line Total                [🗑]     │
│  61,884.00   [9.00]   5,569.56  [9.00]   5,569.56  11,139.12  73,023.12                          │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [+ Add Item]                                                                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                              Total USD        73,023.12           │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Wireframe — Section 2: Procurement for Export (Zero-Rated)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Line Items                                                                                        │
├───┬──────────────┬──────────┬──────────┬──────────┬─────┬──────┬──────────┬──────────┬───────────┤
│ # │ Description  │Item Code │ NCM/HSN  │  Mfr     │ FCL │ UOM  │Unit (MT) │Pkg Qty   │Unit Price │
├───┼──────────────┼──────────┼──────────┼──────────┼─────┼──────┼──────────┼──────────┼───────────┤
│ 1 │[Caustic Soda]│[3004    ]│[2815.11 ]│[Shreas  ]│[4  ]│[MT▼] │[108.00  ]│[4320 bags│[573.00   ]│
├───┴──────────────┴──────────┴──────────┴──────────┴─────┴──────┴──────────┴──────────┴───────────┤
│  Taxable Amt    Line Total                                                            [🗑]        │
│  61,884.00      61,884.00                                                                         │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [+ Add Item]                                                                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                              Total USD        61,884.00           │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### Section 3 — Terms & Conditions

| Field | UI Control | Required | Notes |
| --- | --- | --- | --- |
| T&C Template | Dropdown | No | All active T&C templates — not filtered by vendor |
| T&C Content | Read-only rich-text preview | No | Auto-populated on template selection; snapshot stored with document |

### Wireframe — Section 3 (T&C)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Terms & Conditions                                                   │
│                                                                      │
│  Template                                                            │
│  [General Purchase T&C                              ▼]              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 1. Application                                                 │ │
│  │ These terms and conditions of purchase shall apply             │ │
│  │ exclusively. Differing or contrary terms shall not apply       │ │
│  │ except if expressly agreed upon in writing.                    │ │
│  │                                                                │ │
│  │ 2. Offer, Acceptance                                           │ │
│  │ The seller shall accept the buyer's order in writing...        │ │
│  │                                                          [read-only preview]
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

#### Section 4 — Remarks and Actions

| Field | UI Control | Required |
| --- | --- | --- |
| Remarks | Multi-line text area | No |

### Wireframe — Section 4 (Remarks + Action buttons)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Remarks                                                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ GOODS MUST MEET SPECIFICATIONS AND MUST BE FRESHLY PRODUCED!   │ │
│  │ DELIVERY: Goods must be loaded within 2-3 weeks of order       │ │
│  │ confirmation. Transit-time must be the shortest possibility.   │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

                           [Cancel]  [Save as Draft]  [Submit for Approval]
                                      (always)          (DRAFT / REWORK only)
```

---

## Stage 7 — Frontend: Detail Page and PDF

### FR-PO-16 — PurchaseOrderDetailPage

File: `frontend/src/pages/purchase-order/PurchaseOrderDetailPage.tsx`

Read-only view for Checkers/Admins reviewing the PO, and for all roles once the PO has left DRAFT state.

**Layout sections:**
1. Page header bar — PO number, date, status badge, workflow action buttons
2. Two-column info block — left: vendor details; right: delivery + contact details
3. Document details strip — bank, currency, payment terms, country of origin, time of delivery
4. Line items table (read-only)
5. Summary block — total only
6. Terms & Conditions (collapsible)
7. Remarks (if present)
8. Audit Log (collapsible drawer)

**Workflow actions (via ****`WorkflowActionButton`****):**

| Role | Status | Actions |
| --- | --- | --- |
| Maker (document owner) | DRAFT | [Edit]  [Submit for Approval] |
| Maker (document owner) | REWORK | [Edit]  [Submit for Approval] |
| Checker / Company Admin | PENDING_APPROVAL | [Approve]  [Rework]  [Permanently Reject] |
| Checker / Company Admin | Any state | [Permanently Reject] |
| Any role | APPROVED | [Download PDF] |

### Wireframe — Detail Page

```
┌──────────────────────────────────────────────────────────────────────┐
│ PO-2026-0003                22 Mar 2026     [● PENDING APPROVAL]    │
│                                      [Approve] [Rework] [Perm.Rej.] │
├───────────────────────────────┬──────────────────────────────────────┤
│ Vendor                        │ Delivery Address                     │
│ Shreas Industries Ltd.        │ Northern Trading Solutions GmbH      │
│ SY NO 115-2, Chittivalasa     │ Wellingsbuetteler Landstr. 128       │
│ Village, Andhra Pradesh       │ 22337 Hamburg, Germany               │
│ India                         │ TAX: DE295875226                     │
│                               │                                      │
│ Customer No: 71931            │ Internal Contact: Sicco Harrendorf   │
│                               │ 📞 +49 40 500 539 96                │
├───────────────────────────────┴──────────────────────────────────────┤
│ Bank: Hamburger Volksbank – USD  │ Currency: USD                     │
│ Payment Terms: CAD 1 week        │ Country of Origin: India          │
│ Time of Delivery: prompt / August 2025                               │
├──────────────────────────────────────────────────────────────────────┤
│ Line Items  (Inter State Transaction — IGST)                        │
├───┬──────────────────┬───────┬─────────┬──────────┬───────┬─────────┤
│ # │ Description      │Unit(MT│Taxable  │ IGST%    │IGST   │ Total   │
│   │ Item / NCM / Mfr │) /Pkg │ Amt     │          │ Amt   │         │
├───┼──────────────────┼───────┼─────────┼──────────┼───────┼─────────┤
│ 1 │ Caustic Soda     │108.00 │61,884.00│  18%     │11,139 │73,023.12│
│   │ Item: 3004       │4,320  │         │          │       │         │
│   │ NCM: 2815.11.00  │25kg   │         │          │       │         │
│   │ Mfr: Shreas Ind. │bags   │         │          │       │         │
├───┴──────────────────┴───────┴─────────┴──────────┴───────┴─────────┤
│                                           Total USD      73,023.12  │
├──────────────────────────────────────────────────────────────────────┤
│ [▶ Show Terms & Conditions]                                          │
├──────────────────────────────────────────────────────────────────────┤
│ Remarks                                                              │
│ GOODS MUST MEET SPECIFICATIONS AND MUST BE FRESHLY PRODUCED!...     │
├──────────────────────────────────────────────────────────────────────┤
│ [▶ Audit Log]                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### Wireframe — Rework / Reject Comment Modal

```
  ┌──────────────────────────────────────────────┐
  │ Rework — Add Comment                         │
  │                                              │
  │ Comment *                                    │
  │ ┌────────────────────────────────────────┐   │
  │ │ Please update the NCM code for item 1  │   │
  │ │ and confirm the delivery address.      │   │
  │ └────────────────────────────────────────┘   │
  │ Comment is required to send for rework.      │
  │                                              │
  │                    [Cancel]  [Confirm Rework] │
  └──────────────────────────────────────────────┘
```

---

### FR-PO-17 — PDF Generation

PDF is generated in-memory and streamed (constraint 20, `technical_architecture.md` Section 9). Exact layout to be confirmed in a follow-up before this step is built.

**No logo or letterhead** is included on the PDF. The document header will show the issuing company name and details as plain text only.

| State | PDF available | Watermark |
| --- | --- | --- |
| Draft | All roles | Diagonal "DRAFT" |
| Pending Approval | All roles | Diagonal "DRAFT" |
| Rework | All roles | Diagonal "DRAFT" |
| Approved | All roles | None — clean final PDF |

Endpoint: `GET /api/v1/purchase-orders/{id}/pdf/`
Suggested filename: `PO-{po_number}.pdf`

---

## Constants to Add

**`frontend/src/utils/constants.ts`****:**
```typescript
VENDOR: "VENDOR"                          // organisation tag
DELIVERY: "DELIVERY"                      // address type
DOCUMENT_TYPES.PURCHASE_ORDER: "purchase_order"
```

**`apps/workflow/constants.py`****:**
```python
DOCUMENT_TYPE_PURCHASE_ORDER = "purchase_order"
```

---

## Open Questions

| # | Question | Status | Decision |
| --- | --- | --- | --- |
| OQ-PO-01 | Can a PO be linked to a Proforma Invoice? | **Closed** | No link to PI. PO is a standalone document. |
| OQ-PO-02 | Should the PDF include the company's own logo/letterhead? | **Closed** | No logo. Company name and details printed as plain text. |
| OQ-PO-03 | Should PO number be manually overridable by the Maker? | **Closed** | Always auto-generated. `po_number` is permanently `read_only`. |
| OQ-PO-04 | Can a Maker delete a DRAFT PO? | **Closed** | Same states and delete logic as all other documents. No special handling. |
| OQ-PO-05 | Should the T&C template dropdown filter to templates associated with the selected Vendor, or show all active templates? | **Closed** | Show all active templates. No filtering by vendor. |
| OQ-PO-06 | Are Subtotal and Net Amount always equal, or can a discount be applied? | **Closed** | One total only. No subtotal or net amount rows anywhere. |
