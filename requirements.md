# Product Requirements Document — TradeDocs

**Version:** 1.5
**Status:** Active
**Last Updated:** 2026-03-19

> **v1.5 Change:** Discrepancy resolution pass. Additional Description removed from FR-14M.2 (not required). HSN Code made mandatory in FR-14M.8A and FR-14M validation rules. US-08 updated: HSN Code and UOM confirmed mandatory, Batch Details optional. US-13 removed: Disable action removed — DISABLED state is not part of FR-08.1 common workflow states. AD Code (Authorised Dealer Code) added to FR-05 Bank master.

> **v1.4 Change:** FR-14M wireframe alignment pass. 12 discrepancies resolved against validated wireframes_plci.html: PI Preview Card added to FR-14M.1; Incoterms/Payment Terms and FOB/Freight/Insurance/L/C Details relocated to Page 5 (FR-14M.8B); Drawee field removed entirely; Additional Description added to FR-14M.2 (subsequently removed in v1.5); UOM made mandatory in FR-14M.8A with dynamic Rate label rule; FR-14M.8B and FR-14M.10 extended with Payment & Terms and Break-up in USD sections; FR-14M.14 Document Detail tab layout added; Disable action updated to Any state.

> **v1.3 Change:** FR-14 (standalone Packing List) and FR-15 (5-step CI wizard from Approved PL) have been replaced by **FR-14M — Combined Packing List + Commercial Invoice**. The PL and CI are now created together in a single form flow with joint approval. There is no backward-compatible standalone PL path. All modifiedrequirement.md content has been merged into this file; modifiedrequirement.md is no longer authoritative.

---

## 1. Overview

**TradeDocs** is a platform designed for trading houses engaged in the import and export of commodities and goods. The platform streamlines the creation, review, approval, and management of critical trade documentation, reducing manual errors, ensuring regulatory compliance, and accelerating shipment cycles.

The platform will produce the following trade documents:
- **Proforma Invoice** — a preliminary invoice sent to buyers before shipment to confirm terms
- **Packing List** — a detailed record of shipment contents used by customs and logistics teams
- **Commercial Invoice** — the primary document used for customs clearance and payment

Beyond document generation, TradeDocs will provide:
- **Approval workflows** (maker–checker model) to ensure document accuracy before dispatch
- **Master data management** for organisations, banks, ports, incoterms, and more
- **Reporting** capabilities for audit trails and operational visibility

---

## 2. Goals & Non-Goals

### Goals
- Provide a centralised, error-free document generation system for export trade documents (commercial invoice, proforma invoice, packing list)
- Maintain structured 
- Mter data to ensure consistency and reuse across all documents
- Enforce a maker–checker 
-  workflow before any document is finalised
- Allow Company Admins to manage users, roles, and organisation-level master data
- Enable reporting for document history, approval status, and audit trails

### Non-Goals
- A native mobile application (iOS/Android) is out of scope for this release
- Customs filing or direct integration with government trade portals (e.g., DGFT, ICEGATE) is out of scope for v1
- Automated freight booking or logistics coordination is out of scope
- Financial accounting or ERP integration is out of scope for v1

---

## 3. Background & Context

Trading houses that handle multi-commodity exports are required to produce highly accurate, consistently formatted trade documents for every shipment. Errors in documents such as the commercial invoice or packing list can lead to customs delays, demurrage charges, payment holds under Letters of Credit (LC), and legal non-compliance.

Currently, most mid-sized trading houses manage these documents manually using Excel templates or Word files, leading to:
- Inconsistent formatting across shipments and personnel
- High risk of data entry errors (incorrect HS codes, wrong quantities, mismatched values)
- No formal approval trail, creating audit and compliance risk
- Difficulty scaling as shipment volumes grow

TradeDocs addresses these pain points by providing a structured, role-governed, data-driven document generation platform tailored to the needs of export-focused trading houses.

---

## 4. Stakeholders

| Role | Responsibility |
| --- | --- |
| **Company Admin** | Has full permissions within their organisation. Can manage master data (organisations, \nks, ports, terms, etc.). Can create and manage users and assign roles. Inherits all Maker and Checker permissions. |
| **Maker** | Creates trade documents (proforma invoice, commercial invoice, packing list) and saves drafts. Can submit documents for approval. Can search and view all documents. Cannot edit a document once it has been approved. |
| **Checker** | Reviews documents submitted for approval. Can approve or reject with comments. Rejected documents are returned to the Maker for revision and resubmission.Can manage master data (organisations, banks, ports, terms, etc.). |

---

## 5. Functional Requirements

### 5.1 Platform

- **FR-01** TradeDocs is a single-organisation platform. All users operate within the same organisation. All data is shared across the Company Admin, Checker, and Maker roles within that organisation.

---

### 5.2 Home Page & Navigation

- **FR-02** The home/landing page (pre-login) shall display a product feature slider and a login panel. The login panel shall include:
  - Username field
  - Password field
  - Login button
  - Forgot Password link

- **FR-03** Upon successful login, the application shall display a persistent left-hand navigation sidebar. The following modules shall appear based on role:

| Sidebar Item | Visible To |
| --- | --- |
| Proforma Invoice | All roles |
| Packing List | All roles |
| Commercial Invoice | All roles |
| Master Data | Company Admin, Checker |
| Organisation Management | Company Admin |
| User Management | Company Admin |
| Reports | Checker, Company Admin |

---
### 5.9 User Management

- **FR-10** The Company Admin may invite, deactivate, and manage users. The Company Admin may assign or change the role of a user (Maker / Checker).
- **FR-12** Deleting an organisation is not permitted. 
---
- 
### 5.3 Master Data — Organisation

- **FR-04** Company Admins or checker shall be able to create and manage organisation records. Each organisation record comprises four sub-sections described below.

#### FR-04.1 General Information

| Field | Required | Notes |
| --- | --- | --- |
| Organisation Name | Yes | Must be unique within the system |
| IEC Code | Yes (when tagged as Exporter) | Importer–Exporter Code issued by DGFT; 10-character alphanumeric; must be unique within the system |

#### FR-04.2 Tax Codes *(one or more)*

Each organisation may have one or more tax code entries. A Tax Type and a Tax Code must always be saved together.

| Field | Required | Notes |
| --- | --- | --- |
| Tax Type | Yes (if Tax Code is present) | Free text label (e.g., GSTIN, PAN, VAT) |
| Tax Code | Yes (if Tax Type is present) | Alphanumeric; format validated by Tax Type (see below) |

**Tax Code format validation by Tax Type:**

| Tax Type | Validation |
| --- | --- |
| GST or GSTIN | Length: exactly 15 characters. Example format: `22AAAAA0000A1Z5`. Regex: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`. Checksum: official GSTIN algorithm (36-character set `0–9A–Z`, weighted sum mod 36). |
| PAN | Length: exactly 10 characters. Regex: `^[A-Z]{3}[PCHHFATBLJGE]{1}[A-Z]{1}[0-9]{4}[A-Z]{1}$`. |
| All other types | No format validation; stored as entered. |

#### FR-04.3 Addresses *(one or more; at least one required)*

| Field | Required | Notes |
| --- | --- | --- |
| Address Type | Yes | Must be one of: **Registered**, **Factory**, **Office** |
| Address Line 1 | Yes | — |
| Address Line 2 | No | — |
| City | Yes | — |
| State / Province | No | — |
| PIN / ZIP Code | No | — |
| Country | Yes | Dropdown from Countries master |
| Email Address | Yes | Must be a valid email format (RFC 5322) |
| Contact Name | Yes | Point of contact for this address |
| Phone Number | No | Stored as Country Code (dropdown) + Number; validated using a standard phone number library |

Contact details (email, phone, contact name) are stored per address and are **not** held separately at the organisation level. When a Maker selects an organisation on a document, they then select which of that organisation's addresses to use. If the organisation has only one address, it is selected automatically. If it has more than one, the Maker must explicitly choose.

#### FR-04.4 Document Role Tags *(multi-select)*

Determines where the organisation appears in document dropdowns. At least one tag must be selected; an organisation with no tags will not appear in any document dropdown.

| Tag | Dropdown it populates |
| --- | --- |
| Exporter | Exporter field on all document creation forms |
| Consignee | Consignee field on all document creation forms |
| Buyer | Buyer field on all document creation forms |
| Notify Party | Notify Party field on the Packing List creation form |

A single organisation may hold multiple tags simultaneously.

---

### 5.4 Master Data — Bank Details

- **FR-05 – Bank Account Master**
Company Admins shall be able to create and manage bank account records within the master data. Each bank account record shall include the following fields:

**Core Fields**
- **Exporter Organisation** – Required. Dropdown from Organisations tagged as **Exporter**. A bank account always belongs to one exporter organisation.
- **Account Nickname** – A short internal label to identify the account (e.g., "USD Operating Account", "AED Payroll Account")
- **Beneficiary Name** – The name of the account holder as it appears on wire transfer instructions and printed documents
- **Bank Name**
- **Branch Name** – The specific branch name (e.g., "Commercial Client Group")
- **Bank Country** – Dropdown from the country master
- **Branch Address** – Optional; full postal address of the branch
- **Account Number**
- **Account Type** – Dropdown: Current / Savings / Checking
- **Currency of Account** – Dropdown from the currency master

**Routing & Identification Codes**
- **SWIFT / BIC Code** – Optional; required for international wire transfers
- **IBAN** – Optional; required for transfers within Europe and parts of the Middle East
- **IFSC / Routing Number / Sort Code** – Optional; region-specific national routing code (India: IFSC, USA: ACH Routing Number, UK: Sort Code)
- Attachment of cancelled cheque optional

**Intermediary Institution** *(Optional — used when the receiving bank requires a correspondent bank for a specific currency, e.g., USD)*
- **Intermediary Bank Name** – Name of the correspondent/intermediary bank (e.g., "THE BANK OF SBI NEW YORK")
- **Intermediary Account Number** – Account number at the intermediary bank
- **Intermediary SWIFT Code** – SWIFT/BIC of the intermediary bank
- **Intermediary Routing Currency** – The currency for which this intermediary routing applies (e.g., USD); dropdown from the currency master

If any intermediary field is entered, all four intermediary fields become required. The intermediary block prints on the document PDF only when it is configured.

---

### 5.5 Master Data — Reference & Lookup Data

- **FR-06** The following reference data shall be maintainable by the Company Admin or checker

  | Reference Entity | Fields |
  | --- | --- |
  | Payment Terms | Term Name, Description |
  | Countries | Country Name, ISO 3166-1 Alpha-2 Code, ISO 3166-1 Alpha-3 Code |
  | Incoterms | Code (e.g., FOB, CIF, EXW), Full Name, Description |
  | Units of Measurement (UOM) | Unit Name, Abbreviation (e.g., MT, KG, PCS, CBM) |
  | Ports | Port Name, Port Code (UN/LOCODE), Country |
  | Locations | Location Name, Country |
  | Pre-Carriage By | Carrier / Mode Name (e.g., Truck, Rail, Feeder Vessel) |

---

### 5.6 Master Data — Terms & Conditions Templates

- **FR-07** Company Admins shall be able to create rich-text Terms & Conditions templates. Each template shall include:
  - Template Name
  - Organisation (multi-select — the organisations this template is associated with)
  - Rich-text body supporting the following formatting options:
  - Bold
  - Italic
  - Underline
  - Bullet List
  - Numbered List
  - Hyperlink
  - Clear Formatting

  Templates shall be selectable when generating trade documents to auto-populate the T&C section.

---

### 5.7 Approval Workflow — Platform-Wide Rules

- **FR-08** All three document types (Proforma Invoice, Packing List, Commercial Invoice) share the same core maker–checker approval workflow. All workflow state definitions, rules, and PDF generation behaviour are defined exclusively in this section and apply universally. Document sections (FR-09, FR-14, FR-15) contain only the state machine diagram and role-based actions table specific to each document.

#### FR-08.1 Common Workflow States

All state definitions are authoritative here. No document section defines or redefines any state.

| State | Applicable To | Meaning |
| --- | --- | --- |
| **Draft** | All documents | Created by Maker; editable; can be submitted for approval or deleted. |
| **Pending Approval** | All documents | Submitted by Maker for Checker or Company Admin review; locked for editing by all roles. |
| **Approved** | All documents | Finalised by Checker or Company Admin; fully read-only for all roles. The final clean PDF is available for download. |
| **Rework** | All documents | Rejected by Checker or Company Admin with mandatory comments; returned to Maker for revision and resubmission. All other documents label it **Rework**. |
| **Permanently Rejected** | All documents | Terminal state. A Checker or Company Admin may move any document to Permanently Rejected at any point. No further submissions, edits, approvals, or downloads are possible. **Cascading rule:** Permanently Rejecting a Proforma Invoice automatically moves all Packing Lists linked to it, and all Commercial Invoices linked to those Packing Lists, to Permanently Rejected. Permanently Rejecting a Packing List automatically moves all Commercial Invoices linked to it to Permanently Rejected. A mandatory comment is required; the comment dialog must display the names of all downstream documents that will be affected before the user confirms. |

#### FR-08.2 Common Workflow Rules

- A **Maker** may save a document as Draft and submit it for Pending Approval when ready.
- A **Checker** or **Company Admin** may Approve or Reject/Rework a document in Pending Approval state.
- A Checker cannot approve a document that is in Rework state directly. The Maker must revise and resubmit (moving it back to Pending Approval) before the Checker can act.
- Once a document reaches **Approved** status, it becomes fully read-only for all roles including the Maker.
- If there is more than one Maker in an organisation, a Rejected/Rework document is visible to all Makers; the original author's name is tagged on the document.
- All state transitions are logged with user identity, timestamp, and comments (if any) — retained for a minimum of 7 years.
- **Mandatory comments policy (platform-wide):** A comment is required whenever any document moves into aRework, or **Permanently Rejected**  state. The system must block the action if the comment field is empty.

#### FR-08.3 PDF Generation Rules (Platform-Wide)

| Document State | PDF Availability | Visual Indicator |
| --- | --- | --- |
| Draft | Available to Maker, Checker, and Company Admin | Diagonal **"DRAFT"** watermark across all pages |
| Pending Approval | Available to Maker, Checker, and Company Admin | Diagonal **"DRAFT"** watermark across all pages |
| Rework | Available to Maker, Checker, and Company Admin | Diagonal **"DRAFT"** watermark across all pages |
| Approved | Available to all authorised roles | No watermark — clean final output |

> **Note:** The combined Packing List + Commercial Invoice document has role-specific PDF download restrictions. See FR-14M.13 (Watermark Rules).

#### FR-08.4 Signed Copy Upload

Once a document reaches **Approved** status, the system shall allow any authorised user to upload and store a signed or stamped scanned copy of the document against its record.

---

### 5.8 Document Generation — Proforma Invoice

- **FR-09** A Maker shall be able to create, edit, and manage Proforma Invoices. The document is titled **"PROFORMA INVOICE CUM SALES CONTRACT"** on the generated PDF.

#### FR-09.1 Creation — Invoice Header

When creating a new Proforma Invoice, the Maker fills in the following header fields. The invoice is created first; line items are added after creation.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Exporter | Dropdown | Yes | Organisations tagged as **Exporter** |
| Consignee | Dropdown | Yes | Organisations tagged as **Consignee** |
| Buyer (if other than Consignee) | Dropdown | No | Organisations tagged as **Buyer**; the Maker explicitly selects a Buyer-tagged organisation; it is not auto-derived from the Consignee |
| Proforma Invoice No | Text (read-only) | — | Auto-generated by the system on save. Format: PI-YYYY-NNNN (e.g., PI-2026-0001). Zero-padded 4-digit sequence, unique within the system. |
| Proforma Invoice Date | Date | No | Defaults to today's date[AI01-Editable to user] |
| Buyer Order No | Free text | No | Buyer's purchase order reference number |
| Buyer Order Date | Date | No | Date of the buyer's purchase order |
| Other References | Free text (multi-line) | No | Any additional references or notes |
| Country of Origin of Goods | Dropdown | No | **Countries** master; the country where goods are produced |
| Country of Final Destination | Dropdown | No | **Countries** master; the ultimate delivery country |

#### FR-09.2 Creation — Shipping & Logistics

The complete table below has to come from master data:
| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Pre-Carriage By | Dropdown | No | **Pre-Carriage By** master (e.g., Truck, Rail). |
| Place of Receipt by Pre-Carrier | Dropdown | No | Locations,Location Name, Country   master |
| Vessel / Flight No | Free text | No | Name or number of the vessel or flight |
| Port of Loading | Dropdown | No | **Ports** master |
| Port of Discharge | Dropdown | No | **Ports** master |
| Final Destination | Dropdown | No | Location Name, Country   master |
| Payment Terms | Dropdown |  | Term Name |
| Incoterms | Dropdown |  | Code, Description |
#### FR-09.5 Line Items (added after header creation)

Line items are added on the document edit/detail page after the header has been saved. Each line item represents one commodity or product in the shipment.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| HSN Code | Free text | No | Harmonized System Nomenclature code for the commodity.\n- Regex: `^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?$`\n |
| Item Code | Free text | No | Internal product / item code |
| Description of Goods | Free text | Yes | Full description of the commodity |
| Quantity | Number (3 dp) | Yes | Quantity of goods |
| UOM | Dropdown | No | **Units of Measurement** master (e.g., MT, KG, PCS); UOM is selectable per line item. From master data. |
| Rate (USD/[UOM]) | Number (2 dp) | Yes | Unit price in USD; the label is dynamic and reflects the selected UOM — e.g., "Rate (USD/MT)" if UOM is MT, "Rate (USD/Litre)" if UOM is Litre |
| Amount (USD) | Calculated (read-only) | — | Auto-calculated: Quantity × Rate |
The line items table displays a **summary row** at the bottom showing:
- Total Quantity — sum of all line item quantities
- Total Amount (USD) — sum of all line item amounts

The Maker may add one or more **additional charge rows** below the line items summary. Each row has two fields: a free-text **Description** (e.g., "Inspection Fees", "Documentation Charges") and an **Amount (USD)**. Rows can be added and removed at any time while the document is in an editable state. There is no fixed label — the Maker names each charge as appropriate.

Below this we will have the row for Grand Total Amount

- Grand Total in Words — total amount written out in English (e.g., "One Hundred Twenty Thousand Dollars Only")

#### FR-09.3 Creation — Payment & Terms

The complete table below has to come from master data:
| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Payment Terms | Dropdown | Yes | **Payment Terms** master |
| Bank | Dropdown | No | **Bank** master; displayed as "Bank Name – Beneficiary Name" |
| Incoterms | Dropdown | Yes | **Incoterms** master; displayed as "Code – Description" |
| Validity for Acceptance | Date | No | Last date the buyer may accept this proforma |
| Validity for Shipment | Date | No | Last date by which shipment must occur |
| Partial Shipment | Select | No | Allowed / Not Allowed |
| Transshipment | Select | No | Allowed / Not Allowed |

#### FR-09.4 Creation — Terms & Conditions

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| T&C Template | Dropdown | No | **Terms & Conditions Templates** master |
| Terms & Conditions Content | Rich text (read-only preview) | No | Auto-loaded from selected template; stored with the document |

#### 
#### FR-09.6 PDF Output Layout

The generated PDF follows this structure:

1. **Exporter name** — centred, large, bold (from Organisation master)
2. **Document title** — "PROFORMA INVOICE CUM SALES CONTRACT"
3. **Main information table** (8 rows):
  - Row 1–3: Exporter details | Invoice No & Date / Buyer Order No & Date / Other References
  - Row 4–6: Consignee details | Buyer if other than Consignee / Country of Origin / Country of Final Destination
  - Row 7: Pre-Carriage By | Place of Receipt by Pre-Carrier | Vessel/Flight No | Incoterms | Payment Terms
  - Row 8: Port of Loading | Port of Discharge | Final Destination
4. **Line items table**: Sr. | HSN Code | Item Code | Description of Goods | Qty | UOM | Rate (USD/UOM) | Amount (USD)
5. **Total amount**: "Amount Chargeable in: USD" | Total | $amount
6. **Amount in words**
7. **Validity & terms block**: Validity for Acceptance | Validity for Shipment | Partial Shipment | Transshipment
8. **MT103 payment instruction** (static text): *"Request your bank to send MT 103 Message to our bank and send us copy of this message to trace & claim the payment from our bank."*
9. **Declaration** (static text): *"We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."*
10. **Beneficiary / Bank details** — printed as a labelled block:
  - BENEFICIARY NAME: [Beneficiary Name]
  - BANK NAME: [Bank Name]
  - BRANCH NAME: [Branch Name]
  - BRANCH ADDRESS: [Branch Address]
  - A/C NO.: [Account Number]
  - IFSC CODE: [IFSC / Routing Number] *(printed only if present)*
  - SWIFT CODE: [SWIFT Code]
  - *(If an intermediary institution is configured on the bank record, the following block is appended):*
  - Intermediary Institution Routing for Currency [Intermediary Routing Currency]
  - A/C No.: [Intermediary Account Number]
  - [Intermediary Bank Name]
  - SWIFT Code: [Intermediary SWIFT Code]
11. **Terms & Conditions** (on a new page, if present)
12. **Footer** (every page): "This is a computer-generated document. Signature is not required."

# FR-09.7 Invoice Amount — Incoterms Logic
---
## What this section covers
When a Maker selects an Incoterm on the Proforma Invoice, the system needs to show the right cost fields and calculate the correct Invoice Total. Different Incoterms mean different costs are borne by the seller — so the form and PDF should only show what the seller is actually charging.
---
## FR-09.7.1 How Incoterm selection works
The Maker picks an Incoterm from the existing dropdown on the invoice form (already defined in FR-09.3). This choice controls everything in this section — which fields appear, and what gets added to the Invoice Total.
> The selection is made fresh on each invoice. There is no default.
---
## FR-09.7.2 The cost fields
Below the Grand Total row (from FR-09.5), the form shows a **Cost Breakdown** section with these fields:
| Field | Editable? | Notes |
| --- | --- | --- |
| FOB Value | Read-only | Always equals the Grand Total Amount from FR-09.5 |
| Freight | Maker enters | The freight charge the seller is paying |
| Insurance Amount | Maker enters | The insurance premium the seller is paying |
| Import Duty / Taxes | Maker enters | Only appears for DDP |
| Destination Charges | Maker enters | Only appears for DPU and DDP |
| **Invoice Total Value** | Read-only | Sum of all the fields above that are visible |
The **Amount in Words** line below the Invoice Total should update to reflect the Invoice Total Value (not the Grand Total Amount).
---
## FR-09.7.3 Which fields appear for each Incoterm
Fields the buyer pays should be **hidden completely** — no greyed-out rows, no placeholders.
| Incoterm | FOB Value | Freight | Insurance | Import Duty | Destination Charges |
| --- | --- | --- | --- | --- | --- |
| EXW | — | — | — | — | — |
| FCA | ✓ | — | — | — | — |
| FOB | ✓ | — | — | — | — |
| CFR | ✓ | ✓ | — | — | — |
| CIF | ✓ | ✓ | ✓ | — | — |
| CPT | ✓ | ✓ | — | — | — |
| CIP | ✓ | ✓ | ✓ | — | — |
| DAP | ✓ | ✓ | ✓ | — | — |
| DPU | ✓ | ✓ | ✓ | — | ✓ |
| DDP | ✓ | ✓ | ✓ | ✓ | ✓ |
**✓ = shown and editable    — = hidden**
Two things worth noting:
- **EXW** — no cost breakdown fields appear at all. Invoice Total = Grand Total Amount.
- **CIF vs CIP** — both show the Insurance field, but CIP requires broader (all-risk) coverage. Add a small tooltip on the Insurance field for these two terms to remind the Maker.
---
## FR-09.7.4 How Invoice Total is calculated
Invoice Total = FOB Value + every visible field the Maker has filled in.
It recalculates automatically as the Maker types. No save needed to see the updated total.
---
## FR-09.7.5 What happens when the Maker changes the Incoterm
- The cost breakdown section re-renders immediately.
- Any fields that are no longer relevant get hidden and their values are cleared.
- The Maker is not shown a warning — changing the Incoterm is treated as intentional.
---
## FR-09.7.6 How the form should look
```javascript
────────────────────────────────────────────────
  [Line items table]

  Total Amount (USD)              $xx,xxx.xx
  Bank Charges / other rows       $xx,xxx.xx
  Grand Total Amount              $xx,xxx.xx
────────────────────────────────────────────────
  COST BREAKDOWN  (Incoterm: CIF)

  FOB Value                       $xx,xxx.xx
  Freight                         $xx,xxx.xx
  Insurance Amount                $xx,xxx.xx
────────────────────────────────────────────────
  Invoice Total Value             $xx,xxx.xx
────────────────────────────────────────────────
  Amount in Words: Twelve Thousand Dollars Only
```
Only the fields relevant to the selected Incoterm appear in the Cost Breakdown block. The Incoterm code is shown in the section header so it's clear which term is driving the layout.
---
## FR-09.7.7 PDF output
The PDF follows the same rules — only seller-borne fields are printed. If a visible field has been left at zero, it still prints as `$0.00` (so the document looks complete).
```javascript
  Grand Total Amount              $xx,xxx.xx
  ──────────────────────────────────────────
  COST BREAKDOWN (CIF)
  FOB Value                       $xx,xxx.xx
  Freight                         $xx,xxx.xx
  Insurance Amount                $xx,xxx.xx
  ──────────────────────────────────────────
  Invoice Total Value             $xx,xxx.xx

  Amount in Words: Twelve Thousand Dollars Only
```
---
## FR-09.7.8 Validation
These checks run when the Maker tries to save the invoice:
- **Freight, Insurance, Import Duty, Destination Charges** — if the field is visible, it cannot be left blank. The Maker must enter a value (even if it's 0).
  - Error message: *"[Field name] is required for [Incoterm]. Enter 0 if not applicable."*
- **Invoice Total Value** must always be equal to or greater than the Grand Total Amount.
  - Error message: *"Invoice Total cannot be less than the Grand Total Amount."*
# FR-09.6 PDF Output Layout
The generated PDF follows this structure:
---
**1. Exporter name** Centred, large, bold — pulled from the Organisation master.
---
**2. Document title** "PROFORMA INVOICE CUM SALES CONTRACT"
---
**3. Main information table (8 rows)**
- **Rows 1–3:** Exporter details | Invoice No & Date / Buyer Order No & Date / Other References
- **Rows 4–6:** Consignee details | Buyer if other than Consignee / Country of Origin / Country of Final Destination
- **Row 7:** Pre-Carriage By | Place of Receipt by Pre-Carrier | Vessel/Flight No | Incoterms | Payment Terms
- **Row 8:** Port of Loading | Port of Discharge | Final Destination
---
**4. Line items table**
Sr. | HSN Code | Item Code | Description of Goods | Qty | UOM | Rate (USD/UOM) | Amount (USD)
---
**5. Amount block**
```javascript
Amount Chargeable in: USD
─────────────────────────────────────────────────────
  Total Amount (USD)                     $xx,xxx.xx
  [Additional charge rows, if any]       $xx,xxx.xx  ← free-text description + amount per row
  Grand Total Amount                     $xx,xxx.xx
─────────────────────────────────────────────────────
  COST BREAKDOWN  ([Incoterm code])

  FOB Value                              $xx,xxx.xx  ← hidden for EXW
  Freight                                $xx,xxx.xx  ← only if seller-borne
  Insurance Amount                       $xx,xxx.xx  ← only if seller-borne
  Import Duty / Taxes                    $xx,xxx.xx  ← DDP only
  Destination Charges                    $xx,xxx.xx  ← DPU and DDP only
─────────────────────────────────────────────────────
  Invoice Total Value                    $xx,xxx.xx
─────────────────────────────────────────────────────
```
Which cost breakdown fields appear depends on the Incoterm selected — see FR-09.7.3 for the full visibility rules.
- Fields the buyer pays are **not printed** at all.
- If a seller-borne field has been entered as 0, it **is still printed** as `$0.00`.
- The Incoterm code is shown in the Cost Breakdown header, e.g. `COST BREAKDOWN (CIF)`.
- For **EXW**, no cost breakdown fields are printed. Invoice Total Value = Grand Total Amount.
---
**6. Amount in words**
Invoice Total Value written out in English — e.g. *"One Hundred Twenty Thousand Dollars Only"*
> This reflects the Invoice Total Value (after Incoterm charges), not the Grand Total Amount.
---
**7. Validity & terms block**
Validity for Acceptance | Validity for Shipment | Partial Shipment | Transshipment
---
**8. MT103 payment instruction** Static text: *"Request your bank to send MT 103 Message to our bank and send us copy of this message to trace & claim the payment from our bank."*
---
**9. Declaration** Static text: *"We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."*
---
**10. Beneficiary / Bank details** — printed as a labelled block:
- BENEFICIARY NAME: [Beneficiary Name]
- BANK NAME: [Bank Name]
- BRANCH NAME: [Branch Name]
- BRANCH ADDRESS: [Branch Address]
- A/C NO.: [Account Number]
- IFSC CODE: [IFSC / Routing Number] *(printed only if present)*
- SWIFT CODE: [SWIFT Code]
- *(If an intermediary institution is configured on the bank record, the following block is appended):*
- Intermediary Institution Routing for Currency [Intermediary Routing Currency]
- A/C No.: [Intermediary Account Number]
- [Intermediary Bank Name]
- SWIFT Code: [Intermediary SWIFT Code]
---
**11. Terms & Conditions** Printed on a new page, if a T&C template has been selected.
---
**12. Footer (every page)** *"This is a computer-generated document. Signature is not required."*
---
## FR-09.7.9 Edge cases to be aware of
| Situation | What should happen |
| --- | --- |
| Maker hasn't selected an Incoterm yet | Cost breakdown section doesn't appear. Invoice Total = Grand Total Amount. |
| Maker changes Incoterm mid-way through filling in charges | Fields re-render, previously entered values in now-hidden fields are cleared. |
| EXW is selected | No cost breakdown fields shown. Invoice Total = Grand Total Amount. Section header still shows "COST BREAKDOWN (EXW)" for clarity. |
| A visible field is entered as 0 | That's fine — it's accepted and printed on the PDF as $0.00. |
| Grand Total Amount is 0 | FOB Value = 0, Invoice Total = 0. No error at this point. |
---

### 5.8.1 Master Data → Proforma Invoice Field Mapping

The table below shows exactly which master data entity populates each field on the Proforma Invoice form and PDF.

| Proforma Invoice Field | Master Data Entity | Master Data Fields Used |
| --- | --- | --- |
| Exporter | Organisation (tagged: Exporter) | Address Line 1, Address Line 2 – Optional, City, State / Province, PIN / ZIP Code, Country\nOn next line Email Address,Phone Number\n |
| Consignee | Organisation (tagged: Consignee) | Address Line 1, Address Line 2 – Optional, City, State / Province, PIN / ZIP Code, Country\nOn next line Email Address,Phone Number |
| Buyer if other than Consignee | Organisation (tagged: Buyer) | Address Line 1, Address Line 2 – Optional, City, State / Province, PIN / ZIP Code, Country\nOn next line Email Address,Phone Number\n explicitly selected by Maker from Buyer-tagged organisation list\n |
| Country of Origin of Goods | Countries | Country Name |
| Country of Final Destination | Countries | Country Name |
| Pre-Carriage By | Pre-Carriage By | Name |
| Place of Receipt | Locations | Location Name, Country   master |
| Place of Receipt by Pre-Carrier | Locations | Location Name, Country   master |
| Port of Loading | Ports | Port Name, Country |
| Port of Discharge | Ports | Port Name, Country |
| Country of Supply | Locations | Country   master |
| Final Destination | Final Destinations | Location Name, Country   master |
| Payment Terms | Payment Terms | Term Name |
| Incoterms | Incoterms | Code, Description |
| Bank | Bank | Beneficiary Name, Bank Name, Branch Name, Branch Address, Account Number, IFSC Code, SWIFT Code; and if configured: Intermediary Bank Name, Intermediary Account Number, Intermediary SWIFT Code, Intermediary Routing Currency |
| Terms & Conditions | T&C Templates | Template Name, Content (HTML) |
| *(All line items)* | No master data — entered manually per document | — |

### 5.11 Document Generation — Combined Packing List + Commercial Invoice

> **Changed in v1.3:** FR-14 (standalone Packing List) and FR-15 (5-step CI wizard from Approved PL) are replaced by this combined flow. The PL and CI are created together and share a joint approval workflow. There is no backward-compatible standalone PL path.

- **FR-14M** A Maker shall be able to create, edit, and manage a combined Packing List + Commercial Invoice. Both documents are generated simultaneously from a single creation form. On save, the system generates both a PL number and a CI number. The Packing List PDF section is titled **"Packing List/Weight Note"**; the Commercial Invoice PDF section is titled **"COMMERCIAL INVOICE"**.

---

#### FR-14M.1 Entry Point

The Maker begins the combined creation flow by selecting:
1. **Consignee** — Dropdown of organisations tagged as **Consignee**
2. **Proforma Invoice** — Dropdown of all **Approved** Proforma Invoices belonging to the selected Consignee. The dropdown is searchable and the most recently approved PI appears first.

On selecting the Proforma Invoice, all overlapping fields (FR-14M.3 through FR-14M.6) are auto-populated from the PI and become editable by the Maker.

**PI Preview Card:** Once a Proforma Invoice is selected, a read-only preview card is displayed so the Maker can confirm they have selected the correct PI before proceeding. The preview shows the PI's line items:

| Column | Source |
| --- | --- |
| Item Code | PI line item |
| Description of Goods | PI line item |
| HSN Code | PI line item |
| No. & Kind of Packages | PI line item |
| Quantity | PI line item |

---

#### FR-14M.3 Document Header

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Proforma Invoice | Dropdown | Yes | Select from Approved PIs for the selected Consignee. Stored as the authoritative link on both the PL and CI records. |
| Exporter | Dropdown | Yes | Auto-populated from the selected PI; editable. Organisations tagged as **Exporter**. If the exporter has registered, office, and factory addresses, all are shown. |
| Consignee | Dropdown | Yes | Auto-populated from the selected PI; editable. Organisations tagged as **Consignee**. |
| Buyer (if different from Consignee) | Dropdown | No | Auto-populated from the selected PI if set; editable. Organisations tagged as **Buyer**. |
| Notify Party | Dropdown | No | Organisations tagged as **Notify Party** in the Organisation master. |
| Packing List No | Text (read-only) | — | Auto-generated by the system on first save. Format: PL-YYYY-NNNN. |
| Commercial Invoice No | Text (read-only) | — | Auto-generated by the system on first save. Format: CI-YYYY-NNNN. |
| Packing List Date | Date | No | Date of the packing list. Defaults to today; editable by Maker. |
| Commercial Invoice Date | Date | No | Date of the commercial invoice. Defaults to today; editable by Maker. |

---

#### FR-14M.3 Shipping & Logistics

All fields auto-populated from the linked Proforma Invoice on creation and remain editable by the Maker. These fields print on both the PL PDF and CI PDF.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Pre-Carriage By | Dropdown | No | Auto-populated from PI; editable. **Pre-Carriage By** master. |
| Place of Receipt | Dropdown | No | Auto-populated from PI; editable. Locations master (Location Name, Country). |
| Place of Receipt by Pre-Carrier | Dropdown | No | Auto-populated from PI; editable. Locations master (Location Name, Country). |
| Vessel / Flight No | Free text | No | Auto-populated from PI; editable. Vessel or flight identifier. |
| Port of Loading | Dropdown | No | Auto-populated from PI; editable. **Ports** master. |
| Port of Discharge | Dropdown | No | Auto-populated from PI; editable. **Ports** master. |
| Final Destination | Dropdown | No | Auto-populated from PI; editable. Locations master (Location Name, Country). |

---

#### FR-14M.5 Payment & Terms

Both fields auto-populated from the linked PI; remain editable. Print on both PL PDF and CI PDF.

> **Page placement:** These fields appear on **Page 5 — Final Rates** of the creation wizard (below the rates table), not on the header page. See FR-14M.8B for the full Final Rates page definition.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Incoterms | Dropdown | No | Auto-populated from PI; editable. **Incoterms** master. |
| Payment Terms | Dropdown | No | Auto-populated from PI; editable. **Payment Terms** master. |

---

#### FR-14M.6 Countries

Both fields auto-populated from the linked PI; remain editable. Print on both PL PDF and CI PDF.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Country of Origin of Goods | Dropdown | No | Auto-populated from PI; editable. **Countries** master. |
| Country of Final Destination | Dropdown | No | Auto-populated from PI; editable. **Countries** master. |

---

#### FR-14M.9 Bank Details (for Commercial Invoice)

The Bank field is entered on **Page 2 — Header & Details**. The selected bank's full details print on the CI PDF.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Bank | Dropdown | Yes | **Bank** master; displayed as "Bank Name – Beneficiary Name". Full bank details (Branch, Account No., IFSC, SWIFT) print on the CI PDF. A read-only Bank Details preview card is shown after selection. |

> **Financial break-up fields (FOB Rate, Freight, Insurance, L/C Details)** are entered on **Page 5 — Final Rates** alongside the rates table. See FR-14M.8B.

---

#### FR-14M.2 Order References

All reference fields are optional. Each number/reference field has a paired date field.

| Field | Type | Notes |
| --- | --- | --- |
| PO Number | Free text | Purchase Order number |
| PO Date | Date | Date of the Purchase Order |
| LC Number | Free text | Letter of Credit number |
| LC Date | Date | Date of the Letter of Credit |
| BL Number | Free text | Bill of Lading number |
| BL Date | Date | Date of the Bill of Lading |
| Sales Order (SO) Number | Free text | Internal Sales Order number |
| SO Date | Date | Date of the Sales Order |
| Other References | Free text | Any additional reference |
| Other References Date | Date | Date for the other reference |
| Additional Description | Textarea | Optional free-text field for any supplementary document-level description. Printed in the right info panel on both the PL PDF and CI PDF. |

References that have a value print on **both** the PL PDF and CI PDF in the references block, formatted as: `Label No/Date: value / date`.

> **PDF label note:** The "Other References" field prints as **"Other Reference(s):"** on both the PL PDF and the CI PDF.

---

#### FR-14M.4 Containers

The combined document must have **at least one container** before it can be submitted. Each container must have at least one item.

**Per Container:**

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Container Reference | Free text | Yes | Container identification reference (e.g., CONT001) |
| Marks and Numbers | Free text | Yes | Shipping marks on packages |
| Container Tare Weight | Number (3 dp) | Yes | Weight of the empty container itself (e.g., ISO container tare weight as stamped on the container door) |
| Container Gross Weight | Calculated (read-only) | — | Auto-calculated: SUM(Item Gross Weight for all items in this container) + Container Tare Weight |
| Seal Number | Free text | Yes | Seal number on the container |

**Copy Container:** A Maker may **Copy Container** to duplicate a container and then modify the copy. When copying:
- All items are copied (rates are not copied here — they are entered in the Final Rates section)
- Container Tare Weight is pre-filled from the source container (Maker may adjust)
- Container Reference, Marks & Numbers, and Seal Number are left blank for the Maker to fill in

---

#### FR-14M.8A Items (per Container)

Each container must have **at least one item**. Items represent individual commodity lines within that container. **Rates are not entered here** — they are entered once per unique Item Code + UOM in the Final Rates section (FR-14M.8B) after all containers have been filled in.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| HSN Code | Free text | No | Harmonized System Nomenclature code. Regex: `^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?$` |
| Item Code | Free text | Yes | Internal product code; mandatory as it is the aggregation key for the Final Rates section and the Commercial Invoice |
| No & Kind of Packages | Free text | Yes | e.g., "10 Boxes", "5 Pallets" |
| Description of Goods | Textarea | Yes | Full commodity description |
| Batch Details | Free text | No | Batch or lot number for traceability |
| UOM | Dropdown | Yes | **Units of Measurement** master (e.g., MT, KG, PCS). Mandatory because UOM is the aggregation key for the Final Rates table; the Rate column header renders dynamically as "Rate (USD per [UOM])" (e.g., "Rate (USD per KG)"). |
| Quantity | Number (3 dp) | Yes | Quantity of goods in this container for this item |
| Net Weight | Number (3 dp) | Yes | Weight of the goods only, excluding all packaging |
| Inner Packing Weight | Number (3 dp) | Yes | Weight of the packaging material directly associated with this item (e.g., individual box, foam, wrapping) |
| Item Gross Weight | Calculated (read-only) | — | Auto-calculated: Net Weight (per unit) + Inner Packing Weight |

**Shipment-level weight calculations (derived from items and containers):**

| Calculated Field | Formula |
| --- | --- |
| Total Net Weight | SUM(Net Weight for all rows) |
| Total Gross Weight | SUM(Container Gross Weight for all containers) = SUM(SUM(Item Gross Weight) + Container Tare Weight, per container) |

---

#### FR-14M.8B Final Rates Section

After all containers and items have been entered, the system presents a **Final Rates** table. This table is auto-generated — it deduplicates all items across all containers, grouping by **Item Code + UOM**. The Maker enters one Rate (USD) per row.

> **Key design decision:** Rates are entered **once per unique Item Code + UOM combination**, not per container line. This ensures pricing consistency across containers for the same commodity and directly populates the Commercial Invoice line items.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| Item Code | Text (read-only) | — | Auto-derived from container items; aggregation key |
| Description of Goods | Text (read-only) | — | From the container item with this Item Code + UOM |
| HSN Code | Text (read-only) | — | From the container item with this Item Code + UOM |
| Total Quantity | Number (read-only) | — | Sum of Quantity across all containers for this Item Code + UOM |
| UOM | Text (read-only) | — | Aggregation key |
| Rate (USD per [UOM]) | Number (2 dp) | Yes | Unit price in USD per UOM. Column header is rendered dynamically — e.g., if UOM is KG, the header reads "Rate (USD per KG)". Entered by Maker once per row. |
| Amount (USD) | Calculated (read-only) | — | Auto-calculated: Total Quantity × Rate; updates as Maker types |

The Maker must enter a Rate for every row before the document can be saved or submitted.

**Payment & Terms** (on the Final Rates page, below the rates table — auto-populated from the selected PI; editable):

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Incoterms | Dropdown | No | Auto-populated from PI; editable. **Incoterms** master. See FR-14M.5. |
| Payment Terms | Dropdown | No | Auto-populated from PI; editable. **Payment Terms** master. See FR-14M.5. |

**Break-up in USD** (on the Final Rates page, below Payment & Terms — financial details for the Commercial Invoice PDF):

> **Incoterm-driven visibility:** The FOB Rate, Freight, and Insurance fields are shown or hidden based on the Incoterm selected in the Payment & Terms section above, using the same rules defined in **FR-09.7.3**. L/C Details is always shown regardless of Incoterm. When the Maker changes the Incoterm, fields re-render immediately; values previously entered in now-hidden fields are cleared. The frontend uses the existing `INCOTERM_SELLER_FIELDS` constant from `src/utils/constants.ts`.

| Field | Type | Visibility | Notes |
| --- | --- | --- | --- |
| FOB Rate | Number (2 dp) | See FR-09.7.3 — shown for FCA, FOB, CFR, CIF, CPT, CIP, DAP, DPU, DDP; hidden for EXW | Per-UOM rate in USD. System computes total FOB value as FOB Rate × total shipment quantity. Prints as 0.00 if hidden/not entered. |
| Freight | Number (2 dp) | See FR-09.7.3 — shown for CFR, CIF, CPT, CIP, DAP, DPU, DDP; hidden for EXW, FCA, FOB | Freight charges in USD. Prints as 0.00 if hidden/not entered. |
| Insurance | Number (2 dp) | See FR-09.7.3 — shown for CIF, CIP, DAP, DPU, DDP; hidden for all others | Insurance charges in USD. Prints as 0.00 if hidden/not entered. |
| L/C Details | Free text (multi-line) | Always shown | Letter of Credit reference details. Printed in the bottom-left section of the CI PDF. |

---

#### FR-14M.10 Summary / Review Page

After the Maker saves the combined document for the first time, the system displays a **summary page** showing aggregated line items. This view helps the Maker verify the commercial invoice totals before submission.

**Aggregated Line Items Table** — items aggregated by Item Code + UOM across all containers:

| Column | Source | Notes |
| --- | --- | --- |
| Marks & Nos. / Container Nos. | Container → Marks and Numbers + Container Reference | Lists all container references and marks associated with this item |
| HSN Code | Item → HSN Code |  |
| No. & Kind of Packages | Item → No & Kind of Packages | Joined values across containers for this item.\nThis field should be editable. Highlight this in different colour for user to notice in creation wizard. |
| Description of Goods | Item → Description of Goods |  |
| Item Code | Item → Item Code | Aggregation key (together with UOM) |
| Quantity | Sum of Quantity across all containers for this Item Code + UOM | Displayed with 3 decimal places |
| UOM | Item → UOM | Aggregation key |
| Rate (USD) | Final Rates section (FR-14M.8B) | Single rate per Item Code + UOM |
| Amount (USD) | Total Quantity × Rate | Auto-calculated |

**Weight Summary:**

| Field | Value |
| --- | --- |
| Total Net Weight | SUM(Net Weight per unit × Quantity) for all items across all containers (3 dp) |
| Total Gross Weight | SUM(Container Gross Weight) across all containers (3 dp) |

**Totals:**

| Field | Value |
| --- | --- |
| Total Amount (USD) | Sum of Amount (USD) across all aggregated line items |

**Payment & Terms** (read-only):

| Field | Value |
| --- | --- |
| Incoterms | Selected Incoterm (as entered on Page 5) |
| Payment Terms | Selected Payment Term (as entered on Page 5) |

**Break-up in USD** (read-only):

| Field | Value |
| --- | --- |
| FOB Rate (USD per UOM) | As entered on Page 5 |
| Freight (USD) | As entered on Page 5 |
| Insurance (USD) | As entered on Page 5 |
| L/C Details | As entered on Page 5 |

---

#### FR-14M.11 Document Numbers

Both numbers are auto-generated by the system when the combined document is first saved.

| Document | Format | Example |
| --- | --- | --- |
| Packing List | `PL-YYYY-NNNN` | `PL-2026-0001` |
| Commercial Invoice | `CI-YYYY-NNNN` | `CI-2026-0001` |

- YYYY = current calendar year at time of creation
- NNNN = zero-padded 4-digit sequence, unique per year within the system
- Both numbers are read-only after generation; neither can be manually overridden by the Maker
- Numbers must be generated with `select_for_update()` to prevent duplicates (per technical_architecture.md Section 9)

---

#### FR-14M.12 Workflow States

The combined PL + CI document follows the common workflow defined in FR-08. Both the Packing List and Commercial Invoice records are created simultaneously when the form is first saved, both starting in **Draft** status.

**Joint approval:** The PL and CI are treated as a single unit for approval purposes. One Submit action submits both; one Approve action approves both; one Reject/Rework action reworks both; one Permanently Reject action permanently rejects both. The Maker cannot submit only the PL or only the CI independently.

```
Draft → Pending Approval → Approved
                         → Rework → (Maker edits & resubmits) → Pending Approval

Any state → Permanently Rejected  (terminal — both PL and CI)
```

> **Note on Permanently Rejected:** When the combined document is Permanently Rejected, both the PL and CI records move to Permanently Rejected simultaneously. No further edits, submissions, or downloads are possible on either document.

**Role-based actions:**

| Action | Who | When |
| --- | --- | --- |
| Submit for Approval | Maker / Admin | Draft or Rework state |
| Delete (Deactivate) | Maker / Admin | Draft state only |
| Approve | Checker / Admin | Pending Approval state; approves both PL and CI |
| Reject (→ Rework) | Checker / Admin | Pending Approval state; rejection comments are mandatory; both documents return to Rework |
| Permanently Reject | Checker / Admin | Any state; comments are mandatory; both PL and CI permanently rejected |
| Download PDF | See FR-14M.13 |  |

---

#### FR-14M.14 Document Detail / View Page

After first save, the saved document is accessible as a read-only view for all roles. The detail page uses a **tabbed layout** with four tabs:

| Tab | Contents |
| --- | --- |
| **Document Header** | Document numbers and dates, Parties (Exporter, Consignee, Buyer, Notify Party), Shipping & Logistics, Countries, Payment & Terms (Incoterms, Payment Terms) |
| **Containers & Items** | All containers with their items; weight summary per container; shipment-level weight totals |
| **Final Rates** | Aggregated rates table (Item Code, Description, HSN, Total Qty, UOM, Rate, Amount); Break-up in USD (FOB Rate, Freight, Insurance, L/C Details) |
| **Bank & Payment** | Selected bank's full details (Beneficiary Name, Bank Name, Branch, Account No., IFSC, SWIFT) |

**Context-sensitive action buttons** (shown in the page header, gated by role and current status):

| Button | Role | When Visible |
| --- | --- | --- |
| Edit | Maker / Admin | Draft or Rework state |
| Submit for Approval | Maker / Admin | Draft or Rework state |
| Delete | Maker / Admin | Draft state only |
| Approve | Checker / Admin | Pending Approval state |
| Reject → Rework | Checker / Admin | Pending Approval state |
| Permanently Reject | Checker / Admin | Any state |
| Download PDF | Maker, Checker | Approved state only |
| Download PDF | Admin | Any state |

Rejection comments from the Checker (if any) are displayed on the detail page so the Maker can see what needs to be fixed.

---

#### FR-14M.13 PDF Output

**Single Download, Two Sections:** Downloading the document produces **one PDF file** with two sections separated by a page break:
1. **Packing List/Weight Note** (Section 1)
2. **COMMERCIAL INVOICE** (Section 2)

Both sections are included in every download. The watermark rules from FR-08.3 apply based on the single shared document status.

---

**PDF Section 1 — Packing List/Weight Note:**

*Page header (above the table):*
- Top-left: Exporter company logo (if configured)
- Top-centre: Exporter company name — large, bold
- Below centre: **"Packing List/Weight Note"** — centred subtitle

*Main table — Row 1 (3-column header row):*

| Exporter: *(label)* | Invoice No & Date: | Import/Export Code No: |
| --- | --- | --- |
| *(empty — content in Row 2)* | PL-YYYY-NNNN, DD.MM.YYYY | IEC Code of the Exporter |

*Main table — Row 2 (exporter addresses + references):*

Left side — 3 equal sub-columns:
- **Col A — Corporate Address:** Organisation Name, Corporate/Office address lines, City, PIN, Country
- **Col B — Registered Office:** Address flagged as type "Registered" — lines, City, State, PIN, Country
- **Col C — Factory Address:** Address flagged as type "Factory" — lines, City, PIN

Right side (merged, same row height):
- PO No. & Date: [value] [date]
- LC No. & Date: [value] [date]
- Other Reference(s): [value] [date]
- BL No. & Date: [value] [date]
- SO No. & Date: [value] [date]
- *(Only populated references are printed; unpopulated lines are omitted)*

*Main table — Row 3 (Consignee + Buyer):*

| Advising Bank/Consignee: [Name, full address] | Buyer (If other than Consignee): [Name, full address, Tel, Fax, Email] |
| --- | --- |

*Main table — Row 4 (Notify Party + Countries):*

| Consignee2/Importer/Notify Party: [Name, full address, Tel] | Country of Origin of Goods: [Country] | Country of Final Destination: [Country] |
| --- | --- | --- |

*Main table — Row 5 (Shipping + Info panel):*

| Pre-Carriaged By: [value] | Place of Receipt by Pre-Carrier: [value] | Vessel/Flight No: [value] | **Right info panel** (merged, spans rows 5–6): Incoterms: [Code + Place] Payment Terms: [full text] Additional Description: [text] |
| --- | --- | --- | --- |

*Main table — Row 6 (Ports):*

| Port of Loading: [Port Name] | Port of Discharge: [Port Name] | Final Destination: [Destination] | *(merged with right panel above)* |
| --- | --- | --- | --- |

*Items table:* One row per item per container. Containers are grouped visually. Rate and Amount (USD) are **not** printed on the PL — they appear on the CI section only.

| Marks & Nos./Container Nos. | HSN Code | Item Code | No. & Kind of Pkgs. | Description of Goods | Qty | UOM | Net Wt (per unit) | Total Net Wt | Inner Packing Wt | Item Gross Wt | Batch Details |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

- **Total Net Wt** = Net Weight per unit × Qty (calculated, read-only)
- **Item Gross Wt** = Net Weight per unit + Inner Packing Weight (calculated, read-only)

*Container subtotal row* (appears after all items in each container):

| Sum of Item Gross Weights | Container Tare Weight | Container Total Gross Weight |
| --- | --- | --- |
| SUM(Item Gross Wt for this container) | Container Tare Weight (entered) | Sum of Item Gross + Container Tare |

*Bottom section (two-column block):*

Left column:

| Container/TANK No. | Total Net Wt: | [value] [UOM] |
| --- | --- | --- |
| [List of Container References, one per line] | Total Gross Wt: | [value] [UOM] |

Right column (per-container tare table):

| Container No. | Tare Wt |
| --- | --- |
| [Container Reference 1] | [Tare Weight 1] [UOM] |
| [Container Reference 2] | [Tare Weight 2] [UOM] |
| **Total TARE Wt** | **[Sum of all container tare weights] [UOM]** |

*Signature block (bottom right):* "For [Exporter Organisation Name]" / "Authorised Signatory"

---

**PDF Section 2 — Commercial Invoice:**

The Commercial Invoice PDF section starts on a new page (page break after PL section).

*Page header (above the table):*
- Top-left: Exporter company logo (if configured)
- Top-centre: Exporter company name — large, bold
- Below centre: **"COMMERCIAL INVOICE"** — centred subtitle

*Main table — Row 1 (3-column header row):*

| Exporter: *(label)* | Invoice No & Date: | Import/Export Code No: |
| --- | --- | --- |
| *(empty — content in Row 2)* | CI-YYYY-NNNN, DD.MM.YYYY | IEC Code of the Exporter |

*Main table — Row 2 (exporter addresses + references):*

Left side — 3 equal sub-columns:
- **Col A — Corporate Office:** Organisation Name, address lines, City, PIN, Country
- **Col B — Registered Office:** Address flagged type "Registered" — lines, City, State, PIN, Country
- **Col C — Factory Address:** Address flagged type "Factory" — lines, City, PIN

Right side (merged): PO No. & Date / LC No. & Date / Other Reference(s) / BL No. & Date / SO No. & Date *(only populated references printed)*

*Main table — Row 3 (Consignee + Buyer):*

| Advising Bank/Consignee1: [Name, full address] | Buyer if other than Consignee: [Name, full address, Tel, Fax, Email] |
| --- | --- |

*Main table — Row 4 (Notify Party + Countries):*

| Consignee2/Importer/Notify Party: [Name, full address, Tel] | Country of Origin of Goods: [Country] | Country of Final Destination: [Country] |
| --- | --- | --- |

*Main table — Row 5 (Shipping + Info panel):*

| Pre-Carriaged By: [value] | Place of Receipt by Pre-Carrier: [value] | Vessel/Flight No: [value] | **Right info panel** (merged rows 5–6): Incoterms: [Code + Place] Payment Terms: [full text] Batch: [value] Additional Description: [text] |
| --- | --- | --- | --- |

*Main table — Row 6 (Ports):*

| Port of Loading: [Port Name] | Port of Discharge: [Port Name] | Final Destination: [Destination] | *(merged with right panel above)* |
| --- | --- | --- | --- |

*Items table (aggregated by Item Code + UOM):*

| Marks & Nos./Container Nos. | HSN Code | No. & Kind of Pkgs. | Description of Goods | Item Code | Qty | UOM | Net Wt (per unit) | Total Net Wt | Rate (USD) per [UOM] | Amount (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

- Items aggregated by Item Code + UOM across all containers
- **Marks & Nos./Container Nos.** — all container references and marks containing this item, combined
- **Qty** — sum of Quantity for this Item Code + UOM across all containers
- **Total Net Wt** = Net Weight per unit × Total Qty (calculated, read-only)
- **Rate (USD) per [UOM]** — column header is dynamic (e.g., "Rate (USD) per KG")
- **Amount (USD)** = Total Qty × Rate

*Bottom section — two-part row:*

Left part:

| Total Net Weight: | [value] [UOM] |
| --- | --- |
| Total Gross Weight: | [value] [UOM] |
| L/C Details: | [L/C Details text, if populated] |

Right part — "Break-up in USD(Approx.)":

| FOB Rate | [value] |
| --- | --- |
| Freight | [value] |
| Insurance | [value] |

*(FOB Rate, Freight, Insurance print as 0.00 if not entered)*

*Totals row:* "Amount Chargeable in currency: USD" | **Total: [Total Amount USD]**

*Amount in Words:* "Amount in Words: [Total amount in English] US-Dollar(s) Only."

*Declaration block:* "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."

*Bank details block:*
- **BENEFICIARY NAME:** [Beneficiary Name]
- **BANK NAME:** [Bank Name]
- **BRANCH NAME:** [Branch Name]
- **BRANCH ADDRESS:** [Branch Address]
- **A/C NO.:** [Account Number] &nbsp; **IFSC CODE:** [IFSC / Routing Number] *(only if present)* &nbsp; **SWIFT CODE:** [SWIFT Code]
- *(If intermediary bank configured):* Intermediary Institution Routing For Currency [Currency] A/C No.: [Account No.] [Bank Name] SWIFT Code: [SWIFT Code]

*Signature block (bottom right):* "For [Exporter Organisation Name]" / "Authorised Signatory"

---

**Watermark Rules:**

| Document Status | Watermark (both PL and CI sections) |
| --- | --- |
| Draft | Diagonal "DRAFT" watermark on both sections |
| Pending Approval | Diagonal "DRAFT" watermark on both sections |
| Rework | Diagonal "DRAFT" watermark on both sections |
| Approved | No watermark — clean output on both sections |

**PDF download access:**

| Who | When | Result |
| --- | --- | --- |
| Maker, Checker | Approved state only | Clean PDF (both PL and CI sections, no watermark) |
| Admin | Any state | PDF with appropriate watermark based on current status |

---

### 5.11.1 Master Data → Combined PL + CI Field Mapping

| Field | Source | Master Data / PI Fields Used |
| --- | --- | --- |
| Proforma Invoice (link) | Proforma Invoice master | PI number; stored as authoritative link on both PL and CI |
| Exporter | Organisation (tagged: Exporter) *(auto from PI)* | Name, IEC Code; Corporate Office address, Registered Office address (type "Registered"), Factory address (type "Factory") — all three printed on PDF |
| Consignee | Organisation (tagged: Consignee) *(auto from PI)* | Name, full address, Tel, Fax, Email — printed as "Advising Bank/Consignee1" (CI) / "Advising Bank/Consignee" (PL) |
| Buyer | Organisation (tagged: Buyer) *(auto from PI)* | Name, full address, Tel, Fax, Email |
| Notify Party | Organisation (tagged: Notify Party) | Name, full address, Tel — printed as "Consignee2/Importer/Notify Party" on both PDFs |
| Batch | Free text field on form | Printed in right info panel on CI PDF only |
| Country of Origin of Goods | Countries *(auto from PI)* | Country Name |
| Country of Final Destination | Countries *(auto from PI)* | Country Name |
| Pre-Carriage By | Pre-Carriage By *(auto from PI)* | Name |
| Place of Receipt | Locations *(auto from PI)* | Location Name, Country |
| Place of Receipt by Pre-Carrier | Locations *(auto from PI)* | Location Name, Country |
| Port of Loading | Ports *(auto from PI)* | Port Name, Country |
| Port of Discharge | Ports *(auto from PI)* | Port Name, Country |
| Final Destination | Locations *(auto from PI)* | Location Name, Country |
| Incoterms | Incoterms *(auto from PI)* | Code, Description |
| Payment Terms | Payment Terms *(auto from PI)* | Term Name |
| Item UOM | Units of Measurement | Unit Name / Abbreviation |
| Bank | Bank master | Beneficiary Name, Bank Name, Branch Name, Branch Address, Account Number, IFSC Code, SWIFT Code; Intermediary block if configured |
| Weight Unit (kg/lbs) | Entered by Maker at shipment level | Applied to all weight fields on both PDFs |
| Container Tare Weight | Entered by Maker per container | Used to calculate Container Gross Weight |
| Container Gross Weight | Calculated: SUM(Item Gross Weight) + Container Tare | Shown in container subtotal row on PL PDF |
| Net Weight per unit | Entered by Maker per item | Used to calculate Total Net Weight |
| Inner Packing Weight | Entered by Maker per item | Used to calculate Item Gross Weight |
| Item Gross Weight | Calculated: Net Weight + Inner Packing Weight | Shown in item rows on PL PDF |
| Total Net Weight | Calculated: SUM(Net per unit × Qty) | Shown on both PL and CI PDFs |
| Total Gross Weight | Calculated: SUM(Container Gross Weight) | Shown on both PL and CI PDFs |
| *(All other container, item, and reference fields)* | No master data — entered manually | — |

---

### 5.11.2 Validation Rules

| Rule | Error Message |
| --- | --- |
| Exporter is required | "Exporter is required." |
| Proforma Invoice is required | "Please select a Proforma Invoice." |
| Consignee is required | "Consignee is required." |
| At least one container required | "Add at least one container before submitting." |
| Each container must have at least one item | "Container [ref] must have at least one item." |
| Container Reference is required | "Container Reference is required." |
| Marks and Numbers is required | "Marks and Numbers is required." |
| Container Tare Weight is required | "Container Tare Weight is required." |
| Seal Number is required | "Seal Number is required." |
| Net Weight (per unit) is required on each item | "Net Weight is required." |
| Inner Packing Weight is required on each item | "Inner Packing Weight is required." |
| Weight Unit (kg/lbs) is required at shipment level | "Weight unit is required." |
| No & Kind of Packages is required | "No & Kind of Packages is required." |
| Description of Goods is required | "Description of Goods is required." |
| Quantity is required | "Quantity is required." |
| Item Code is required on each item | "Item Code is required." |
| HSN Code is required on each item | "HSN Code is required." |
| HSN Code format validation | HSN Code must match `^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?$` |
| UOM is required on each item | "UOM is required." |
| All rates in Final Rates section must be filled | "Rate (USD) is required for all items before saving." |
| Bank is required | "Bank is required." |
| All monetary amounts | Stored as `DecimalField(max_digits=15, decimal_places=2)`. Never FloatField. |
| All weights | Stored as `DecimalField(max_digits=12, decimal_places=3)`. Never FloatField. |

---

### 5.11.3 Weight Fields Specification

**Item level (entered per line item in each container):**

| Field | Type | Notes |
| --- | --- | --- |
| Net Weight (per unit) | Number (3 dp) | Weight of the goods only, excluding all packaging |
| Inner Packing Weight | Number (3 dp) | Weight of the packaging directly associated with this item (box, foam, wrapping, etc.) |
| Item Gross Weight | Calculated (read-only) | = Net Weight (per unit) + Inner Packing Weight |

**Container level:**

| Field | Type | Notes |
| --- | --- | --- |
| Container Tare Weight | Number (3 dp) | Weight of the empty container. For FCL, this is the ISO container tare weight stamped on the container door. |
| Container Gross Weight | Calculated (read-only) | = SUM(Item Gross Weight for all items in this container) + Container Tare Weight |

**Shipment level (auto-calculated across all containers):**

| Field | Formula |
| --- | --- |
| Total Net Weight | SUM(Net Weight per unit × Quantity) for all items across all containers |
| Total Gross Weight | SUM(Container Gross Weight) for all containers |

All weight fields use a single unit of measure (kg or lbs) selected at the shipment level. This unit is applied consistently across the Packing List, Commercial Invoice, and all PDFs.

---

## 6. Non-Functional Requirements

- **NFR-02 Performance** — Document generation and page load times should be under 3 seconds under normal load conditions.
- **NFR-03 Security** — All data must be encrypted at rest and in transit (TLS 1.2+). User sessions must be managed with secure, expiring tokens. Passwords must be stored as salted hashes.
- **NFR-04 Scalability** — The architecture must support horizontal scaling to accommodate growth in the number of users and documents.
- **NFR-05 Availability** — Target uptime of 99.9% (excluding scheduled maintenance windows).
- **NFR-06 Audit Trail** — All document creation, modification, and approval events must be logged with user identity and timestamp and retained for a minimum of 7 years to support trade compliance audits.
- **NFR-07 PDF Output** — Generated documents must be exportable as print-ready PDFs consistent with international trade document standards.
- **NFR-08 Browser Compatibility** — The application must be fully functional on the latest two versions of Chrome, Firefox, Safari, and Edge.

---

## 7. User Stories

### US-01: Create a Proforma Invoice Header
**As a** Maker, **I want to** create a proforma invoice by filling in header details from master data dropdowns, **so that** I can begin building an accurate, consistent document for the buyer before the shipment is confirmed.

**Acceptance Criteria:**
- [ ] Exporter dropdown shows only organisations tagged as "Exporter"; selection is required
- [ ] Consignee dropdown shows only organisations tagged as "Consignee"; selection is required
- [ ] Proforma Invoice No is auto-generated by the system and displayed as read-only; Maker cannot edit it
- [ ] Invoice Date defaults to today; Maker may change it
- [ ] Buyer Order No, Buyer Order Date, and Other References are optional free-text fields
- [ ] Country of Origin and Country of Final Destination are optional dropdowns populated from the Countries master
- [ ] All shipping & logistics fields (Pre-Carriage, Ports, Final Destination, etc.) are optional dropdowns from their respective master data lists
- [ ] Payment Terms and Incoterms dropdowns are required; Bank is optional
- [ ] Selecting a T&C Template auto-populates the Terms & Conditions preview; content is stored with the document
- [ ] On successful creation, the system redirects to the document detail / edit page where line items can be added
- [ ] If Exporter, Consignee, Payment Terms, or Incoterms are missing on submit, a validation error is shown and the form is not submitted

### US-02: Add Line Items to a Proforma Invoice
**As a** Maker, **I want to** add line items to a proforma invoice, **so that** the document reflects the actual commodities, quantities, and pricing for the shipment.

**Acceptance Criteria:**
- [ ] Maker can add one or more line items on the proforma invoice detail page
- [ ] Each line item requires: Description of Goods, Quantity, UOM (dropdown), and Rate (USD/[UOM])
- [ ] HSN Code and Item Code are optional per line item
- [ ] The Rate field label is dynamic and reflects the selected UOM — e.g., "Rate (USD/MT)" if UOM is MT, "Rate (USD/KG)" if UOM is KG
- [ ] Amount (USD) is automatically calculated as Quantity × Rate and displayed read-only
- [ ] After each addition, the totals summary updates: Total Quantity, Total Amount (USD), and Amount in Words
- [ ] Maker can edit an existing line item via an inline modal
- [ ] Maker can delete a line item; total summary recalculates immediately
- [ ] Line items cannot be added, edited, or deleted once the document status is Approved

### US-03: Submit a Proforma Invoice for Approval
**As a** Maker, **I want to** submit a completed proforma invoice for approval, **so that** a Checker can review it before it is shared with the buyer.

**Acceptance Criteria:**
- [ ] Maker can submit a document for approval from the document detail page when it is in Draft status
- [ ] The document status changes from Draft to **Pending Approval**
- [ ] The Checker and Company Admin are notified that a document is awaiting approval
- [ ] The Maker cannot edit header fields or line items once the document is submitted
- [ ] The submission event is recorded in the audit trail with the Maker's name and timestamp

### US-04: Approve or Reject a Proforma Invoice
**As a** Checker, **I want to** review and approve or reject a submitted proforma invoice, **so that** only verified documents are finalised and shared with buyers.

**Acceptance Criteria:**
- [ ] Checker can view the complete proforma invoice including all header fields, line items, totals, and T&C
- [ ] Checker can Approve the document; status changes to Approved and the document becomes fully read-only
- [ ] Checker can Reject the document with mandatory rejection comments; status changes to **Rework** and is returned to the Maker for revision
- [ ] Maker is notified upon rejection and can view the Checker's comments in the audit trail
- [ ] Approval and rejection events are recorded in the audit trail with actor name, timestamp, and any comments
- [ ] A Checker cannot approve a document they themselves created as Maker

### US-05: Download Proforma Invoice PDF
**As a** Maker or Checker, **I want to** download a print-ready PDF of the proforma invoice at any workflow stage, **so that** I can preview the document layout or share it with the buyer.

**Acceptance Criteria:**
- [ ] A "Download PDF" action is available on the proforma invoice detail page for all roles
- [ ] PDF is downloadable regardless of document status (Draft, Pending Approval, Approved, Rework)
- [ ] The PDF layout matches the defined structure: header table, line items table, totals, bank details, T&C
- [ ] The PDF footer reads: "This is a computer-generated document. Signature is not required."
- [ ] All monetary values are formatted with comma separators and 2 decimal places (e.g., 1,234.56)
- [ ] Quantities are formatted with 3 decimal places (e.g., 1,234.567)
- [ ] The Total Amount in Words is correctly computed and displayed in the PDF
- [ ] The PDF file is named after the Proforma Invoice number

### US-08: Create a Combined Packing List + Commercial Invoice
**As a** Maker, **I want to** create a combined PL + CI by selecting an Approved PI, entering container and item data, and pricing each item in the Final Rates section, **so that** both documents are generated together without re-entering shipment information.

**Acceptance Criteria:**
- [ ] The creation flow begins with selecting a Consignee, then an Approved Proforma Invoice belonging to that Consignee; the PI dropdown is searchable and shows the most recently approved PI first
- [ ] On PI selection, all overlapping header, shipping, payment, and country fields are auto-populated from the PI and become editable
- [ ] Both Packing List No and Commercial Invoice No are auto-generated on first save; neither is editable by the Maker
- [ ] All Order Reference fields (PO, LC, BL, SO, Other) are optional; each has a paired date field
- [ ] Notify Party is an optional dropdown from organisations tagged as "Notify Party"
- [ ] At least one container must be added before the form can be submitted; each container requires Container Reference, Marks and Numbers, Container Tare Weight (3 dp), and Seal Number; Container Gross Weight is auto-calculated (read-only)
- [ ] Each container must have at least one item; each item requires HSN Code, Item Code, No & Kind of Packages, Description of Goods, UOM, Quantity (3 dp), Net Weight per unit (3 dp), and Inner Packing Weight (3 dp); Batch Details is optional
- [ ] Item Gross Weight is auto-calculated as Net Weight + Inner Packing Weight (read-only)
- [ ] After all containers and items are entered, the Final Rates section shows a deduplicated table of Item Code + UOM combinations; the Maker must enter a Rate (USD) for every row
- [ ] Amount (USD) per row is auto-calculated as Total Quantity × Rate and updates as the Maker types
- [ ] Bank is required; FOB Rate, Freight, Insurance, and L/C Details are optional
- [ ] On successful save, both a PL number and a CI number are generated; the system shows a summary/review page with aggregated line items and totals
- [ ] If any required field is missing on submit, a validation error is shown and the form is not submitted

### US-09: Edit a Combined PL + CI Document
**As a** Maker, **I want to** edit a combined PL + CI in Draft or Rework status, **so that** I can correct errors or respond to a Checker's rejection comments before resubmitting.

**Acceptance Criteria:**
- [ ] Maker can reopen a Draft or Rework combined document via the same create/edit form
- [ ] All header, reference, shipping, container, item, rate, and bank fields are editable in Draft and Rework states
- [ ] Maker can add new containers, remove containers, add items, and remove items
- [ ] Maker can use "Copy Container" to duplicate an existing container; the copy opens with blank Container Reference, Marks & Numbers, and Seal Number; Container Tare Weight is pre-filled from the source container
- [ ] The Final Rates section updates automatically as containers and items are added or removed
- [ ] A document in Pending Approval or Approved state cannot be edited by the Maker
- [ ] Saving updates the existing record; neither PL No nor CI No changes after first save

### US-10: Submit a Combined PL + CI for Approval
**As a** Maker, **I want to** submit a completed combined PL + CI for approval, **so that** a Checker can verify both the packing and pricing before the documents are finalised.

**Acceptance Criteria:**
- [ ] Maker can submit a combined document when status is Draft or Rework
- [ ] One Submit action submits both the Packing List and the Commercial Invoice simultaneously; they cannot be submitted separately
- [ ] Status changes to Pending Approval for both documents upon submission
- [ ] The Checker and Company Admin are notified that a document awaits review
- [ ] The submission event is recorded in the audit trail with actor name and timestamp
- [ ] The document becomes non-editable once submitted

### US-11: Approve, Reject, or Permanently Reject a Combined PL + CI
**As a** Checker, **I want to** approve, reject, or permanently reject a submitted combined PL + CI, **so that** only verified documents are finalised or closed out appropriately.

**Acceptance Criteria:**
- [ ] Checker can Approve a Pending Approval combined document; status changes to Approved for both PL and CI simultaneously
- [ ] Checker can Reject a Pending Approval document with mandatory comments; status changes to Rework for both; Maker is notified
- [ ] Checker or Company Admin can Permanently Reject a combined document; both PL and CI move to Permanently Rejected — a terminal state; a comment is mandatory
- [ ] All approval, rejection, and permanent rejection events are recorded in the audit trail with actor, timestamp, and comments
- [ ] A Maker cannot approve their own document

### US-12: Download the Combined PL + CI PDF
**As a** Maker or Checker, **I want to** download the approved combined PL + CI as a single print-ready PDF, **so that** I can share both documents with the freight forwarder and buyer in one file.

**Acceptance Criteria:**
- [ ] "Download PDF" action is available for Maker and Checker only when the document status is Approved
- [ ] Company Admin can download the PDF at any workflow state
- [ ] The PDF is a single file: Packing List/Weight Note section first, then a page break, then the Commercial Invoice section
- [ ] Draft, Pending Approval, and Rework states display a diagonal "DRAFT" watermark on both sections; Approved state produces a clean PDF with no watermark
- [ ] The PL section includes: exporter details (corporate, registered, and factory addresses), consignee, buyer, notify party, all order references (only populated ones printed), shipping details, per-container item rows with weights, container subtotal rows, and bottom summary with total weights and per-container tare table
- [ ] The CI section includes: exporter details, consignee, buyer, notify party, shipping details, aggregated line items (by Item Code + UOM) with rates and amounts, weight totals, FOB/Freight/Insurance break-up, bank details, declaration, and Amount in Words
- [ ] Weights are formatted to 3 decimal places; monetary amounts to 2 decimal places
- [ ] The PDF filename is derived from the PL and CI numbers

---

## 8. Data Requirements

- **Core Entities:** Organisation, User, Role, Bank, Country, Port, Place of Receipt, Incoterm, UOM, Payment Term, Final Destination, Pre-Carriage By, Terms & Conditions Template, Proforma Invoice, Proforma Invoice Line Item, Combined PL+CI Document (single record linking both a Packing List record and a Commercial Invoice record), Packing List Container, Packing List Container Item, Commercial Invoice Line Item (aggregated by Item Code + UOM from container items; stores rate_usd), Document Approval Log (Audit Trail)
- **Data Flow:** Master data is created by Company Admins → referenced by Makers during document creation → documents pass through approval workflow → final approved documents are archived and available for reporting and PDF export
- **Retention:** Document records and approval audit logs must be retained for a minimum of 7 years in accordance with trade compliance requirements
- **Privacy:** Personally identifiable information (contact names, email addresses, phone numbers) must be handled in accordance with applicable data protection regulations (e.g., GDPR where applicable)

---

## 9. Integrations & Dependencies

| System | Type | Notes |
| --- | --- | --- |
| Email / Notification Service | API | Required for approval workflow notifications (e.g., SendGrid, AWS SES) |
| PDF Generation Engine | Library / Service | Required for producing print-ready trade document PDFs |
| Authentication Provider | Service | Internal auth or third-party (e.g., Auth0) — to be decided |
| Country / Currency Reference Data | Static / API | Seed data for countries, ISO codes, and currencies |

---

## 10. Constraints & Assumptions

### Constraints
- The platform is web-only; no mobile application will be developed in this version
- Organisation records cannot be deleted, only deactivated, to preserve historical document integrity

### Assumptions
- At least one Company Admin account must exist before Maker or Checker accounts can be created
- The initial supported language is English; localisation is not in scope for v1
- The trading house's primary regulatory context is Indian export trade (IEC code, GSTIN); other regulatory regimes may need to be considered in future versions

---

## 11. Open Questions

| # | Question | Owner | Status | Answer |
| --- | --- | --- | --- | --- |
| 1 | What document types are required beyond the initial three (commercial invoice, proforma invoice, packing list)? e.g., Bill of Lading, Certificate of Origin, Shipping Bill | Product | Resolved | Out of scope for this version. The platform will support only the three current document types. Additional document types are deferred to future versions. |
| 2 | Should the platform support Letter of Credit (LC) compliance checks on commercial invoice fields? | Product / Business | Resolved | Out of scope for this version. |
| 3 | Are there specific PDF templates / layouts mandated by the company, or will a standard layout suffice? | Business | Resolved | A standard PDF layout is acceptable. No company-mandated format is required. |
| 4 | What are the reporting requirements in detail? (frequency, recipients, format) | Business | Resolved | Add a Reports entry to the left-hand sidebar navigation now as a placeholder. Report content and functionality will be defined and built in a future version. |
| 5 | Is multi-currency support required within a single document (e.g., invoice in USD, domestic costs in INR)? | Business | Resolved | Single currency per document only. Multi-currency within a single document is not required. |
| 6 | What is the expected number of organisations, users, and documents per month at launch and at scale? | Business / Engineering | Resolved | Design baseline: 5 organisations, each producing approximately 5 documents per month. Use this as the assumption for infrastructure and performance planning. |
| 7 | Should the Forgot Password flow be self-service (email reset) or admin-managed? | Product | Resolved | Forgot Password is not self-service. If a user forgets their password, the Company Admin for their organisation resets it manually. There is no email-based self-reset flow. |
| 8 | Are there any existing systems (ERP, accounting) that will need to exchange data with TradeDocs in the future? | Business / Engineering | Resolved | No external system integrations are required. TradeDocs operates as a standalone platform in this version. |
| 9 | Are line item quantities and rates always in MT (Metric Tonnes) and USD/MT, or should the UOM and currency be selectable per line item? The current implementation hardcodes MT and USD. | Business / Product | Resolved | UOM is a selectable dropdown (from the UOM master) on Proforma Invoice line items, consistent with Packing List items. The Rate field label is dynamic and reflects the selected UOM — e.g., if UOM is MT the field reads "Rate (USD/MT)"; if UOM is Litre it reads "Rate (USD/Litre)". Amount = Quantity × Rate regardless of the unit selected. |
| 10 | Should "Buyer if other than Consignee" on the proforma invoice be a separately selectable organisation (from the Buyer-tagged org list) or is it always auto-derived from the Consignee? | Business / Product | Resolved | It is a separately selectable field. The Maker explicitly chooses a Buyer-tagged organisation from the dropdown. It is not auto-derived from the Consignee. |
| 11 | Should the system support attaching and storing the signed/stamped copy of an approved document (e.g., uploading a scanned PDF back against the record)? | Business | Resolved | Yes. The system should support uploading and storing a signed or stamped scanned copy of an approved document against its record. |
| 12 | (FR-04) Should the Organisation master capture an organisation-level Email ID and Country in addition to what is held under Points of Contact and Addresses? Both fields are used directly on generated PDF documents (e.g., exporter email, exporter country). | Business / Product | Resolved | The Organisation master is restructured. An organisation can have multiple addresses (e.g., Registered, Factory, Office). Each address carries its own Email, Phone Number, and Point of Contact Name — these are not held separately at the organisation level. When a Maker selects an organisation in a document, they then select which of that organisation's addresses to use. |
| 13 | (FR-04) When an organisation has multiple addresses, which address is printed on generated documents? Should one address be flagged as the Primary / Document Address, or should the Maker select the address at the time of document creation? | Business / Product | Resolved | Two-step selection at document creation time: (1) select the organisation, then (2) select which address to use. If the organisation has only one address it is selected automatically. If it has more than one, the Maker must explicitly choose. |
| 14 | (FR-05) Should the Bank master include a Beneficiary Name field (i.e., the name of the account holder as it appears on wire transfer instructions and printed documents)? | Business | Resolved | Yes. The Bank master must include a Beneficiary Name field. |
| 15 | (FR-06) Should "Place of Receipt" be maintained as a separate master list (distinct from the Ports master), given that goods may be received at an inland depot or warehouse rather than a port? | Business / Product | Resolved | Yes. Place of Receipt is a separate master list from Ports. |
| 16 | (FR-14) The Packing List has a free-text "Invoice Number" field. Does this refer to the Proforma Invoice number, the Commercial Invoice number, or an external invoice? Should it be a dropdown linked to existing documents in the system rather than a free-text entry? | Business / Product | Resolved | Replace the single free-text field with two separate dropdown fields: one linked to existing Proforma Invoices in the system, and one linked to existing Commercial Invoices. Both are optional. |
| 17 | (FR-14) The PDF generator falls back to a linked Proforma Invoice for shipping fields (Ports, Pre-Carriage, Incoterms, etc.) if those fields are blank on the Packing List itself. Should the Maker explicitly select a Proforma Invoice to link when creating a Packing List? If so, a PI lookup/dropdown field is needed on the creation form. | Business / Product | Resolved | Yes. A Packing List is always created in the context of a Proforma Invoice. Selecting the PI is the mandatory first step on the Packing List creation form. All overlapping fields (Exporter, Consignee, Buyer, Shipping & Logistics, Payment & Terms, Countries) are auto-populated from the selected PI and remain editable. No fallback logic is needed — the PI link is always present. |
| 18 | (FR-14) Notify Party is currently a free-text field on the Packing List. Should it instead be a dropdown from Organisations tagged as "Notify Party" in the Organisation master, for consistency with other party fields? | Business / Product | Resolved | Yes. Notify Party should be a dropdown from the Organisation master (organisations tagged as "Notify Party"), consistent with all other party fields. |
| 19 | (FR-14) The Packing List PDF renders a separate "Registered Office" block for the Exporter alongside the corporate address. Is this "Registered Office" the address flagged as type "Registered" in the Organisation's address list, or is it a separate concept requiring dedicated fields? | Business / Product | Resolved | The Registered Office block on the PDF is sourced from the address within the Organisation's address list that is flagged as type "Registered". No new or separate fields are needed. |
| 20 | (FR-14) The Packing List PDF displays the Consignee's phone number. Should this come from the Organisation's primary Point of Contact, or is a dedicated phone field needed at the Organisation level? | Business / Product | Resolved | The phone number displayed on the PDF comes from the specific address the Maker selected for the consignee on that document. Phone is stored per address, consistent with the Organisation structure resolved in OQ#12. |
| 21 | (FR-14) When a Maker uses "Copy Container", the current implementation copies only the items (not the Container Reference, Marks & Numbers, or weights). Should copied containers also pre-fill weights from the source container as a starting point? | Business / Product | Resolved | Yes. When copying a container, the copy should pre-fill Net Weight and Tare Weight from the source container. The Maker can adjust them before saving. |
| 22 | (FR-14) The Packing List has a "Permanently Rejected" terminal state. Who should be authorised to permanently reject a document — only the Company Admin, or also the Checker? | Business | Resolved | Both Company Admin and Checker can permanently reject a Packing List. |
| 23 | (FR-15) The Commercial Invoice PDF uses `invoice.incoterm` and `invoice.payment_term` fields on the CI record itself — but the 5-step creation wizard has no step for selecting Incoterms or Payment Terms. Are these auto-populated from the linked Packing List? Or is an additional step needed in the wizard for the Maker to select them? | Business / Product | Resolved | Incoterms and Payment Terms on the Commercial Invoice are automatically carried over from the linked Packing List. No additional wizard step is needed. |
| 24 | (FR-15) The Commercial Invoice PDF includes a local-currency amount (`invoice.amount`) alongside the USD total amount (`invoice.total_amount_usd`). The creation wizard has no field for a local-currency amount. What is this field — is it derived from FOB + Freight + Insurance in a local currency? Which currency is it denominated in, and how is it calculated? | Business / Product | Resolved | The local-currency amount field is removed entirely. The Commercial Invoice will display only USD amounts. |
| 25 | (FR-15) The Commercial Invoice PDF renders a Buyer block using `invoice.buyer`, but the creation wizard has no step for selecting a Buyer. Is the Buyer auto-populated from the linked Packing List? If so, is a Buyer field required on the Packing List, or is it optional? | Business / Product | Resolved | Buyer on the Commercial Invoice is automatically carried over from the linked Packing List. No additional wizard step is needed. |
| 26 | (FR-15) The current implementation allows a Checker to approve a Commercial Invoice that is in **Rejected** status directly — without the Maker re-submitting it. Is this intentional? The workflow for Packing List requires re-submission before re-approval; should Commercial Invoice follow the same pattern? | Business | Resolved | A Checker must not approve a Rejected CI directly. The Maker must re-submit it first (moving it to Pending Approval) before the Checker can act. The CI workflow must match the Packing List workflow in this regard. |
| 27 | (FR-15) The **Disabled** state is a terminal state applied by the Checker to an Approved CI. What is the business purpose of disabling an Approved CI? Is a reason/comment required when disabling? Should the Maker or any other role be notified? | Business | Resolved | Disable is used to void a CI when a mistake is discovered after approval, since Approved documents cannot be edited. A mandatory comment is required when disabling. This also establishes a platform-wide policy: a mandatory comment is required whenever any document moves into a rejected state across all three document types — covering Reject on Proforma Invoice, Reject (Rework) and Permanently Reject on Packing List, and Reject and Disable on Commercial Invoice. |
| 28 | (FR-15) The Commercial Invoice index does not display a CI number column — only date, consignee, amount, and status. Is a CI number auto-generated by the system? If so, how is it formatted, and should it appear in the index and on the PDF? | Business / Product | Resolved | CI numbers are auto-generated in the format `CI-YYYY-NNNN` (e.g., `CI-2026-0001`), where YYYY is the year and NNNN is a 4-digit incrementing sequence. The number is unique per exporter account. The Maker can manually override the auto-generated number if needed. The CI number must appear in the index and on the PDF. |
| 29 | (FR-15) There is no visible edit flow for a Commercial Invoice after wizard completion. Once a CI is in Draft status, can the Maker change any fields (e.g., bank, charges, line item prices, L/C details)? If yes, what fields are editable and via what UI — the same wizard, a dedicated edit page, or inline on a detail page? | Business / Product | Resolved | A CI in Draft or Rejected status can be opened for editing by double-clicking it in the CI index. A CI in any other state (Pending Approval, Approved, Disabled) is read-only and cannot be edited. |
| 30 | (FR-15) The FOB Rate field on the Commercial Invoice wizard is a numeric field. Does it represent: (a) a rate per UOM used to compute the total FOB value from the line item quantities, or (b) the total FOB amount for the shipment entered directly by the Maker? The semantics affect how the PDF totals are computed. | Business | Resolved | FOB Rate is a per-UOM rate (e.g., USD per MT). The system computes the total FOB value by multiplying the FOB Rate by the total shipment quantity. |

---

## 12. Revision History

| Version | Date | Author | Summary |
| --- | --- | --- | --- |
| 0.1 | — | — | Initial draft |
| 0.2 | 2026-03-15 | — | Structured and expanded: stakeholder roles clarified, FR-01 through FR-13 formalised, master data entities detailed, NFRs defined, user stories added, open questions raised |
| 0.3 | 2026-03-15 | — | Proforma invoice fully specified (FR-09.1–09.6) based on implementation review; master data → document field mapping table added (section 5.8.1); user stories US-01 through US-07 written with full acceptance criteria; open questions added for master data gaps identified during review (OQ#12–15) |
| 0.4 | 2026-03-15 | — | Packing List fully specified (FR-14.1–14.10, section 5.11) including 3-level hierarchy (list → containers → items), extended workflow with Rework and Permanently Rejected states, copy-container feature, PDF layout, master data mapping (section 5.11.1); user stories US-08–US-12 added with full acceptance criteria; data entities updated; open questions OQ#16–22 added |
| 0.5 | 2026-03-15 | — | Commercial Invoice fully specified (FR-15.1–15.8, section 5.12) including 5-step wizard, mandatory Approved Packing List dependency, line item aggregation by Item Code + UOM, two-mode PDF (Draft watermark vs Final), extended workflow with Rejected and Disabled states, master data mapping (section 5.12.1); user stories US-13–US-17 added with full acceptance criteria; Commercial Invoice Line Item added to data entities; open questions OQ#23–30 added |
| 0.6 | 2026-03-15 | — | Section 13 (Validation Rules) added as a separate, standalone section covering master data field-level validations (13.1) and document creation validations (13.2) for all three document types; two additional open questions OQ#31–32 raised from validation analysis |
| 0.7 | 2026-03-15 | — | All resolved open questions (OQ#4, OQ#9–16, OQ#18–30) propagated into functional requirement sections: sidebar updated with Reports placeholder; FR-04 restructured for per-address contact info with two-step selection; FR-05 Beneficiary Name added; FR-06 Place of Receipt added; FR-08 mandatory comment policy and signed-copy upload added; FR-09 Buyer dropdown and dynamic UOM/Rate label added; FR-14 Invoice Number replaced with PI/CI dropdowns, Notify Party changed to dropdown, Copy Container pre-fills weights, Permanently Reject authority extended to Checker; FR-15 CI number format defined, Incoterms/Payment Terms/Buyer auto-carried from PL, Rejected CI workflow corrected (Maker must resubmit), Disable requires mandatory comment, local-currency amount removed, FOB Rate clarified as per-UOM; validation rules updated for revised org structure |
| 0.8 | 2026-03-15 | — | Packing List creation flow redesigned: a PL is always created in the context of a Proforma Invoice (OQ#17 resolved). Selecting the PI is now the mandatory first step; all overlapping fields (Exporter, Consignee, Buyer, Shipping & Logistics, Payment & Terms, Countries) are auto-populated from the selected PI and remain editable; the Maker's only manual input is container and item data. FR-14 opening, FR-14.2 header table, FR-14.4 Shipping & Logistics, FR-14.5 Payment & Terms, FR-14.6 Countries, section 5.11.1 field mapping, and US-08 acceptance criteria all updated accordingly. |
| 0.9 | 2026-03-15 | — | Workflow states centralised. FR-08 expanded into the authoritative platform-wide approval workflow section (FR-08.1 Common States, FR-08.2 Common Rules, FR-08.3 PDF Generation Rules, FR-08.4 Signed Copy Upload). Duplicate state meanings tables removed from FR-14.9 (Packing List) and FR-15.7 (Commercial Invoice); each retains only its state machine diagram, document-specific terminal state definition, and role-based actions table. |
| 1.0 | 2026-03-15 | — | FR-08.1 made the single authoritative source for all workflow state definitions. Permanently Rejected formalised as a platform-wide terminal state with cascading rule (PI rejection cascades to linked PLs and CIs; PL rejection cascades to linked CIs; comment dialog must show affected downstream documents). Disabled added to FR-08.1 as a CI-only terminal state. Document-specific state tables fully removed from FR-14.9 and FR-15.7; their state diagrams updated to reference FR-08.1. Cross-reference paragraph removed from FR-08. |
| 1.1 | 2026-03-15 | — | FR-04 (Organisation master data) restructured into four labelled sub-sections (FR-04.1 General Information, FR-04.2 Tax Codes, FR-04.3 Addresses, FR-04.4 Document Role Tags). All fields converted to tables. Tax code validation rules moved into a dedicated table by Tax Type (GST/GSTIN, PAN, all others). Implementation note about phone library formalised. Role Tags table shows which dropdown each tag populates. |
| 1.2 | 2026-03-15 | — | Converted to single-tenant architecture. Master Admin role removed. FR-01 rewritten as single-organisation platform. Section 5.1 renamed from "Platform & Multi-Tenancy" to "Platform". Sidebar updated (Organisation Management, User Management, Reports now visible to Company Admin only, not Master Admin). FR-10 rewritten (Company Admin manages all users directly). NFR-01 Data Isolation removed. NFR-04 Scalability updated (removed tenant reference). US-07 (Master Admin onboarding story) removed. Multi-Tenancy bullet removed from Data Requirements. Constraints and Assumptions updated to remove Master Admin and cross-organisation references. Validation uniqueness scope updated from "within the tenant" to "within the system". |

---

## 13. Validation Rules

> **Reviewer Note:** This section is a standalone addition. Every rule below is a proposed validation. Review each rule and remove any that do not apply to your business context before including this section in the final PRD. Nothing in this section modifies any existing functional requirement.

---

### 13.1 Master Data Validations

#### 13.1.1 Organisation (FR-04)

| Field | Validation Rule |
| --- | --- |
| Organisation Name | Required. Max 255 characters. Must be unique within the system. |
| IEC Code | Required when the organisation is tagged as **Exporter**. Must be exactly 10 alphanumeric characters (DGFT standard). Must be unique within the system. |
| Tax Type (per row) | Required if a Tax Code is entered for that row; cannot save a tax row with a code but no type. |
| Tax Code (per row) | Required if a Tax Type is entered for that row; max 50 characters. |
| Addresses — Address Type | Required for each address row. Must be one of: Registered, Factory, Office. |
| Addresses — Address Line 1 | Required for each address row. |
| Addresses — City | Required for each address row. |
| Addresses — Country | Required for each address row; must be selected from the Countries master. |
| Addresses — Email | Required for each address row. Must be a valid email format (RFC 5322). |
| Addresses — Phone | If entered, both Country Code and Number are required. Number must be numeric, max 20 digits. |
| Addresses — Contact Name | Required for each address row. |
| Addresses (overall) | At least one address must be saved on the organisation record. |
| Document Role Tags | At least one role tag (Exporter, Consignee, Buyer, Notify Party) must be selected. An organisation with no tags cannot appear in any document dropdown. The Notify Party tag enables the organisation to appear in the Notify Party dropdown on Packing Lists. |

---

#### 13.1.2 Bank (FR-05)

| Field | Validation Rule |
| --- | --- |
| Bank Name | Required. Max 255 characters. |
| Branch Name | Required. Max 255 characters. |
| Account Number | Required. Max 50 characters. |
| SWIFT Code | Required. Must be exactly 8 or 11 characters. Allowed characters: uppercase letters and digits (ISO 9362 format). |
| IBAN | Optional. If provided: must start with a 2-letter country code (uppercase), followed by 2 check digits, followed by up to 30 alphanumeric characters. Maximum 34 characters total. |
| Account Type | Required. Must be one of: Current, Savings, Checking. |
| Currency of Account | Required. Must be selected from the currency / country master. |

---

#### 13.1.3 Countries (FR-06)

| Field | Validation Rule |
| --- | --- |
| Country Name | Required. Max 100 characters. Must be unique. |
| ISO Alpha-2 Code | Required. Must be exactly 2 uppercase letters. Must be unique. |
| ISO Alpha-3 Code | Required. Must be exactly 3 uppercase letters. Must be unique. |

---

#### 13.1.4 Incoterms (FR-06)

| Field | Validation Rule |
| --- | --- |
| Code | Required. Max 10 characters. Must be unique within the system. |
| Full Name | Required. Max 100 characters. |

---

#### 13.1.5 Units of Measurement (FR-06)

| Field | Validation Rule |
| --- | --- |
| Unit Name | Required. Max 100 characters. |
| Abbreviation | Required. Max 20 characters. Must be unique within the system. |

---

#### 13.1.6 Ports (FR-06)

| Field | Validation Rule |
| --- | --- |
| Port Name | Required. Max 255 characters. |
| Port Code | Optional. If provided: must follow UN/LOCODE format — 2 uppercase letters (country code) + space + 3 uppercase alphanumeric characters (e.g., `IN BOM`). Must be unique within the system if provided. |
| Country | Required. Must be selected from the Countries master. |

---

#### 13.1.7 Payment Terms (FR-06)

| Field | Validation Rule |
| --- | --- |
| Term Name | Required. Max 100 characters. Must be unique within the system. |

---

#### 13.1.8 Final Destinations (FR-06)

| Field | Validation Rule |
| --- | --- |
| Destination Name | Required. Max 255 characters. |
| Country | Required. Must be selected from the Countries master. |

---

#### 13.1.9 Pre-Carriage By (FR-06)

| Field | Validation Rule |
| --- | --- |
| Name | Required. Max 100 characters. Must be unique within the system. |

---

#### 13.1.10 Terms & Conditions Templates (FR-07)

| Field | Validation Rule |
| --- | --- |
| Template Name | Required. Max 255 characters. Must be unique within the system. |
| Organisation (association) | At least one organisation must be associated before the template can be saved. |
| Body content | Must not be empty. A template with a blank body cannot be saved. |

---

### 13.2 Document Creation Validations

#### 13.2.1 Proforma Invoice

**On Save (any state save / Draft creation):**

| Field / Rule | Validation |
| --- | --- |
| Exporter | Required. |
| Consignee | Required. |
| Payment Terms | Required. |
| Incoterms | Required. |
| Proforma Invoice Date | Must be a valid date if entered. |
| Buyer Order Date | Must be a valid date if entered. Must not be in the future. |
| Additional charge rows — Amount (USD) | If a row is added, the Amount field must be ≥ 0. Max 2 decimal places. The Description field is required if an Amount is entered. |
| Validity for Acceptance | If entered, must be a valid date. Must not be in the past at the time of entry. |
| Validity for Shipment | If entered, must be a valid date. If both Validity for Acceptance and Validity for Shipment are set, Validity for Shipment must be ≥ Validity for Acceptance. |

**On Line Item Add / Edit:**

| Field / Rule | Validation |
| --- | --- |
| Description of Goods | Required. |
| Quantity | Required. Must be > 0. Max 3 decimal places. |
| UOM | Required when Quantity is entered. Must be selected from the UOM master. |
| Rate (USD/[UOM]) | Required. Must be > 0. Max 2 decimal places. |
| Amount (USD) | Calculated automatically as Quantity × Rate. Not directly editable. |

**On Submit for Approval:**

| Rule | Validation |
| --- | --- |
| All save-time validations above | Must all pass before submission is allowed. |
| Line items | At least one line item must be present. A Proforma Invoice with zero line items cannot be submitted. |

---

#### 13.2.2 Packing List

**On Save:**

| Field / Rule | Validation |
| --- | --- |
| Exporter | Required. |
| Consignee | Required. |
| Packing List Date | Must be a valid date if entered. |
| PO / LC / BL / SO / Other — Date fields | Each must be a valid date if entered. If a date is entered without its corresponding reference number (or vice versa), display a warning prompting the Maker to fill in the paired field. |
| Container count | At least one container must be added before the form can be saved or submitted. |

**Per Container:**

| Field / Rule | Validation |
| --- | --- |
| Net Weight | Required. Must be > 0. Max 3 decimal places. |
| Tare Weight | Required. Must be ≥ 0. Max 3 decimal places. *(See Open Question #32)* |
| Gross Weight | Auto-calculated as Net Weight + Tare Weight. Never directly editable. Must equal Net + Tare at all times. |
| Item count per container | Each container must have at least one item. A container with zero items cannot be saved. |

**Per Container Item:**

| Field / Rule | Validation |
| --- | --- |
| No & Kind of Packages | Required. Max 100 characters. |
| Description of Goods | Required. |
| Quantity | Required. Must be > 0. Max 3 decimal places. |
| UOM | Required when Quantity is entered. *(Confirm with business — see existing OQ.)* |
| HSN Code | Optional. If entered, max 20 characters. |
| Item Code | Optional. If entered, max 100 characters. |

**On Submit for Approval:**

| Rule | Validation |
| --- | --- |
| All save-time validations above | Must all pass. |
| All containers valid | Every container in the list must individually pass the per-container validation (weights + at least one valid item). |

---

#### 13.2.3 Commercial Invoice — 5-Step Wizard

**Step 1 — Consignee:**

| Rule | Validation |
| --- | --- |
| Consignee | Required. Must be an organisation with at least one Approved Packing List. The dropdown must only show eligible consignees; the Maker cannot manually type a consignee name. |

**Step 2 — Packing List:**

| Rule | Validation |
| --- | --- |
| Packing List | Required. Must be in Approved status. Must belong to the consignee selected in Step 1. |

**Step 3 — Line Items & Pricing:**

| Field / Rule | Validation |
| --- | --- |
| Rate (USD) — per row | Required for every aggregated line item row. Must be > 0. Max 2 decimal places. |
| Amount (USD) — per row | Auto-calculated as Total Quantity × Rate. Not directly editable. |
| All rows must have a rate | The Maker cannot proceed to Step 4 until every aggregated line item has a Rate entered. |

**Step 4 — Bank:**

| Rule | Validation |
| --- | --- |
| Bank | Required. The Maker cannot proceed to Step 5 without selecting a bank. |

**Step 5 — Charges & L/C Details:**

| Field / Rule | Validation |
| --- | --- |
| FOB Rate | Optional. If entered, must be ≥ 0. Max 2 decimal places. |
| Freight | Optional. If entered, must be ≥ 0. Max 2 decimal places. |
| Insurance | Optional. If entered, must be ≥ 0. Max 2 decimal places. |
| L/C Details | Optional. Free text; max 500 characters if a limit is desired. |

**On Submit for Approval:**

| Rule | Validation |
| --- | --- |
| All wizard-step validations | Must all pass. |
| Linked Packing List status | At the moment of submission, the linked Packing List must still be in Approved status. If the PL has been moved to a terminal state between CI creation and CI submission, the system must block submission and notify the Maker. *(See Open Question #32)* |

---

### 13.3 Open Questions Raised by Validation Analysis

| # | Question | Owner | Status |
| --- | --- | --- | --- |
| 31 | Should a Proforma Invoice be submittable for approval with zero line items (header only)? Or must at least one line item exist before submission is permitted? | Business | Resolved — At least one line item must exist before a PI can be submitted for approval. |
| 32 | If a Packing List is moved to Permanently Rejected after a Commercial Invoice has been created from it, what should happen to the Commercial Invoice? Should it be automatically invalidated, or should it continue through its own workflow independently? | Business / Product | Open |

# Packing List — Weight & Packaging Fields Redesign

## Context
This replaces the current `ContainerItem` field set with a structured packaging model
that separates physical package count, type, and material quantity — the way
international trade packing lists are actually filled out.

---

## 1. Master Data — New Entity: Type of Package

Add a new master data entity called **Type of Package** alongside the existing
Reference Data entities (UOM, Country, Port, etc.).

| Attribute | Detail |
|-----------|--------|
| Model name | `TypeOfPackage` |
| Table | `master_data_typeofpackage` |
| Fields | `name` (CharField max 100), `is_active` (BooleanField default True) |
| Soft-delete | Yes — same pattern as all other ReferenceData entities |
| Pre-populate | Seed with common international packaging types on migration: Drums, Bags, Boxes, Cartons, Pallets, Crates, Bales, Bundles, Cylinders, Bottles, Jerricans, Rolls, Tins, Cases |

### Frontend — Master Data page
- Add a **"Type of Package"** tab to the existing Reference Data tabbed page
  (same pattern as UOM, Country, Port tabs).
- Rename the existing **"UOM"** tab to **"Material Unit"** throughout the master
  data admin page (label only — the model/URL/API key stays `uom`).

---

## 2. ContainerItem Model — Field Changes

### Remove these fields entirely
| Field to remove | Current column label |
|-----------------|----------------------|
| `packages_kind` | No & Kind of Pkgs |
| `quantity` | Qty |
| `net_weight` | Net Weight |
| `inner_packing_weight` | Inner Pkg Wt |

### Add these fields
| New field | Type | Notes |
|-----------|------|-------|
| `no_of_packages` | `DecimalField(max_digits=12, decimal_places=3)` | Number of physical packages (e.g. 10 drums) |
| `type_of_package` | `ForeignKey("master_data.TypeOfPackage", on_delete=PROTECT)` | FK to new master data entity |
| `qty_per_package` | `DecimalField(max_digits=12, decimal_places=3)` | Material quantity inside each package |
| `weight_per_unit_packaging` | `DecimalField(max_digits=12, decimal_places=3)` | Weight of one empty package unit |
| `net_material_weight` | `DecimalField(max_digits=12, decimal_places=3, editable=False)` | **Computed**: `no_of_packages × qty_per_package` |
| `item_gross_weight` | `DecimalField(max_digits=12, decimal_places=3, editable=False)` | **Computed** (renamed behaviour): `net_material_weight + (no_of_packages × weight_per_unit_packaging)` |

### Keep unchanged
- `hsn_code`, `item_code`, `description`, `batch_details`
- `uom` FK (this is now labelled **"Material Unit"** in UI; model field name stays `uom`)
- `item_gross_weight` stays stored/computed on `save()`

### Computation logic (on `ContainerItem.save()`)
```python
self.net_material_weight = self.no_of_packages * self.qty_per_package
self.item_gross_weight = self.net_material_weight + (self.no_of_packages * self.weight_per_unit_packaging)
```
Container `gross_weight` rollup stays the same: `SUM(item.item_gross_weight) + tare_weight`.

---

## 3. Create / Edit Wizard — Step 3 (Containers & Items)

### Item row field order (left to right)
| # | Column label | Source |
|---|--------------|--------|
| 1 | # | Row number |
| 2 | HSN Code | `hsn_code` |
| 3 | Item Code | `item_code` |
| 4 | Description | `description` |
| 5 | Batch No. | `batch_details` |
| 6 | No. of Package | `no_of_packages` |
| 7 | Type of Package | `type_of_package` (dropdown — TypeOfPackage master data) |
| 8 | Material Unit | `uom` (dropdown — UOM master data, now labelled "Material Unit") |
| 9 | Qty Per Package | `qty_per_package` |
| 10 | Wt Per Unit Pkg | `weight_per_unit_packaging` |
| 11 | Net Material Wt | `net_material_weight` (read-only, computed) |
| 12 | Gross Weight | `item_gross_weight` (read-only, computed) |

### Validation rules (same strictness as current)
- `no_of_packages` > 0 (required)
- `type_of_package` required
- `uom` required (Material Unit)
- `qty_per_package` ≥ 0 (required)
- `weight_per_unit_packaging` ≥ 0 (required)
- `hsn_code`, `batch_details` remain optional
- `item_code`, `description` remain required

### "Item ready" gate (before row can be saved)
Required: `item_code`, `uom`, `no_of_packages`, `type_of_package`, `qty_per_package`,
`weight_per_unit_packaging`, `description`.

---

## 4. PDF — Packing List Section

### Remove these columns
- No & Kind of Pkgs
- Qty
- Net Weight
- Inner Pkg Wt

### New column sequence in the items table
| # | Header |
|---|--------|
| 1 | # |
| 2 | HSN Code |
| 3 | Item Code |
| 4 | Description |
| 5 | Batch No. |
| 6 | No. of Package |
| 7 | Type of Package |
| 8 | Material Unit |
| 9 | Qty Per Package |
| 10 | Wt Per Unit Pkg |
| 11 | Net Material Wt |
| 12 | Gross Weight |

Container-level totals row continues to show **Total Gross Weight**
(sum of all `item_gross_weight` + `tare_weight`).

---

## 5. Files to Touch

| Layer | File | Change |
|-------|------|--------|
| Master data model | `apps/master_data/models.py` | Add `TypeOfPackage` model |
| Master data migration | new migration file | Add `master_data_typeofpackage` table + seed data |
| Master data serializer | `apps/master_data/serializers.py` | Add `TypeOfPackageSerializer` |
| Master data views | `apps/master_data/views.py` | Add `TypeOfPackageViewSet` |
| Master data URLs | `apps/master_data/urls.py` | Register `type-of-packages` route |
| PL model | `apps/packing_list/models.py` | Swap fields on `ContainerItem`; update `save()` |
| PL migration | new migration file | Drop old columns, add new columns |
| PL serializer | `apps/packing_list/serializers.py` | Update `ContainerItemSerializer` fields + validation |
| PL tests | `apps/packing_list/tests/test_models.py` | Update factories + model tests |
| PL tests | `apps/packing_list/tests/test_views.py` | Update API tests |
| Frontend API | `frontend/src/api/referenceData.ts` | Add `listTypeOfPackages()` |
| Frontend create | `frontend/src/pages/packing-list/PackingListCreatePage.tsx` | Swap item row fields |
| Frontend edit | `frontend/src/pages/packing-list/PackingListEditPage.tsx` | Same as create |
| Frontend detail | `frontend/src/pages/packing-list/PackingListDetailPage.tsx` | Update display columns |
| Frontend master data | `frontend/src/pages/master-data/ReferenceDataPage.tsx` | Add "Type of Package" tab; rename "UOM" tab to "Material Unit" |
| PDF generator | `pdf/packing_list_generator.py` | Swap item table columns |
