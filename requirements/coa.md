# Product Requirements Document — Certificate of Analysis (COA)

**Version:** 1.1
**Status:** Draft
**Last Updated:** 2026-06-01

---

## 1. Overview

A **Certificate of Analysis (COA)** is a quality assurance document issued by the exporter certifying that a product batch meets defined quality and purity specifications. It accompanies chemical, pharmaceutical, and regulated product shipments and is required by buyers, customs authorities, and regulatory bodies.

The COA follows the same maker–checker approval workflow as all other documents in TradeDocs. All workflow rules from **FR-08** apply without modification.

**Document number format:** `COA-YYYY-NNNN`

---

## 2. Development Sequence

| Stage | What gets built |
| --- | --- |
| **Stage 1** | New master data — Product (with Grades), Test Parameter, Test Method, and Product Test Template |
| **Stage 2** | Backend Django app — COA model, line items, number generation, API, workflow |
| **Stage 3** | Frontend navigation and list page |
| **Stage 4** | Frontend create / edit form |
| **Stage 5** | Frontend detail / review page |
| **Stage 6** | PDF generation |

---

## Stage 1 — New Master Data

### FR-COA-01 — Product Master

Products and their grades are managed together on a single page. A product (the chemical) is a parent record; its grades are child records. This is a 1-to-many relationship stored in two tables: `Product` and `ProductGrade`.

**Backend (`apps/master_data/`):**

**`Product`** — one row per chemical:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `CharField(255)`, unique | e.g. "Chloroform", "Acetone", "Methanol" |
| `cas_number` | `CharField(20)`, blank | Chemical Abstracts Service registry number, e.g. "67-66-3" |
| `is_active` | `BooleanField(default=True)` | Soft-delete; never hard-deleted |

**`ProductGrade`** — one row per (product, grade) pair:

| Field | Type | Notes |
| --- | --- | --- |
| `product` | `FK → Product`, `on_delete=CASCADE` | Parent chemical |
| `grade` | `CharField(100)` | e.g. "Technical", "Pharmaceutical", "Industrial", "Laboratory" |
| `is_active` | `BooleanField(default=True)` | Soft-delete; never hard-deleted |

- `unique_together = ('product', 'grade')` enforced at the DB level.
- FK references to `ProductGrade` from the COA model must use `on_delete=PROTECT` — you cannot delete a grade that is already used on a COA.
- Expose via `ProductViewSet` and `ProductGradeViewSet`.

**Frontend — Reference Data Page:**
- Add a **"Products"** tab alongside existing tabs.
- The Products list shows one row per **chemical** (not per grade). Columns: Name, CAS Number, Status, Actions.
- Each product row shows its grades as an inline chip list (e.g. `Technical  Pharmaceutical`).
- Actions per product row: **Edit** (name, CAS number), **Manage Grades**, **Deactivate**.
- **Manage Grades** opens an inline panel or modal showing the grades for that product with their active status. The user can add a new grade (text input with common suggestions: Technical, Pharmaceutical, Industrial, Laboratory), edit a grade name, or deactivate/reactivate a grade.
- Deactivating a product automatically deactivates all its grades; the COA form will not show deactivated products or grades.

**Seed data:**

| Product (chemical) | CAS Number | Grades to create |
| --- | --- | --- |
| Chloroform | 67-66-3 | Technical, Pharmaceutical |
| Acetone | 67-64-1 | Technical, Industrial |
| Methanol | 67-56-1 | Technical, Industrial |
| Carbon Tetrachloride | 56-23-5 | Technical |
| Methylene Chloride | 75-09-2 | Technical |
| Bromo Chloromethane | 74-97-5 | Technical |

**Wireframe — Reference Data: Products tab**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Reference Data                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│ [Countries] [Ports] [UOM] [Payment Terms] [Incoterms] [Pre-Carriage]   │
│ [Package Types] [Test Parameters] [Test Methods] [Products]  ← new tabs │
├──────────────────────────────────────────────────────────────────────────┤
│ Products                                              [+ Add Product]   │
│                                                                          │
│  Name                  CAS Number  Grades                   Status  Actions     │
│  ──────────────────────────────────────────────────────────────────────  │
│  Acetone               67-64-1     Technical  Industrial    Active  [Edit][Manage Grades][Deact]│
│  Chloroform            67-66-3     Technical  Pharmaceutical Active [Edit][Manage Grades][Deact]│
│  Carbon Tetrachloride  56-23-5     Technical                Active  [Edit][Manage Grades][Deact]│
└──────────────────────────────────────────────────────────────────────────┘

  Add / Edit Product modal:         Manage Grades panel (inline):
  ┌─────────────────────────────┐   ┌──────────────────────────────────┐
  │ Add Product                 │   │ Grades — Chloroform              │
  │                             │   │                                  │
  │ Name *                      │   │  Technical      Active  [Deact]  │
  │ ┌─────────────────────────┐ │   │  Pharmaceutical Active  [Deact]  │
  │ │ e.g. Chloroform         │ │   │                                  │
  │ └─────────────────────────┘ │   │  Add grade:                      │
  │                             │   │  ┌──────────────────────┐        │
  │ CAS Number                  │   │  │ e.g. Industrial    ▼ │ [Add]  │
  │ ┌─────────────────────────┐ │   │  └──────────────────────┘        │
  │ │ e.g. 67-66-3            │ │   └──────────────────────────────────┘
  │ └─────────────────────────┘ │
  │                             │
  │          [Cancel]  [Save]   │
  └─────────────────────────────┘
```

---

### FR-COA-02 — Test Parameter Master

A library of standard test characteristics/parameters used as dropdown options in the COA test results table.

**Backend (`apps/master_data/`):**
- New `TestParameter` model:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `CharField(255)`, unique | e.g. "Appearance", "Purity, percent by mass, Min", "Moisture, percent by mass, Max" |
| `default_unit` | `FK → UOM`, null=True, blank=True, `on_delete=PROTECT` | Pre-fills the Unit column when this parameter is selected |
| `is_active` | `BooleanField(default=True)` | Soft-delete |

- Expose via `TestParameterViewSet`.

**Frontend — Reference Data Page:**
- Add a **"Test Parameters"** tab.
- Columns: Name, Default Unit, Status, Actions.
- Add / Edit modal: Name (required), Default Unit (optional dropdown from UOM master).

**Seed data (common chemical parameters):**
Appearance, Colour (Hazen), Purity, Moisture, Acidity, Free Chlorine, Residue on Evaporation, Carbon Tetrachloride content, Methylene Chloride content, Amylene as Stabilizer, Bromo Chloromethane.

---

### FR-COA-03 — Test Method Master

A library of standard test method codes referenced in COA tables.

**Backend (`apps/master_data/`):**
- New `TestMethod` model:

| Field | Type | Notes |
| --- | --- | --- |
| `code` | `CharField(50)`, unique | e.g. "ASTM D3741-00", "IS 5296-K", "In house" |
| `description` | `CharField(255)`, blank | Full name of the standard or method |
| `is_active` | `BooleanField(default=True)` | Soft-delete |

- Expose via `TestMethodViewSet`.

**Frontend — Reference Data Page:**
- Add a **"Test Methods"** tab.
- Columns: Code, Description, Status, Actions.
- Add / Edit modal: Code (required), Description (optional).

**Seed data:** ASTM D3741-00, ASTM D2108-10, ASTM D6806-02, ASTM D2109-01, ASTM D2989-01, ASTM D3401, IS 5296-K, IS 5296-C, IS 5296-D, IS 5296-E, IS 5296-J, In house.

---

### FR-COA-04 — Product Test Template

Each `ProductGrade` can have a **test template** — a saved set of standard test parameter rows (characteristic, unit, specification, test method) that is automatically loaded into the test table whenever that product + grade combination is selected on a new COA. The user can then edit, add, or remove rows before saving.

The template stores specifications only — no result values, since results vary per batch.

**Backend (`apps/master_data/`):**

Two new models linked to `ProductGrade`:

**`ProductTestTemplate`** — one per product grade (1:1):

| Field | Type | Notes |
| --- | --- | --- |
| `product_grade` | `OneToOneField → ProductGrade`, `on_delete=CASCADE` | Each product grade has at most one template |
| `updated_at` | `DateTimeField(auto_now=True)` | Last modified timestamp |

**`ProductTestTemplateRow`** — the individual parameter rows of a template:

| Field | Type | Notes |
| --- | --- | --- |
| `template` | `FK → ProductTestTemplate`, CASCADE | Parent template |
| `s_no` | `PositiveIntegerField` | Display order |
| `parameter` | `FK → TestParameter`, null=True, blank=True, `on_delete=PROTECT` | Optional; auto-fills label when selected |
| `parameter_label` | `CharField(255)` | Always required — the printed characteristic name |
| `unit` | `FK → UOM`, null=True, blank=True, `on_delete=PROTECT` | Blank for qualitative rows |
| `spec_type` | `CharField(20)`: `QUANTITATIVE` / `QUALITATIVE` | Required |
| `spec_min` | `DecimalField(max_digits=15, decimal_places=6)`, null=True | For QUANTITATIVE rows |
| `spec_max` | `DecimalField(max_digits=15, decimal_places=6)`, null=True | For QUANTITATIVE rows |
| `spec_description` | `TextField`, blank=True | For QUALITATIVE rows |
| `test_method` | `FK → TestMethod`, null=True, blank=True, `on_delete=PROTECT` | Optional |
| `test_method_label` | `CharField(100)`, blank=True | The test method string |

> Template rows have **no result fields** (`result_value`, `result_text`) — results are entered fresh per COA batch.

- Expose via `GET /api/product-grades/{id}/test-template/` — returns the template rows serialised in the same shape as `COAParameter` rows, so the frontend can insert them directly into the test table without transformation.
- `PUT /api/product-grades/{id}/test-template/` — full replace of template rows (admin/checker only). A save overwrites all existing rows for that product grade.

**Frontend — Products tab: Manage Template action:**

The Manage Grades panel (see FR-COA-01) adds a **"Manage Template"** button per grade row. Clicking it opens a dedicated template editor page with the same editable parameter table as the COA form, but **without the Result column** — only Characteristic, Unit, Spec Type, Specification, and Test Method columns are shown.

**Wireframe — Reference Data: Manage Grades panel (with Manage Template per grade)**

```
  Manage Grades panel — Chloroform:
  ┌──────────────────────────────────────────────────────┐
  │ Grades — Chloroform                                  │
  │                                                      │
  │  Technical      Active  [Manage Template] [Deact]    │
  │  Pharmaceutical Active  [Manage Template] [Deact]    │
  │                                                      │
  │  Add grade: ┌────────────────────┐                   │
  │             │ e.g. Industrial  ▼ │  [Add]            │
  │             └────────────────────┘                   │
  └──────────────────────────────────────────────────────┘
```

**Copy-from feature:**

When a template already exists for at least one other product grade, the template editor toolbar shows a **"Copy from…"** button. Clicking it opens a searchable dropdown listing every product grade that has a saved template (label format: "Name — Grade", e.g. "Chloroform — Technical"). Selecting a source fetches its template rows via `GET /api/product-grades/{source_id}/test-template/` and replaces the editor's current rows. A yellow banner appears: "Rows copied from Chloroform — Technical. Review and adjust before saving." No new backend endpoint is required — this is a frontend-only operation using the existing GET endpoint.

Use case: a user adds "Chloroform — Pharmaceutical" and wants to start from the "Chloroform — Technical" template. They click "Manage Template" on the Pharmaceutical grade row, click "Copy from…", select "Chloroform — Technical", adjust the few differing spec values, then save.

**Wireframe — Product Test Template editor**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Products                                                               │
│ Chloroform — Pharmaceutical · Test Template                              │
│                                          [Copy from…▼]  [Save Template] │
├──────────────────────────────────────────────────────────────────────────┤
│  ⚠ Rows copied from Chloroform — Technical. Review and adjust before    │
│    saving.                                                               │
├──────────────────────────────────────────────────────────────────────────┤
│  ℹ Define the standard parameters for this product. When a user selects │
│    Chloroform — Pharmaceutical on a new COA, these rows will be          │
│    pre-filled automatically. Results are not stored here.                │
├────┬──────────────────────┬────────┬──────────────┬──────────────┬──────┤
│ No │ Characteristic       │ Unit   │ Spec Type    │ Specification│Method│
├────┼──────────────────────┼────────┼──────────────┼──────────────┼──────┤
│ 1  │ [Appearance      ▼]  │ [   ▼] │ (•) Qual     │[Clear, Co…]  │[…▼] │
├────┼──────────────────────┼────────┼──────────────┼──────────────┼──────┤
│ 2  │ [Colour, Hazen   ▼]  │[Hazen▼]│ (•) Quant    │Max:[5      ] │[…▼] │
├────┼──────────────────────┼────────┼──────────────┼──────────────┼──────┤
│ 3  │ [Purity          ▼]  │ [%  ▼] │ (•) Quant    │Min:[99.90  ] │[…▼] │
├────┴──────────────────────┴────────┴──────────────┴──────────────┴──────┤
│                                                          [+ Add Row]    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 2 — Backend

### FR-COA-05 — COA Model and Line Items

New Django app: `apps/certificate_of_analysis/`

**Model: `CertificateOfAnalysis` (COA header)**

| Field | Django Type | Dropdown Source | Required |
| --- | --- | --- | --- |
| `coa_number` | `CharField(20)`, unique | Auto-generated | Yes (auto) |
| `product_grade` | `FK → ProductGrade`, `on_delete=PROTECT` | Product + Grade selected together on the form | Yes |
| `customer` | `FK → Organisation`, `on_delete=PROTECT` | Organisations tagged CONSIGNEE or BUYER | Yes |
| `batch_number` | `CharField(100)` | Free text | Yes |
| `package_count` | `PositiveIntegerField` | Number input | Yes |
| `package_volume` | `DecimalField(max_digits=12, decimal_places=3)` | Number input | Yes |
| `package_uom` | `FK → UOM`, `on_delete=PROTECT` | UOM master dropdown | Yes |
| `package_type` | `FK → TypeOfPackage`, `on_delete=PROTECT` | TypeOfPackage master dropdown | Yes |
| `date_of_despatch` | `DateField`, null=True, blank=True | Date picker | No |
| `date_of_manufacture` | `DateField` | Date picker | Yes |
| `date_of_retest` | `DateField` | Date picker | Yes |
| `date_time_of_sampling` | `DateTimeField` | Datetime picker | Yes |
| `date_time_of_analysis` | `DateTimeField` | Datetime picker | Yes |
| `analyst_name` | `CharField(150)` | Free text | Yes |
| `qc_incharge_name` | `CharField(150)` | Free text | Yes |
| `status` | `CharField(30)` | WorkflowService only | Yes (auto) |
| `footer_organisation` | `FK → Organisation`, `on_delete=PROTECT` | Organisations tagged CONSIGNEE or EXPORTER | Yes |
| `created_by` | `FK → User`, `on_delete=PROTECT` | Auto (request.user) | Yes (auto) |
| `created_at` | `DateTimeField(auto_now_add=True)` | — | Auto |
| `updated_at` | `DateTimeField(auto_now=True)` | — | Auto |

**Model: `COAParameter` (test result line items)**

Each row in the test results table. Belongs to one COA header.

| Field | Django Type | Dropdown Source | Notes |
| --- | --- | --- | --- |
| `coa` | `FK → CertificateOfAnalysis`, CASCADE | — | Parent document |
| `s_no` | `PositiveIntegerField` | Auto-numbered | Display order |
| `parameter` | `FK → TestParameter`, null=True, blank=True, `on_delete=PROTECT` | TestParameter master dropdown | If selected, `parameter_label` is pre-filled |
| `parameter_label` | `CharField(255)` | Free text or auto-filled from FK | Always required — the printed characteristic name |
| `unit` | `FK → UOM`, null=True, blank=True, `on_delete=PROTECT` | UOM master dropdown | Blank for qualitative rows |
| `spec_type` | `CharField(20)`: `QUANTITATIVE` / `QUALITATIVE` | Toggle on form | Controls which spec fields are active |
| `spec_min` | `DecimalField(max_digits=15, decimal_places=6)`, null=True, blank=True | Number input | Only for QUANTITATIVE |
| `spec_max` | `DecimalField(max_digits=15, decimal_places=6)`, null=True, blank=True | Number input | Only for QUANTITATIVE |
| `spec_description` | `TextField`, blank=True | Free text | Only for QUALITATIVE; printed in place of Min/Max |
| `result_value` | `DecimalField(max_digits=15, decimal_places=6)`, null=True, blank=True | Number input | For QUANTITATIVE results |
| `result_text` | `CharField(100)`, blank=True | Free text | For QUALITATIVE results (e.g. "Complies") |
| `test_method` | `FK → TestMethod`, null=True, blank=True, `on_delete=PROTECT` | TestMethod master dropdown | If selected, `test_method_label` is pre-filled |
| `test_method_label` | `CharField(100)`, blank=True | Free text or auto-filled from FK | The printed test method string |

**Validation rules:**
- `parameter_label` is always required (cannot be blank regardless of FK selection).
- QUANTITATIVE rows: at least one of `spec_min` or `spec_max` must be filled; `result_value` is required.
- QUALITATIVE rows: `spec_description` is required; `result_text` is required.
- At least 1 `COAParameter` row must exist before the COA can be submitted.
- `date_of_retest` must be on or after `date_of_manufacture`.
- `date_time_of_analysis` must be on or after `date_time_of_sampling`.

> **Decimal precision:** `spec_min`, `spec_max`, `result_value` use `decimal_places=6` (not 2) because trace-level chemical measurements (e.g. 0.0001%) require 6 significant decimal places. Never use FloatField.

---

### FR-COA-06 — Document Number Generation

- Format: `COA-YYYY-NNNN` where YYYY is the calendar year of creation and NNNN is a zero-padded sequential counter resetting each year.
- Use `select_for_update()` on a lock row to prevent duplicate numbers — same pattern as PI/PL/CI.
- Number is assigned on first save (DRAFT creation), not on submission.

---

### FR-COA-07 — API Endpoints

All endpoints require `permission_classes` declared explicitly (Rule #10).

| Method | URL | Action |
| --- | --- | --- |
| `GET` | `/api/coas/` | List all COAs (filterable by status, product, customer) |
| `POST` | `/api/coas/` | Create COA (status = DRAFT, number auto-assigned) |
| `GET` | `/api/coas/{id}/` | Retrieve COA detail with all parameters |
| `PATCH` | `/api/coas/{id}/` | Update COA (only allowed in DRAFT or REWORK state) |
| `POST` | `/api/coas/{id}/submit/` | Maker submits for approval |
| `POST` | `/api/coas/{id}/approve/` | Checker approves |
| `POST` | `/api/coas/{id}/reject/` | Checker rejects (comment required) |
| `POST` | `/api/coas/{id}/rework/` | Checker sends back for rework (comment required) |
| `GET` | `/api/coas/{id}/pdf/` | Stream COA PDF (in-memory, never to disk) |
| `GET` | `/api/product-grades/{id}/test-template/` | Fetch template rows for a product grade (returns empty list if no template exists) |
| `PUT` | `/api/product-grades/{id}/test-template/` | Save / replace template rows for a product grade (Checker and Company Admin only) |

All Axios calls for these endpoints must live in `src/api/coa.ts`. No component calls Axios directly (Rule #11).

---

### FR-COA-08 — Workflow

Same states and transitions as FR-08 (common workflow rules):

```
DRAFT → SUBMITTED → APPROVED
SUBMITTED → REJECTED → DRAFT
SUBMITTED → REWORK → DRAFT
```

- All transitions go through `WorkflowService` in `apps/workflow/services.py` (Rule #5).
- Every transition writes an `AuditLog` entry in the same `transaction.atomic()` (Rule #6).
- REJECT and REWORK actions must block if the comment field is empty (Rule #7).
- Makers can edit a COA only when it is in DRAFT or REWORK state.
- Checkers can approve/reject/rework only when status is SUBMITTED.

---

## Stage 3 — Frontend Navigation & List Page

### FR-COA-09 — Sidebar Entry

Add **"Certificate of Analysis"** to the left-hand navigation sidebar, visible to all roles (same visibility rule as PI, PL, CI).

### FR-COA-10 — COA List Page

Follows the same table + search pattern as the PI and PO list pages.

| Column | Notes |
| --- | --- |
| COA Number | Clickable link to detail page |
| Product | Chemical name — Grade (e.g. "Chloroform — Technical") |
| Customer | Organisation name |
| Batch Number | — |
| Date of Manufacture | Formatted date |
| Status | Colour-coded badge (same constants as other documents) |
| Actions | View / Edit (edit only shown when DRAFT or REWORK and user is Maker) |

- Filters: Status (dropdown), Product (dropdown from Product master — chemical names), Grade (dropdown from ProductGrade filtered by selected Product), Customer (dropdown from Organisation).
- Search: by COA number or batch number.
- Pagination: same as other list pages.

**Wireframe — COA List Page**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Certificate of Analysis                          [+ New COA]            │
├──────────────────────────────────────────────────────────────────────────┤
│ Search: [_______________] Status: [All ▼] Product: [All ▼]             │
├──────────────────────────────────────────────────────────────────────────┤
│ COA No.       Product                   Customer  Batch No.   Mfg Date   Status   │
│ ───────────────────────────────────────────────────────────────────────────────── │
│ COA-2026-0001 Chloroform — Technical    AGC       CFM/25/12/0 22-Dec-25  APPROVED │
│ COA-2026-0002 Acetone — Industrial      XYZ Corp  ACE/26/01/0 10-Jan-26  DRAFT    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 4 — Frontend Create / Edit Form

### FR-COA-11 — Create / Edit Form

Two-section form: **Header** and **Test Parameters**.

#### Header Section

| Label | Input Type | Source / Notes |
| --- | --- | --- |
| Product * | Searchable dropdown | Product master (active only); shows chemical names |
| Grade * | Dropdown | Active grades for the selected product only; disabled until a product is chosen |
| Customer * | Searchable dropdown | Organisations tagged CONSIGNEE or BUYER (active only) |
| Footer Company * | Searchable dropdown | Organisations tagged CONSIGNEE or EXPORTER (active only); if a company carries both tags it appears in the list only once; the selected company's addresses are printed in the PDF footer |
| Batch Number * | Text input | Free entry |
| Supplied Quantity * | Three inputs in one row: Count (integer) + Volume per package (decimal) + UOM (dropdown) | UOM master dropdown; display as "N x V UOM" |
| Package Type * | Dropdown | TypeOfPackage master (active only) |
| Date of Manufacture * | Date picker | — |
| Date of Retest * | Date picker | Auto-suggested as manufacture date + 1 year; user can override |
| Date of Despatch | Date picker | Optional; shown as "XXXX" on PDF if blank |
| Date & Time of Sampling * | Datetime picker | — |
| Date & Time of Analysis * | Datetime picker | Must be ≥ Date & Time of Sampling |
| Analyst Name * | Text input | Free entry |
| QC Incharge Name * | Text input | Free entry |

#### Test Parameters Section

An editable table where rows can be added, removed, and reordered. Minimum 1 row required.

Each row has these columns:

| Column | Input | Source / Notes |
| --- | --- | --- |
| S.No | Auto | Sequential, recomputed on reorder |
| Characteristic * | Searchable dropdown + free-text override | TestParameter master; selecting a parameter auto-fills the Unit if the parameter has a Default Unit |
| Unit | Dropdown (optional) | UOM master; leave blank for qualitative rows (e.g. Appearance, Free Chlorine) |
| Spec Type * | Toggle pill: Quantitative / Qualitative | Controls which specification and result inputs are visible |
| Spec Min | Decimal input | Shown only for Quantitative rows; optional (some specs are max-only) |
| Spec Max | Decimal input | Shown only for Quantitative rows; optional (some specs are min-only) |
| Spec Description | Text input | Shown only for Qualitative rows; e.g. "Clear, Colourless, Transparent and No Suspension" |
| Result | Decimal (Quantitative) or Text (Qualitative) | Qualitative result auto-suggests "Complies" |
| Test Method | Searchable dropdown + free-text override | TestMethod master; "In house" is a valid selection |

**Product + Grade selection — auto-populate behaviour:**
- Template lookup is triggered only when **both** Product and Grade are selected (i.e. a `ProductGrade` is fully resolved).
- Changing Product clears the Grade dropdown and any loaded template rows (after a confirmation if rows already exist).
- Once both Product and Grade are selected, the frontend calls `GET /api/product-grades/{id}/test-template/`.
- If a template exists: the test parameters table is immediately populated with all template rows (characteristic, unit, spec type, spec values, test method). A blue info banner appears above the table: "11 test parameters loaded from Chloroform — Technical template. You can edit, add, or remove rows before saving."
- If no template exists: the table remains empty and the user adds rows manually. No banner is shown.
- If the user changes Product or Grade after the table already has rows: a confirmation dialog appears — "Changing the product/grade will replace the current test parameters with the [Product — Grade] template. Any unsaved changes will be lost." — with [Replace] and [Keep current rows] buttons.
- Template rows are **copied** into the COA at creation time. Subsequent changes to the template do not affect existing COAs, and changes made in the COA form do not update the template.

**Row interactions:**
- Clicking the Characteristic dropdown shows the TestParameter list. User can also type to search, or type a new value not in the list (free-text override stored in `parameter_label`).
- Selecting a TestParameter auto-fills Unit if `default_unit` is set on that parameter.
- Switching Spec Type hides irrelevant inputs and clears their values.
- The [+ Add Row] button appends a blank row at the bottom.
- Each row has a [Remove] button (trash icon); disabled when only one row remains.
- Rows can be dragged to reorder; S.No updates automatically.

**Wireframe — COA Form: Header**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ New Certificate of Analysis                                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Product *                    Grade *                                    │
│  ┌────────────────────────┐   ┌────────────────────────┐                │
│  │ Chloroform          ▼  │   │ Technical            ▼ │                │
│  └────────────────────────┘   └────────────────────────┘                │
│                                                                          │
│  Customer *                                                              │
│  ┌────────────────────────┐                                              │
│  │ AGC                  ▼ │                                              │
│  └────────────────────────┘                                              │
│                                                                          │
│  Batch Number *                                                          │
│  ┌────────────────────────────────────────────────────┐                 │
│  │ CFM/25/12/0733                                     │                 │
│  └────────────────────────────────────────────────────┘                 │
│                                                                          │
│  Supplied Quantity *                           Package Type *            │
│  ┌──────────┐  ┌───────────────┐  ┌──────┐   ┌────────────────────┐    │
│  │  1  (no.)│x │  1000 (vol.)  │  │ ml ▼│   │ Bottles          ▼ │    │
│  └──────────┘  └───────────────┘  └──────┘   └────────────────────┘    │
│                                                                          │
│  Date of Manufacture *         Date of Retest *                         │
│  ┌────────────────────────┐   ┌────────────────────────┐                │
│  │ 22 / 12 / 2025     📅  │   │ 21 / 12 / 2026     📅  │                │
│  └────────────────────────┘   └────────────────────────┘                │
│                                                                          │
│  Date of Despatch                                                        │
│  ┌────────────────────────┐                                              │
│  │                    📅  │  (optional)                                  │
│  └────────────────────────┘                                              │
│                                                                          │
│  Date & Time of Sampling *     Date & Time of Analysis *                │
│  ┌────────────────────────┐   ┌────────────────────────┐                │
│  │ 25/12/2025 18:00   📅  │   │ 25/12/2025 19:25   📅  │                │
│  └────────────────────────┘   └────────────────────────┘                │
│                                                                          │
│  Analyst Name *                QC Incharge Name *                       │
│  ┌────────────────────────┐   ┌────────────────────────┐                │
│  │                        │   │                        │                │
│  └────────────────────────┘   └────────────────────────┘                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Wireframe — COA Form: Test Parameters**

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Test Parameters                                                                                  │
├────┬──────────────────────┬────────┬──────────────┬────────────┬────────────┬───────────┬────────┤
│ No │ Characteristic       │ Unit   │ Spec Type    │ Spec       │ Result     │ Method    │        │
├────┼──────────────────────┼────────┼──────────────┼────────────┼────────────┼───────────┼────────┤
│ 1  │ [Appearance      ▼]  │ [   ▼] │ (•) Qual     │ [Clear,    │ [Complies] │[ASTM D374]│ [🗑]  │
│    │                      │        │ ( ) Quant    │  Colourles]│            │           │        │
├────┼──────────────────────┼────────┼──────────────┼────────────┼────────────┼───────────┼────────┤
│ 2  │ [Colour, Hazen   ▼]  │[Hazen▼]│ ( ) Qual     │ Min: [   ] │ [< 5.0   ] │[ASTM D210]│ [🗑]  │
│    │                      │        │ (•) Quant    │ Max: [5   ]│            │           │        │
├────┼──────────────────────┼────────┼──────────────┼────────────┼────────────┼───────────┼────────┤
│ 3  │ [Purity          ▼]  │ [%  ▼] │ ( ) Qual     │ Min: [99.9]│ [99.96   ] │[ASTM D680]│ [🗑]  │
│    │                      │        │ (•) Quant    │ Max: [   ] │            │           │        │
├────┴──────────────────────┴────────┴──────────────┴────────────┴────────────┴───────────┴────────┤
│                                                                           [+ Add Row]            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

[Save as Draft]   [Submit for Approval]
```

---

## Stage 5 — Frontend Detail / Review Page

### FR-COA-12 — Detail Page

Read-only view of the full COA.

**Layout:**
- Top bar: COA number, status badge, action buttons (Submit / Approve / Reject / Rework) based on user role and current status.
- Header info card: all header fields displayed as label–value pairs in a two-column grid.
- Supplied Quantity displayed as: `{package_count} x {package_volume} {package_uom} {package_type}` — e.g. "1 x 1000 ml Bottles".
- Date of Despatch shows "Not yet dispatched" if blank.
- Test parameters displayed as a read-only table matching the PDF layout.
- Audit log section at the bottom (same component as PI/PL/CI detail pages).

**Action button visibility rules:**

| Status | Maker sees | Checker sees |
| --- | --- | --- |
| DRAFT | Submit | — |
| SUBMITTED | — | Approve, Reject, Rework |
| REWORK | Submit | — |
| APPROVED | — | — |
| REJECTED | Edit (returns to DRAFT) | — |

**Wireframe — COA Detail Page**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Certificate of Analysis                                               │
│ COA-2026-0001          [APPROVED]                    [Download PDF]     │
├──────────────────────────────────────────────────────────────────────────┤
│ Product          Chloroform          Grade          Technical           │
│ Customer         AGC                                                    │
│ Batch No.        CFM/25/12/0733      Supplied Qty   1 x 1000 ml Bottles │
│ Date of Mfg.     22 Dec 2025         Date of Retest 21 Dec 2026         │
│ Date of Desp.    Not yet dispatched                                     │
│ Sampling         25 Dec 2025 18:00   Analysis       25 Dec 2025 19:25   │
│ Analyst          [Name]              QC Incharge    [Name]              │
├──────────────────────────────────────────────────────────────────────────┤
│  No  Characteristic           Unit   Spec              Result  Method   │
│  ──────────────────────────────────────────────────────────────────────  │
│  1   Appearance               —      Complies spec.    Complies ASTM…   │
│  2   Colour, Hazen, Max       Hazen  Max: 5            < 5.0    ASTM…   │
│  3   Purity, % by mass, Min   %      Min: 99.90        99.96    ASTM…   │
│  ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Audit Log                                                                │
│  26 Dec 2025 10:00  Maker User     Created (DRAFT)                      │
│  26 Dec 2025 11:00  Maker User     Submitted for approval               │
│  26 Dec 2025 12:00  Checker User   Approved                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 6 — PDF Generation

### FR-COA-13 — PDF Layout and Rules

The COA PDF mirrors the reference document layout. Generated in memory and streamed to the client — **never written to disk** (Rule #9).

**PDF structure (top to bottom):**

1. **Company header block** — logo top-right; company name (bold, large); CIN number; registered address, admin address, and factory address; phone numbers. This mirrors the exporter's Organisation record in the system.

2. **Page label** — "Page 1 of 1" top-right corner.

3. **Document title** — "Certificate of Analysis" (centered, bold, underlined).

4. **Header info block** — key–value pairs, left-aligned label with colon, right-aligned value:

   | Label | Value source |
   | --- | --- |
   | Name of the Product | `product_grade.product.name` |
   | Grade | `product_grade.grade` |
   | Name of the Customer | `customer.name` |
   | Batch No | `batch_number` |
   | Supplied Quantity | `{package_count} x {package_volume} {package_uom} {package_type}` e.g. "1 x 1000 ml Bottles" |
   | Date of Despatch | `date_of_despatch` formatted, or "XXXX" if blank |
   | Date of Manufacture | `date_of_manufacture` formatted DD.MM.YYYY |
   | Date of Retest | `date_of_retest` formatted DD.MM.YYYY |
   | Date and time of sampling | `date_time_of_sampling` formatted DD.MM.YYYY – HH:MM |
   | Date and time of analysis | `date_time_of_analysis` formatted DD.MM.YYYY – HH:MM |

5. **Test parameters table** — columns:

   | S. No | Characteristic | Unit | Specification (Minimum / Maximum or Description) | Results | Test Method |
   | --- | --- | --- | --- | --- | --- |

   - Header row: dark navy background, white text (same style as PI/PL/CI tables).
   - Specification column: for QUANTITATIVE rows, renders as two sub-columns "Minimum" and "Maximum" with a dash where not applicable. For QUALITATIVE rows, spans the full Specification width with the `spec_description` text.
   - Results column: `result_value` for QUANTITATIVE, `result_text` for QUALITATIVE.
   - Test Method column: `test_method_label`.
   - Alternating row shading for readability.

6. **Signature section** — three columns:
   - Left: Signature line + "Analyst" label + analyst name + "Date : DD.MM.YYYY"
   - Center: Company seal / logo image
   - Right: Signature line + "QC Incharge" label + QC incharge name + "Date : DD.MM.YYYY"
   - The date in the signature section is the date the COA was approved (or the current date if still DRAFT — for preview purposes).

7. **Footer** — uses the `footer_organisation` selected on the COA header. Prints: company name (bold), CIN, and all addresses (registered, admin, factory) stored against that organisation in the MDM. Thin top border separating footer from body. If an organisation holds both CONSIGNEE and EXPORTER tags it still appears once in the dropdown; its addresses are printed regardless of which tag caused the selection.

**PDF styling rules (consistent with existing documents):**
- Dark navy (`#1a2a5e` or matching existing documents) for table header rows — white text.
- No colour on data rows except alternating light-grey shading.
- Font: same font family as PI/PL/CI PDFs.
- Margins: same as existing PDFs.
- COA number printed in the document header area (e.g. below the "Certificate of Analysis" title).

---

## Validation Summary

| Rule | Detail |
| --- | --- |
| Product | Required; must be an active Product from master |
| Grade | Required; must be an active ProductGrade belonging to the selected Product |
| Customer | Required; must be an Organisation tagged CONSIGNEE or BUYER |
| Footer Company | Required; must be an Organisation tagged CONSIGNEE or EXPORTER (active only); deduplicated in dropdown if tagged as both |
| Batch Number | Required; free text; no uniqueness constraint |
| Package Count | Required; positive integer |
| Package Volume | Required; positive decimal |
| Package UOM | Required; active UOM from master |
| Package Type | Required; active TypeOfPackage from master |
| Date of Manufacture | Required |
| Date of Retest | Required; must be ≥ Date of Manufacture |
| Date of Despatch | Optional |
| Date & Time of Sampling | Required |
| Date & Time of Analysis | Required; must be ≥ Date & Time of Sampling |
| Analyst Name | Required |
| QC Incharge Name | Required |
| Test Parameters | At least 1 row required to submit |
| QUANTITATIVE row | At least one of Spec Min or Spec Max required; Result Value required |
| QUALITATIVE row | Spec Description required; Result Text required |
| Reject / Rework | Comment field must not be empty (Rule #7) |

---

## New Master Data Summary

Six new models are introduced by this feature (all in `apps/master_data/`):

| Model | Reference Data Tab | Key Fields |
| --- | --- | --- |
| `Product` | Products | name (unique), cas_number |
| `ProductGrade` | (managed via Products tab — Manage Grades) | product (FK→Product), grade (CharField); unique_together (product, grade) |
| `TestParameter` | Test Parameters | name, default_unit (FK→UOM) |
| `TestMethod` | Test Methods | code, description |
| `ProductTestTemplate` | (managed via Products tab — Manage Template per grade) | product_grade (1:1 FK→ProductGrade) |
| `ProductTestTemplateRow` | (managed via Products tab) | template FK, parameter_label, unit, spec fields, test_method_label |

`Product`, `ProductGrade`, `TestParameter`, and `TestMethod` follow the same soft-delete (`is_active`) pattern as all existing reference tables. `ProductTestTemplate` and `ProductTestTemplateRow` are hard-deletable (they are configuration, not historical records). All FK references from the COA model to these tables use `on_delete=PROTECT`.

---

## Testing Requirements

- Every model must have a factory in `apps/certificate_of_analysis/tests/factories.py` and `apps/master_data/tests/factories.py` (for Product, TestParameter, TestMethod, ProductTestTemplate, ProductTestTemplateRow).
- Minimum test coverage:
  - Happy-path create/submit/approve flow.
  - Permission denial for wrong roles.
  - QUALITATIVE and QUANTITATIVE row validation rules.
  - Date validation rules (retest ≥ manufacture; analysis ≥ sampling).
  - Template auto-populate: `GET /api/products/{id}/test-template/` returns correct rows; returns empty list when no template exists.
  - Template save: `PUT /api/products/{id}/test-template/` replaces rows; denied for Maker role.
  - COA creation with template rows: template rows are copied into COA, not linked; editing COA rows does not mutate the template.
  - PDF endpoint returns 200 with `application/pdf` content type.
- Run with `pytest --cov=apps/certificate_of_analysis --cov-report=term-missing`.
