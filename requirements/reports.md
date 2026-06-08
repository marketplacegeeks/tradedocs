
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
| Buyer | `buyer.name` | Optional; the buying organisation issuing the PO |
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
| Total Taxable Amount | Sum of `line_item.taxable_amount` | Pre-tax, in PO currency |
| Total IGST | Sum of `line_item.igst_amount` | Blank for CGST+SGST and Zero-Rated POs |
| Total CGST | Sum of `line_item.cgst_amount` | Blank for IGST and Zero-Rated POs |
| Total SGST | Sum of `line_item.sgst_amount` | Blank for IGST and Zero-Rated POs |
| Total Tax | Sum of `line_item.total_tax` |  |
| Total (Currency) | Sum of `line_item.total` | In PO currency |
| Status | `status` |  |
| Created By | `created_by.full_name` |  |
