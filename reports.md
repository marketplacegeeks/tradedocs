# Reports — TradeDocs

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-22

---

## 1. Overview

All reports are read-only views available to **Checker** and **Company Admin** roles. Makers do not have access to reports. Every report supports:

- **Date range filter** (applied to the document date unless noted otherwise)
- **Export to CSV** button on every report
- Default sort: newest document date first

Reports are built from existing document data — no new data entry is required.

---

## 2. Reports List

| # | Report Name | Primary Source | Purpose |
| --- | --- | --- | --- |
| R-01 | Document Register | PI + PL/CI + PO | Master log of all documents across all types |
| R-02 | Proforma Invoice Register | PI | Detailed record of all PIs |
| R-03 | Shipment Register | PL + CI | All shipments with weights, ports, and financials |
| R-04 | Commodity Sales Report | PI + CI line items | What goods are being sold, at what rates |
| R-05 | Consignee-wise Business Summary | PI + CI | Revenue and volume grouped by buyer |
| R-06 | Purchase Order Register | PO | Detailed record of all POs |
| R-07 | Vendor-wise Procurement Summary | PO | Spend and volume grouped by vendor |
| R-08 | Workflow Status Report | PI + PL/CI + PO | Documents currently pending or in a specific state |
| R-09 | Audit Trail Report | AuditLog | Full history of all status changes across all documents |

---

---

## R-02 — Proforma Invoice Register

**Purpose:** A detailed register of all Proforma Invoices. Used for sales tracking, follow-up on open PIs, and confirming shipment validity dates.

**Filters:**
- Date range (PI date)
- Status
- Exporter
- Consignee
- Country of Final Destination
- Incoterms
- Payment Terms

**Columns:**

| Column | Source | Notes |
| --- | --- | --- |
| PI Number | `pi_number` |  |
| PI Date | `pi_date` |  |
| Exporter | `exporter.name` |  |
| Consignee | `consignee.name` |  |
| Buyer | `buyer.name` | Blank if same as Consignee |
| Country of Origin | `country_of_origin.name` |  |
| Country of Destination | `country_of_final_destination.name` |  |
| Port of Loading | `port_of_loading.name` |  |
| Port of Discharge | `port_of_discharge.name` |  |
| Incoterms | `incoterms.code` |  |
| Payment Terms | `payment_terms.name` |  |
| Buyer Order No | `buyer_order_no` |  |
| Grand Total (USD) | Sum of line item amounts + additional charges | Before Incoterm cost breakdown |
| Invoice Total (USD) | `invoice_total_value` | After FOB / Freight / Insurance additions |
| Validity for Acceptance | `validity_for_acceptance` |  |
| Validity for Shipment | `validity_for_shipment` | Highlight in red if date has passed and PI is not yet Approved |
| Linked PL Number | `packinglist.pl_number` | Blank if no PL has been created from this PI yet |
| Status | `status` |  |
| Created By | `created_by.full_name` |  |

---

## R-03 — Shipment Register

**Purpose:** A record of every shipment (PL + CI pair). Used for tracking vessels, BL numbers, port routing, and invoice totals by shipment.

**Filters:**
- Date range (PL date)
- Status
- Consignee
- Port of Loading
- Port of Discharge
- Incoterms
- Payment Terms

**Columns:**

| Column | Source | Notes |
| --- | --- | --- |
| PL Number | `pl_number` |  |
| CI Number | `ci_number` |  |
| Linked PI Number | `proforma_invoice.pi_number` |  |
| PL Date | `pl_date` |  |
| CI Date | `ci_date` |  |
| Exporter | `exporter.name` |  |
| Consignee | `consignee.name` |  |
| Notify Party | `notify_party.name` | Blank if not set |
| Port of Loading | `port_of_loading.name` |  |
| Port of Discharge | `port_of_discharge.name` |  |
| Vessel / Flight No | `vessel_flight_no` |  |
| BL Number | `bl_number` | From Order References |
| BL Date | `bl_date` |  |
| Incoterms | `incoterms.code` |  |
| Payment Terms | `payment_terms.name` |  |
| Total Net Weight (MT) | Sum of all container item net weights | 3 decimal places |
| Total Gross Weight (MT) | Sum of all container gross weights | 3 decimal places |
| No. of Containers | Count of containers on the PL |  |
| CI Total (USD) | Sum of all CI line item amounts |  |
| FOB Value (USD) | `fob_rate × total_quantity` | Blank if Incoterm = EXW |
| Freight (USD) | `freight` | Blank if not seller-borne for selected Incoterm |
| Insurance (USD) | `insurance` | Blank if not seller-borne for selected Incoterm |
| Status | `status` | Single status covering both PL and CI |
| Created By | `created_by.full_name` |  |

---

## R-04 — Commodity Sales Report

**Purpose:** A line-item level breakdown of what goods are being sold, at what rates, and in what quantities. Used for HSN-wise analysis, pricing history, and commodity performance.

**Filters:**
- Date range (document date)
- Document Type: Proforma Invoice / Commercial Invoice (separate selection)
- HSN Code
- Item Code
- UOM
- Consignee
- Status (default: Approved only — but can be changed to All)

**Columns:**

| Column | Source | Notes |
| --- | --- | --- |
| Document Type | System | PI or CI |
| Document Number | `pi_number` or `ci_number` |  |
| Document Date | `pi_date` or `ci_date` |  |
| Status | `status` |  |
| Consignee | `consignee.name` |  |
| Country of Destination | `country_of_final_destination.name` |  |
| HSN Code | Line item `hsn_code` |  |
| Item Code | Line item `item_code` |  |
| Description of Goods | Line item `description` |  |
| Quantity | Line item `quantity` | 3 decimal places |
| UOM | Line item `uom.abbreviation` |  |
| Rate (USD) | Line item `rate_usd` | Per UOM |
| Amount (USD) | Line item `amount_usd` | Quantity × Rate |
| Incoterms | Document `incoterms.code` |  |
| Port of Loading | Document `port_of_loading.name` |  |

**Footer row (when filtered to a single document or item code):**
- Total Quantity, Total Amount (USD)

---
R-06 — Purchase Order Register

**Purpose:** A detailed register of all Purchase Orders. Used for procurement tracking and vendor management.

**Filters:**
- Date range (PO date)
- Status
- Vendor
- Currency
- Transaction Type (IGST / CGST+SGST / Zero-Rated)
- Internal Contact
- Country of Origin

**Columns:**

| Column | Source | Notes |
| --- | --- | --- |
| PO Number | `po_number` |  |
| PO Date | `po_date` |  |
| Vendor | `vendor.name` |  |
| Customer No. | `customer_no` | Vendor's reference for this buyer |
| Internal Contact | `internal_contact.full_name` |  |
| Delivery Address | `delivery_address` (city + country) | Short form |
| Currency | `currency.code` |  |
| Transaction Type | `transaction_type` | IGST / CGST+SGST / Zero-Rated |
| Payment Terms | `payment_terms.name` |  |
| Country of Origin | `country_of_origin.name` |  |
| Time of Delivery | `time_of_delivery` |  |
| No. of Line Items | Count of `line_items` |  |
| Total Taxable Amount | Sum of `line_item.taxable_amount` | Pre-tax |
| Total Tax | Sum of `line_item.total_tax` |  |
| Total (Currency) | Sum of `line_item.total` | In PO currency |
| Status | `status` |  |
| Created By | `created_by.full_name` |  |
