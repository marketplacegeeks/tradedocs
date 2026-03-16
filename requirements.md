# Product Requirements Document — TradeDocs

**Version:** 1.2
**Status:** Draft — Pending Review
**Last Updated:** 2026-03-15

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
- 
- =ter data to ensure consistency and reuse across all documents
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
- **Account Nickname** – A short internal label to identify the account (e.g., "USD Operating Account", "AED Payroll Account")
- **Beneficiary Name** – The name of the account holder as it appears on wire transfer instructions and printed documents
- **Bank Name**
- **Bank Country** – Dropdown from the country master
- **Branch Address** – Optional
- **Account Number**
- **Account Type** – Dropdown: Current / Savings / Checking
- **Currency of Account** – Dropdown from the currency master
**Routing & Identification Codes**
- **SWIFT / BIC Code** – Optional; required for international wire transfers
- **IBAN** – Optional; required for transfers within Europe and parts of the Middle East
- **IFSC / Routing Number / Sort Code** – Optional; region-specific national routing code (India: IFSC, USA: ACH Routing Number, UK: Sort Code)
- Attachment of cancelled cheque optional

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

> **Note:** The Packing List and Commercial Invoice have role-specific PDF download restrictions beyond the above. See FR-14.9 and FR-15.7 respectively.

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
| Proforma Invoice No | Text (read-only) | — | Auto-generated by the system on save. PR-Year-Number (4 digit starting from 0) |
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
| Place of Receipt | Dropdown | No | Locations,Location Name, Country  master |
| Place of Receipt by Pre-Carrier | Dropdown | No | Locations,Location Name, Country   master |
| Vessel / Flight No | Free text | No | Name or number of the vessel or flight |
| Port of Loading | Dropdown | No | **Ports** master |
| Port of Discharge | Dropdown | No | **Ports** master |
| Final Destination | Dropdown | No | Location Name, Country   master |
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

Give user an option to manually add rows for additional charges - Free text description and fees. One or more rows. e.g Bank Charges

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
  - Row 8: Port of Loading | Port of Discharge | Final Destination | Marks & Nos / Container No | No & Kind of Packages
4. **Line items table**: Sr. | HSN Code | Item Code | Description of Goods | Qty | UOM | Rate (USD/UOM) | Amount (USD)
5. **Total amount**: "Amount Chargeable in: USD" | Total | $amount
6. **Amount in words**
7. **Validity & terms block**: Validity for Acceptance | Validity for Shipment | Bank Charges | Partial Shipment | Transshipment
8. **MT103 payment instruction** (static text)
9. **Declaration** (static text)
10. **Beneficiary / Bank details**: Beneficiary Name | Bank Name | Branch Name | Branch Address | A/C No. | SWIFT Code
11. **Terms & Conditions** (on a new page, if present)
12. **Footer** (every page): "This is a computer-generated document. Signature is not required."

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
| Final Destination | Final Destinations | Location Name, Country   master |
| Payment Terms | Payment Terms | Term Name |
| Incoterms | Incoterms | Code, Description |
| Bank | Bank | Beneficiary Name, Bank Name, Branch Name, Branch Address, Account Number, SWIFT Code |
| Terms & Conditions | T&C Templates | Template Name, Content (HTML) |
| *(All line items)* | No master data — entered manually per document | — |

### 5.11 Document Generation — Packing List

- **FR-14** A Maker shall be able to create, edit, and manage Packing Lists. The document is titled **"Packing List, Weight Note"** on the generated PDF. **A Packing List is always created in the context of an existing Proforma Invoice.** The Maker begins by selecting a Proforma Invoice; all overlapping header, shipping, payment, and country fields are then auto-populated from the selected PI and remain editable. The only information the Maker must add manually is the container and item data.

#### FR-14.1 Data Hierarchy

The Packing List follows a three-level hierarchy:

```
Packing List (header + references + shipping)
  └── Container 1
        └── Item 1
        └── Item 2
  └── Container 2
        └── Item 1
        ...
```


---

#### Header section for packing list - FR-14.2 Header Details

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Proforma Invoice | Dropdown | Yes | Select from all Proforma Invoices in the system (any status). On selection, all overlapping fields (Exporter, Consignee, Buyer, Shipping & Logistics, Payment & Terms, Countries) are auto-populated from the selected PI and become editable. The PI number is stored as the authoritative link on the Packing List record. |
| Exporter | Dropdown | Yes | Auto-populated from the selected Proforma Invoice; editable. Organisations tagged as **Exporter**. |
| Consignee | Dropdown | Yes | Auto-populated from the selected Proforma Invoice; editable. Organisations tagged as **Consignee**. |
| Buyer (if different from Consignee) | Dropdown | No | Auto-populated from the selected Proforma Invoice if set; editable. Organisations tagged as **Buyer**. |
| Packing List No | Text (read-only) | — | Auto-generated by the system on save. Format: PL-YYYY-Serial No |
| Packing List Date | Date | No | Date of the packing list |
| Notify Party | Dropdown | No | Organisations tagged as **Notify Party** in the Organisation master |

---

#### FR-14.3 Order References

All reference fields are optional. Each number field has a paired date field.

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

References that have a value print on the PDF in the **References block** alongside the exporter details, formatted as: `Label No/Date: value / date`.

---

#### FR-14.4 Shipping & Logistics

All fields in this section are auto-populated from the linked Proforma Invoice on creation and remain editable by the Maker.

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

#### FR-14.5 Payment & Terms

Both fields are auto-populated from the linked Proforma Invoice on creation and remain editable by the Maker.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Incoterms | Dropdown | No | Auto-populated from PI; editable. **Incoterms** master. |
| Payment Terms | Dropdown | No | Auto-populated from PI; editable. **Payment Terms** master. |

---

#### FR-14.6 Countries

Both fields are auto-populated from the linked Proforma Invoice on creation and remain editable by the Maker.

| Field | Type | Required | Source / Notes |
| --- | --- | --- | --- |
| Country of Origin of Goods | Dropdown | No | Auto-populated from PI; editable. **Countries** master. |
| Country of Final Destination | Dropdown | No | Auto-populated from PI; editable. **Countries** master. |

---

#### FR-14.7 Containers

A packing list must have **at least one container**. Each container contains at least one item.

**Per Container:**

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Container Reference | Free text | Yes | Container identification reference (e.g., CONT001) |
| Marks and Numbers | Free text | Yes | Shipping marks on packages |
| Net Weight | Number (3 dp) | Yes | Net weight of goods in this container |
| Tare Weight | Number (3 dp) | Yes | Weight of the empty container |
| Gross Weight | Calculated (read-only) | Yes | Auto-calculated: Net Weight + Tare Weight |
| Seal Number | Free Text | Yes | Free Text |

A Maker may **Copy Container** to duplicate a container and then modify the new copy. This speeds up data entry for shipments with repeated commodity structures across containers. When copying: all items are copied; Net Weight and Tare Weight are pre-filled from the source container (the Maker may adjust them); Container Reference and Marks & Numbers , Seal noare left blank for the Maker to fill in.

---

#### FR-14.8 Items (per Container)

Each container must have **at least one item**. Items represent individual commodity lines within that container.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| HSN Code | Free text | No | Harmonized System Nomenclature code |
| Item Code | Free text | No | Internal product code |
| No & Kind of Packages | Free text | Yes | e.g., "10 Boxes", "5 Pallets" |
| Description of Goods | Textarea | Yes | Full commodity description |
| Quantity | Number | Yes | Quantity of goods |
| UOM | Dropdown | No | **Units of Measurement** master (e.g., MT, KG, PCS) |
| Batch Details | Free text | No | Batch or lot number for traceability |

---

#### FR-14.9 Workflow States

The Packing List follows the common workflow defined in FR-08. All state definitions and platform-wide rules are in FR-08.

```
Draft → Pending Approval → Approved
                        → Rework → (Maker edits & resubmits) → Pending Approval
                        → Permanently Rejected  (terminal — see FR-08.1)
```

**Role-based actions by state:**

| Action | Who | When |
| --- | --- | --- |
| Submit for Approval | Maker | Draft state |
| Re-submit for Approval | Maker | Rework state |
| Delete (Deactivate) | Maker | Draft state only |
| Approve | Checker / Admin | Pending Approval state |
| Reject (→ Rework) | Checker / Admin | Pending Approval state; rejection comments are mandatory |
| Permanently Reject | Checker / Admin | Any state; comments are mandatory |
| Download PDF | Maker, Checker | Approved state only |
| Download PDF | Admin | Any state |

---

#### FR-14.10 PDF Output Layout

The generated PDF is titled **"Packing List, Weight Note"** and follows this structure:

1. **Exporter name** — centred, large, bold
2. **Document title** — "Packing List, Weight Note"
3. **Summary block — Row 1** (2 columns merged | IEC Code | Invoice No)
  - "Exporter:" label across columns 0–1 | IEC Code | Invoice Number
4. **Summary block — Row 2** (4 columns):
  - Col 0: Exporter corporate office — Name, Address, Country, Email
  - Col 1: Exporter registered office — sourced from the address within the Organisation's address list that is flagged as type "Registered"; shows Name, Address, Country, Phone, Email
  - Col 2–3 (merged): Order References (PO, LC, B/L, SO, Other — each with number and date, only if populated)
5. **Consignee & Buyer block** (2 columns, 90mm each):
  - Col 0: Consignee — Name, Address, Country, Phone, Email
  - Col 1: Buyer — Name, Address, Country, Phone, Email (if buyer differs from consignee; otherwise shows consignee details)
6. **Summary bottom row** (4 equal columns):
  - Notify Party (merged across cols 0–1) | Country of Origin of Goods | Country of Final Destination
7. **Shipping block** (6 equal columns, 2 rows):
  - Row 1: Pre-Carriage By | Place of Receipt by Pre-Carrier | Vessel/Flight No | Incoterms + Payment Terms (merged cols 3–5)
  - Row 2: Port of Loading | Port of Discharge | Final Destination | *(merged with above)*
8. **Per-container block** (repeated for each container, kept together on page):
  - Container header: Container Reference | Marks & Numbers
  - Container weights: Net Weight | Tare Weight | Gross Weight
  - Items table: Sr. | HSN/Item Code | No & Kind of Packages | Description of Goods | Qty | UOM | Batch Details
9. **Totals row**: Total Net Weight | Total Tare Weight | Total Gross Weight (summed across all containers)
10. **Footer note**: "Quantities and UOM as per container item details."
11. **Footer** (every page): "This is a computer-generated document. Signature is not required."

---

### 5.11.1 Master Data → Packing List Field Mapping

Fields marked *(auto from PI)* are pre-filled from the linked Proforma Invoice at creation time and remain editable.

| Packing List Field | Source | Master Data / PI Fields Used |
| --- | --- | --- |
| Proforma Invoice (link) | Proforma Invoice master | PI number; stored as the authoritative link |
| Exporter | Organisation (tagged: Exporter) *(auto from PI)* | Name, Selected Address, Country, Email, IEC Code |
| Exporter Registered Office *(PDF)* | Organisation — address of type "Registered" | Name, Address, Country, Phone, Email |
| Consignee | Organisation (tagged: Consignee) *(auto from PI)* | Name, Selected Address, Country, Phone, Email |
| Buyer | Organisation (tagged: Buyer) *(auto from PI)* | Name, Selected Address, Country, Phone, Email |
| Country of Origin of Goods | Countries *(auto from PI)* | Country Name |
| Country of Final Destination | Countries *(auto from PI)* | Country Name |
| Pre-Carriage By | Pre-Carriage By *(auto from PI)* | Name |
| Place of Receipt | Place of Receipt *(auto from PI)* | Name |
| Place of Receipt by Pre-Carrier | Place of Receipt *(auto from PI)* | Name |
| Port of Loading | Ports *(auto from PI)* | Port Name |
| Port of Discharge | Ports *(auto from PI)* | Port Name |
| Final Destination | Final Destinations *(auto from PI)* | Destination Name |
| Incoterms | Incoterms *(auto from PI)* | Code |
| Payment Terms | Payment Terms *(auto from PI)* | Term Name |
| Notify Party | Organisation (tagged: Notify Party) | Name, Selected Address, Country, Phone, Email |
| Item UOM | Units of Measurement | Unit Name / Abbreviation |
| *(All container and item fields)* | No master data — entered manually per document | — |

---

### 5.12 Document Generation — Commercial Invoice

- **FR-15** A Maker shall be able to create and manage Commercial Invoices. The document is titled **"COMMERCIAL INVOICE"** on the generated PDF. **A Commercial Invoice can only be created from an existing Approved Packing List.** There is no standalone creation path. Upon creation, the system auto-generates a CI number in the format **`CI-YYYY-NNNN`** (e.g., `CI-2026-0001`), where YYYY is the current year and NNNN is a zero-padded 4-digit sequence unique per exporter account. The Maker may manually override the auto-generated number if needed. The CI number is displayed in the index list and on the PDF.

#### FR-15.1 Creation Overview — 5-Step Wizard

The Commercial Invoice creation follows a guided 5-step wizard. All data sourced from the linked Approved Packing List is read-only and cannot be overridden during creation. The wizard steps are:

| Step | Name | Purpose |
| --- | --- | --- |
| 1 | Select Consignee | Choose the consignee; only consignees that have at least one Approved Packing List are shown |
| 2 | Select Packing List | Choose one Approved Packing List linked to the selected consignee |
| 3 | Review & Price Line Items | Review aggregated line items derived from the Packing List; enter unit price per item |
| 4 | Select Bank | Choose the bank account for payment details on the document |
| 5 | Charges & L/C Details | Enter FOB Rate, Freight, Insurance, and Letter of Credit details |

On completion of Step 5, the system creates the Commercial Invoice in **Draft** status. Incoterms and Payment Terms are automatically carried over from the linked Packing List — no additional wizard step is required for these fields. The Buyer is also automatically carried over from the linked Packing List.

A CI in **Draft** or **Rejected** status can be reopened for editing by double-clicking the record in the CI index. The same wizard fields (pricing, bank, charges, L/C details) become editable. A CI in any other state (Pending Approval, Approved, Disabled) is fully read-only.

---

#### FR-15.2 Step 1 — Consignee Selection

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Consignee | Dropdown | Yes | Shows only organisations tagged as **Consignee** that have at least one Approved Packing List |

The system filters the consignee list to only those for whom an Approved Packing List exists. A consignee with no Approved Packing Lists will not appear.

---

#### FR-15.3 Step 2 — Packing List Selection

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Packing List | Dropdown | Yes | Shows Approved Packing Lists for the selected consignee only; each entry shows the PL number |

Selecting a Packing List locks the document to that PL. All references (PO, LC, BL, SO, Other), all shipping fields, all container weights, the exporter, and the consignee are sourced from the linked Packing List and cannot be changed on the Commercial Invoice.

---

#### FR-15.4 Step 3 — Aggregated Line Items and Pricing

The system automatically aggregates all items from all containers in the selected Packing List. Items are aggregated by **Item Code + Unit of Measurement (UOM)**. Each aggregated row represents the total quantity of that item across all containers.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Item Code | Text (read-only) | — | Sourced from PL container items; aggregated key |
| UOM | Text (read-only) | — | Unit of measurement; aggregated key |
| HSN Code | Text (read-only) | — | Sourced from PL container items |
| Description of Goods | Text (read-only) | — | Sourced from PL container items |
| No & Kind of Packages | Text (read-only) | — | Sourced from PL container items; multiple values joined across containers |
| Total Quantity | Number (read-only) | — | Sum of item quantity across all containers (for this item_code + unit_id combination) |
| Rate (USD) | Number (2 dp) | Yes | Unit price in USD; entered by Maker per aggregated row |
| Amount (USD) | Calculated (read-only) | — | Auto-calculated: Total Quantity × Rate |

The Maker must enter a Rate (USD) for every aggregated line item row. Amount is calculated and displayed automatically. The Maker cannot change item codes, quantities, descriptions, or UOM — these are fixed from the Packing List.

---

#### FR-15.5 Step 4 — Bank Selection

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Bank | Dropdown | Yes | Shows all bank records from the **Bank** master; displayed as "Bank Name – Account Number" or similar |

Bank selection is mandatory. The selected bank's details (Bank Name, Branch Name, Branch Address, Account Number, SWIFT Code) print on the Commercial Invoice PDF.

---

#### FR-15.6 Step 5 — Charges & L/C Details

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| FOB Rate | Number (2 dp) | No | Per-UOM rate in USD (e.g., USD per MT). The system computes the total FOB value as FOB Rate × total shipment quantity across all line items. |
| Freight | Number (2 dp) | No | Freight charges in USD |
| Insurance | Number (2 dp) | No | Insurance charges in USD |
| L/C Details | Free text (multi-line) | No | Letter of Credit reference details |

---

#### FR-15.7 Workflow States

The Commercial Invoice follows the common workflow defined in FR-08. All state definitions and platform-wide rules are in FR-08.

```
Draft → Pending Approval → Approved → Disabled  (terminal — see FR-08.1)
                         → Rejected → (Maker re-submits) → Pending Approval
```

**Role-based actions by state:**

| Action | Who | When |
| --- | --- | --- |
| Submit for Approval | Maker | Draft or Rejected state |
| Download Draft PDF | Maker | Draft or Rejected state |
| Download Draft PDF | Admin | Any non-Approved state |
| Download Final PDF | Maker, Checker, Admin | Approved state only |
| Approve | Checker / Admin | Pending Approval state only |
| Reject (with mandatory comments) | Checker / Admin | Pending Approval state |
| Disable (with mandatory comment) | Checker / Admin | Approved state only; terminal action |
| View Rejection Comments | Maker, Checker | Rejected state; opens audit trail |


---

#### FR-15.8 PDF Output

The Commercial Invoice supports **two PDF modes**:

| Mode | When Available | Visual Indicator |
| --- | --- | --- |
| **Draft PDF** | Draft, Rejected states (Maker and Admin) | Diagonal watermark: "DRAFT" in light red across the document |
| **Final PDF** | Approved state only (all roles) | No watermark; clean output |

**PDF Layout:**

1. **Exporter name** — centred, large, bold (from linked Packing List → Exporter Organisation)
2. **Document title** — "COMMERCIAL INVOICE" | **CI Number** (auto-generated `CI-YYYY-NNNN`, overridable by Maker)
3. **Main information block**:
  - Col 0: Exporter — Name, IEC Code, Address, Country, Email, Registered Office details
  - Col 1: References (PO, LC, BL, SO, Other — each with number and date; only populated references printed)
  - Col 2: Consignee — Name, Address, Country
  - Col 3: Buyer — Name, Address, Country (if buyer differs from consignee)
4. **Shipping block** (sourced from linked Packing List):
  - Pre-Carriage By | Place of Receipt by Pre-Carrier | Vessel/Flight No | Incoterms | Payment Terms
  - Port of Loading | Port of Discharge | Final Destination
5. **Line items table**: Sr. | HSN Code | No & Kind of Packages | Item Code | Description of Goods | Qty | Rate (USD) | Amount (USD)
6. **Weight summary**: Total Net Weight | Total Gross Weight (summed from PL containers)
7. **Totals block**:
  - Total Amount (USD)
  - Amount in Words
8. **Charges block**: FOB Rate (per UOM) | Total FOB Value (computed: FOB Rate × total quantity) | Freight | Insurance
9. **L/C Details**
10. **Bank details**: Bank Name | Branch Name | Branch Address | Account Number | SWIFT Code
11. **Footer** (every page): "This is a computer-generated document. Signature is not required."

---

### 5.12.1 Master Data → Commercial Invoice Field Mapping

The table below shows which master data entities and linked-document fields populate each section of the Commercial Invoice.

| Commercial Invoice Field | Source | Fields Used |
| --- | --- | --- |
| Exporter | Linked Packing List → Organisation (tagged: Exporter) | Name, IEC Code, Address, Country, Email, Registered Office Address |
| Consignee | Linked Packing List → Organisation (tagged: Consignee) | Name, Address, Country |
| Buyer | Linked Packing List → Organisation (tagged: Buyer) | Name, Address, Country |
| References (PO, LC, BL, SO, Other) | Linked Packing List → Order References | Number and Date per reference type |
| Shipping fields (Pre-Carriage, Ports, Vessel, Final Destination) | Linked Packing List → Shipping fields | All shipping field values |
| Incoterms | Linked Packing List → Incoterms | Code, Description (automatically carried over; not re-entered on CI) |
| Payment Terms | Linked Packing List → Payment Terms | Term Name (automatically carried over; not re-entered on CI) |
| Container Weights | Linked Packing List → Containers | Net Weight, Gross Weight (summed) |
| Line items (Item Code, HSN Code, Description, Packages, Qty, UOM) | Aggregated from PL Container Items (by Item Code + UOM) | All item fields; quantity is sum across containers |
| Rate (USD) per line item | Entered by Maker in Step 3 of wizard | unit_price_usd |
| Bank | Bank master | Bank Name, Branch Name, Branch Address, Account Number, SWIFT Code |
| FOB Rate, Freight, Insurance | Entered by Maker in Step 5 | Numeric values |
| L/C Details | Entered by Maker in Step 5 | Free text |

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
- [ ] Each line item requires: Description of Goods, Quantity (MT), and Rate (USD/MT)
- [ ] HSN Code and Item Code are optional per line item
- [ ] Amount (USD) is automatically calculated as Quantity × Rate and displayed read-only
- [ ] After each addition, the totals summary updates: Total Quantity (MT), Total Amount (USD), and Amount in Words
- [ ] Maker can edit an existing line item via an inline modal
- [ ] Maker can delete a line item; total summary recalculates immediately
- [ ] Line items cannot be added, edited, or deleted once the document status is Approved

### US-03: Submit a Proforma Invoice for Approval
**As a** Maker, **I want to** submit a completed proforma invoice for approval, **so that** a Checker can review it before it is shared with the buyer.

**Acceptance Criteria:**
- [ ] Maker can submit a document for approval from the document detail page when it is in Draft status
- [ ] The document status changes from Draft to "Submitted for Approval"
- [ ] The Checker and Company Admin are notified that a document is awaiting approval
- [ ] The Maker cannot edit header fields or line items once the document is submitted
- [ ] The submission event is recorded in the audit trail with the Maker's name and timestamp

### US-04: Approve or Reject a Proforma Invoice
**As a** Checker, **I want to** review and approve or reject a submitted proforma invoice, **so that** only verified documents are finalised and shared with buyers.

**Acceptance Criteria:**
- [ ] Checker can view the complete proforma invoice including all header fields, line items, totals, and T&C
- [ ] Checker can Approve the document; status changes to Approved and the document becomes fully read-only
- [ ] Checker can Reject the document with mandatory rejection comments; status returns to Draft
- [ ] Maker is notified upon rejection and can view the Checker's comments in the audit trail
- [ ] Approval and rejection events are recorded in the audit trail with actor name, timestamp, and any comments
- [ ] A Checker cannot approve a document they themselves created as Maker

### US-05: Download Proforma Invoice PDF
**As a** Maker or Checker, **I want to** download a print-ready PDF of the proforma invoice at any workflow stage, **so that** I can preview the document layout or share it with the buyer.

**Acceptance Criteria:**
- [ ] A "Download PDF" action is available on the proforma invoice detail page for all roles
- [ ] PDF is downloadable regardless of document status (Draft, Submitted, Approved, Rejected)
- [ ] The PDF layout matches the defined structure: header table, line items table, totals, bank details, T&C
- [ ] The PDF footer reads: "This is a computer-generated document. Signature is not required."
- [ ] All monetary values are formatted with comma separators and 2 decimal places (e.g., 1,234.56)
- [ ] Quantities are formatted with 3 decimal places (e.g., 1,234.567)
- [ ] The Total Amount in Words is correctly computed and displayed in the PDF
- [ ] The PDF file is named after the Proforma Invoice number

### US-08: Create a Packing List
**As a** Maker, **I want to** create a packing list by first selecting a Proforma Invoice and then adding container data, **so that** I can accurately document the physical shipment contents and weights without re-entering information that already exists on the PI.

**Acceptance Criteria:**
- [ ] The Packing List creation form opens with a mandatory Proforma Invoice dropdown as the first field; the form is blocked until a PI is selected
- [ ] On PI selection, the following fields are immediately auto-populated and become editable: Exporter, Consignee, Buyer, Pre-Carriage By, Place of Receipt, Place of Receipt by Pre-Carrier, Vessel / Flight No, Port of Loading, Port of Discharge, Final Destination, Incoterms, Payment Terms, Country of Origin of Goods, Country of Final Destination
- [ ] Changing the PI selection updates all auto-populated fields to reflect the newly selected PI
- [ ] Exporter and Consignee remain required; the Maker cannot clear them
- [ ] Packing List No is auto-generated and read-only
- [ ] All Order Reference fields (PO, LC, BL, SO, Other) are optional; each has a paired date field
- [ ] Notify Party is an optional dropdown from organisations tagged as "Notify Party"
- [ ] At least one container must be added before the form can be submitted
- [ ] Each container requires Net Weight and Tare Weight (numeric, 3 decimal places); Gross Weight is auto-calculated and read-only
- [ ] Each container must have at least one item before the form can be submitted
- [ ] Each item requires No & Kind of Packages, Description of Goods, and Quantity; HSN Code, Item Code, UOM, and Batch Details are optional
- [ ] If the Proforma Invoice, Exporter, Consignee, or any required container/item field is missing on submit, a validation error lists every issue and the form is not submitted
- [ ] On successful save, the packing list appears in the Packing List index with status Draft and the linked PI number is displayed

### US-09: Edit a Packing List
**As a** Maker, **I want to** edit a packing list in Draft or Rework status, **so that** I can correct errors or respond to a Checker's rejection comments before resubmitting.

**Acceptance Criteria:**
- [ ] Maker can reopen a Draft or Rework packing list via the same create/edit form
- [ ] All header, reference, shipping, container, and item fields are editable in Draft and Rework states
- [ ] Maker can add new containers, remove containers, add items, and remove items
- [ ] Maker can use "Copy Container" to duplicate an existing container's item list; the copy opens with a blank Container Reference, blank Marks & Numbers, and blank weights for the Maker to fill in
- [ ] Gross Weight continues to auto-calculate as Net + Tare whenever either weight field changes
- [ ] A packing list in Pending Approval or Approved state cannot be edited by the Maker
- [ ] Saving updates the existing record; the Packing List No does not change

### US-10: Submit a Packing List for Approval
**As a** Maker, **I want to** submit a completed packing list for approval, **so that** a Checker can verify the contents and weights before the document is finalised.

**Acceptance Criteria:**
- [ ] Maker can submit from the Packing List index using the "Submit for Approval" action when status is Draft
- [ ] Maker can re-submit using "Re-submit for Approval" when status is Rework
- [ ] Status changes to Pending Approval upon submission
- [ ] The Checker and Company Admin are notified of the pending review
- [ ] The submission event is recorded in the audit trail with actor name and timestamp
- [ ] The packing list becomes non-editable once submitted

### US-11: Approve, Reject, or Permanently Reject a Packing List
**As a** Checker, **I want to** approve, reject, or permanently reject a submitted packing list, **so that** only verified documents are finalised or closed out appropriately.

**Acceptance Criteria:**
- [ ] Checker can Approve a Pending Approval packing list; status changes to Approved
- [ ] Checker can Reject a Pending Approval packing list with mandatory comments; status changes to Rework; Maker is notified
- [ ] Checker or Company Admin can Permanently Reject a packing list; status changes to Permanently Rejected, which is a terminal state — no further submissions or edits are possible; a comment is mandatory
- [ ] All approval, rejection, and permanent rejection events are recorded in the audit trail with actor, timestamp, and comments
- [ ] A Maker cannot approve their own document

### US-12: Download Packing List PDF
**As a** Maker or Checker, **I want to** download the approved packing list as a print-ready PDF, **so that** it can be included in the shipment documents handed to the freight forwarder or customs.

**Acceptance Criteria:**
- [ ] "Download PDF" action is available for Maker and Checker only when the packing list status is Approved
- [ ] Company Admin can download the PDF at any workflow state
- [ ] The PDF includes: exporter details (corporate and registered office), consignee, buyer, notify party, all order references, shipping details, per-container blocks (weights + item table), grand total weights, and footer
- [ ] Weights are formatted to 3 decimal places
- [ ] Only references that have a value are printed (empty PO/LC/BL/SO/Other fields are omitted from the PDF)
- [ ] The PDF filename is derived from the Packing List number
- [ ] The PDF footer reads: "This is a computer-generated document. Signature is not required."

### US-13: Create a Commercial Invoice from an Approved Packing List
**As a** Maker, **I want to** create a commercial invoice using a 5-step wizard starting from an Approved Packing List, **so that** the invoice is directly tied to the shipment details without re-keying data.

**Acceptance Criteria:**
- [ ] The "Create Commercial Invoice" entry point is accessible only via the Commercial Invoice module; no standalone form exists
- [ ] Step 1 shows only consignees that have at least one Approved Packing List; consignees without Approved PLs are not shown
- [ ] Step 2 shows only Approved Packing Lists for the selected consignee; Maker cannot select a PL in any other state
- [ ] Step 3 displays aggregated line items: each row represents a unique Item Code + UOM combination summed across all containers of the selected PL; the Maker must enter a Rate (USD) for every row
- [ ] Amount (USD) per line item is auto-calculated as Total Quantity × Rate and updates in real time as the Maker types
- [ ] Maker cannot edit Item Code, Quantity, Description, HSN Code, or UOM — these are fixed from the Packing List
- [ ] Step 4 requires a bank to be selected; the Maker cannot proceed past Step 4 without selecting a bank
- [ ] Step 5 allows optional entry of FOB Rate, Freight, Insurance, and L/C Details
- [ ] On successful save, the Commercial Invoice is created in Draft status and appears in the CI index
- [ ] The linked Packing List number is associated with the created CI and the shipping/reference data from the PL is non-editable on the CI

### US-14: Submit a Commercial Invoice for Approval
**As a** Maker, **I want to** submit a Commercial Invoice for approval, **so that** a Checker can review and finalise it before it is used for customs clearance.

**Acceptance Criteria:**
- [ ] Maker can submit a CI from the index "Actions" menu when status is Draft or Rejected
- [ ] Status changes to Pending Approval upon submission
- [ ] The Checker and Company Admin are notified that a document awaits review
- [ ] The CI becomes non-editable once submitted
- [ ] The submission event is recorded in the audit trail with actor name and timestamp

### US-15: Approve or Reject a Commercial Invoice
**As a** Checker, **I want to** approve or reject a submitted commercial invoice, **so that** only verified documents are finalised for customs use.

**Acceptance Criteria:**
- [ ] Checker can Approve a Pending Approval CI; status changes to Approved and the document becomes fully read-only
- [ ] Checker cannot approve a CI in Rejected status directly; the Maker must re-submit it first (moving it to Pending Approval) before the Checker can act
- [ ] Checker can Reject a Pending Approval CI with mandatory rejection comments; status changes to Rejected; Maker is notified
- [ ] Maker can view the rejection comments via "View Rejection Comments" in the Actions menu when status is Rejected
- [ ] Approval and rejection events are recorded in the audit trail with actor name, timestamp, and comments
- [ ] A Maker cannot approve their own document

### US-16: Download a Commercial Invoice PDF
**As a** Maker or Checker, **I want to** download a Draft PDF during review and a Final PDF once approved, **so that** I can preview the document at any stage and produce the final clean copy for submission.

**Acceptance Criteria:**
- [ ] "Download Draft PDF" action is available to Maker when CI status is Draft or Rejected
- [ ] "Download Draft PDF" action is available to Company Admin at any non-Approved state
- [ ] The Draft PDF displays a diagonal "DRAFT" watermark in light red across all pages
- [ ] "Download Final PDF" action is available to Maker, Checker, and Company Admin only when status is Approved
- [ ] The Final PDF has no watermark
- [ ] Both PDF modes include: exporter details, consignee, buyer, all order references (only populated ones), shipping fields, line items table, weight totals, amounts, bank details
- [ ] Line item amounts are formatted to 2 decimal places; quantities are formatted to 3 decimal places
- [ ] The Total Amount in Words is correctly computed and displayed

### US-17: Disable an Approved Commercial Invoice
**As a** Checker, **I want to** disable an Approved Commercial Invoice, **so that** it can be voided after it has been finalised if required.

**Acceptance Criteria:**
- [ ] "Disable" action is available to Checker and Company Admin only when CI status is Approved
- [ ] A mandatory comment is required when disabling; the system must block the action if the comment is empty
- [ ] On confirmation, status changes to Disabled — a terminal state; no further actions (submit, approve, reject, or download) are possible
- [ ] The disable event is recorded in the audit trail with actor name, timestamp, and the mandatory comment
- [ ] A Maker cannot disable a CI

### US-06: Approve a Commercial Invoice
**As a** Checker, **I want to** review and approve a submitted commercial invoice, **so that** the trading house can use it for customs clearance and present it under a Letter of Credit.

**Acceptance Criteria:**
- [ ] Checker receives a notification when a document is submitted for approval
- [ ] Checker can view the complete document and its revision history
- [ ] Checker can approve the document, making it read-only and final
- [ ] Checker can reject the document with mandatory comments
- [ ] Maker is notified upon rejection and can view the Checker's comments

---

## 8. Data Requirements

- **Core Entities:** Organisation, User, Role, Bank, Country, Port, Place of Receipt, Incoterm, UOM, Payment Term, Final Destination, Pre-Carriage By, Terms & Conditions Template, Proforma Invoice, Proforma Invoice Line Item, Commercial Invoice, Commercial Invoice Line Item (aggregated from Packing List container items by Item Code + UOM; stores unit_price_usd), Packing List, Packing List Container, Packing List Container Item, Document Approval Log (Audit Trail)
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
| Bank Charges (USD) | If entered, must be ≥ 0. Max 2 decimal places. |
| Validity for Acceptance | If entered, must be a valid date. Must not be in the past at the time of entry. |
| Validity for Shipment | If entered, must be a valid date. If both Validity for Acceptance and Validity for Shipment are set, Validity for Shipment must be ≥ Validity for Acceptance. |

**On Line Item Add / Edit:**

| Field / Rule | Validation |
| --- | --- |
| Description of Goods | Required. |
| Quantity (MT) | Required. Must be > 0. Max 3 decimal places. |
| Rate (USD/MT) | Required. Must be > 0. Max 2 decimal places. |
| Amount (USD) | Calculated automatically as Quantity × Rate. Not directly editable. |

**On Submit for Approval:**

| Rule | Validation |
| --- | --- |
| All save-time validations above | Must all pass before submission is allowed. |
| Line items | At least one line item must be present. A Proforma Invoice with zero line items cannot be submitted. *(See Open Question #31)* |

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
| 31 | Should a Proforma Invoice be submittable for approval with zero line items (header only)? Or must at least one line item exist before submission is permitted? | Business | Open |
| 32 | If a Packing List is moved to Permanently Rejected or Disabled after a Commercial Invoice has been created from it, what should happen to the Commercial Invoice? Should it be automatically invalidated, or should it continue through its own workflow independently? | Business / Product | Open |
