"""
# PROFORMA INVOICE PDF LAYOUT GUIDE (ASCII VISUAL + VARIABLE MAP)
# ============================================================================
# Generates a PROFORMA INVOICE / CUM SALES CONTRACT PDF using ReportLab
# Platypus Tables. Use this guide to understand every section's layout,
# column widths, and which model variable populates each cell.
#
# PAGE:
# - A4 portrait (210mm x 297mm)
# - Margins: left=15mm, right=15mm, top=10mm, bottom=15mm
# - Effective content width = 210 - 30 = 180mm
#
# WATERMARK (non-Approved documents — FR-08.3):
# - Diagonal "DRAFT" at 45°, Helvetica-Bold 80pt, alpha=0.07
# - Controlled by: is_draft = (invoice.status != APPROVED)
#
# FOOTER (every page):
# - Centered 8pt text: "This is a computer-generated document..."
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — DOCUMENT HEADER  (centered Paragraphs, no table)
# ─────────────────────────────────────────────────────────────────────────────
#   Variable         Source field
#   ───────────────  ────────────────────────────────
#   exp_name         invoice.exporter.name            (16pt bold, center)
#   "PROFORMA INVOICE CUM SALES CONTRACT"            (12pt bold, center)
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — MAIN INFO TABLE (top half)
# Total width = 180mm  |  4 columns: [36mm | 36mm | 54mm | 54mm]
# ─────────────────────────────────────────────────────────────────────────────
#
#   ┌──────────────────────────────────────────┬──────────────────────────────┬─────────────────────┐
#   │ Exporter:                                │ Proforma Invoice No & Date:  │ Buyer Order No      │  Row 0
#   │ exp_detail_html                          │ pi_number  &  pi_date        │ and Date:           │
#   │ (exp_name, exp_address, exp_country,     │ (col 2 standalone)           │ buyer_order_no &    │
#   │  exp_email — all from exporter.addresses)│                              │ buyer_order_date    │
#   │ (merged: col 0-1, rows 0-1)              ├──────────────────────────────┼─────────────────────┤
#   │                                          │ Country of Origin of Goods:  │ Country of Final    │  Row 1
#   │                                          │ origin_country               │ Destination:        │
#   │                                          │ (col 2 standalone)           │ final_country       │
#   │                                          │                              │ (col 3 standalone)  │
#   ├──────────────────────────────────────────┼──────────────────────────────┼─────────────────────┤
#   │ Consignee:                               │ Buyer if other than          │ Other reference(s): │  Row 2
#   │ consignee_details_html                   │ consignee:                   │ other_references    │
#   │ (cons_name, cons_address, cons_country,  │ buyer_details_html           │ (merged: col 3,     │
#   │  cons_email — via consignee.addresses)   │ (buyer_name, buyer_addr,     │  rows 2-3)          │
#   │ (merged: col 0-1, rows 2-3)              │  buyer_country, buyer_email) │                     │  Row 3
#   │                                          │ (merged: col 2, rows 2-3)    │ (continued)         │
#   └──────────────────────────────────────────┴──────────────────────────────┴─────────────────────┘
#        36mm (col 0)      36mm (col 1)              54mm (col 2)                54mm (col 3)
#                                                                                     Total = 180mm
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — MAIN INFO TABLE (bottom half)
# Total width = 180mm  |  5 equal columns: [36mm | 36mm | 36mm | 36mm | 36mm]
# ─────────────────────────────────────────────────────────────────────────────
#
#   ┌──────────────────┬──────────────────────────┬──────────────────┬──────────────────┬──────────────────┐
#   │ Pre-Carriaged By:│ Place of Receipt by       │ Vessel/Flight No:│ Incoterms:       │ Payment Terms:   │ Row 0
#   │ pre_carriage     │ Pre-Carrier:              │ invoice.vessel_  │ incoterm_disp    │ payment_term_    │
#   │ (pre_carriage_by │ por_pre                   │ flight_no        │ (incoterms.code) │ name             │
#   │  .name)          │ (place_of_receipt_by_     │                  │                  │ (payment_terms   │
#   │                  │  pre_carrier.name)        │                  │                  │  .name)          │
#   ├──────────────────┼──────────────────────────┼──────────────────┼──────────────────┼──────────────────┤
#   │ Port of Loading: │ Port of Discharge:        │ Final            │ Marks & Nos /    │ No & Kind of     │ Row 1
#   │ port_loading     │ port_discharge            │ Destination:     │ Container No     │ Packages         │
#   │ (port_of_loading │ (port_of_discharge        │ final_dest       │ (blank — no      │ (blank — no      │
#   │  .name)          │  .name)                   │ (final_          │  model field)    │  model field)    │
#   │                  │                           │ destination.name)│                  │                  │
#   └──────────────────┴──────────────────────────┴──────────────────┴──────────────────┴──────────────────┘
#        36mm                   36mm                    36mm               36mm               36mm
#                                                                                     Total = 180mm
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — LINE ITEMS TABLE
# Total width = 180mm  |  7 columns: [10 | 24 | 24 | 50 | 22 | 26 | 24] mm
# repeatRows=1 → header repeats on page break
# ─────────────────────────────────────────────────────────────────────────────
#
#   ┌──────┬──────────┬──────────┬──────────────────────────────┬────────────┬───────────┬────────────┐
#   │ Sr.  │ HSN Code │ Item Code│ Description of Goods         │ Qty        │ Rate (USD)│ Amount(USD)│ Header
#   ├──────┼──────────┼──────────┼──────────────────────────────┼────────────┼───────────┼────────────┤
#   │ idx  │ it.hsn_  │ it.item_ │ it.description               │ it.quantity│ it.rate_  │ it.amount_ │ Row N
#   │      │ code     │ code     │                              │ + uom_disp │ usd       │ usd        │
#   │      │          │          │                              │ (uom.abbrev│           │            │
#   │      │          │          │                              │ iation)    │ RIGHT-    │ RIGHT-     │
#   │      │          │          │                              │ RIGHT-ALIGN│ ALIGNED   │ ALIGNED    │
#   └──────┴──────────┴──────────┴──────────────────────────────┴────────────┴───────────┴────────────┘
#     10mm    24mm       24mm              50mm                     22mm        26mm        24mm
#                                                          total_amount_usd = sum(it.amount_usd)
#                                                                                     Total = 180mm
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — TOTALS ROW
# Total width = 180mm  |  3 columns: [100mm | 40mm | 40mm]
# ─────────────────────────────────────────────────────────────────────────────
#
#   ┌────────────────────────────────────────────────────────────────┬──────────────────┬──────────────────┐
#   │ Amount Chargeable in: USD                                      │ Total            │ $total_amount_usd│
#   └────────────────────────────────────────────────────────────────┴──────────────────┴──────────────────┘
#                100mm                                                      40mm               40mm
#                                                                                     Total = 180mm
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — AMOUNT IN WORDS  (single Paragraph, full width)
# ─────────────────────────────────────────────────────────────────────────────
#   Variable           Source
#   ─────────────────  ──────────────────────────────────
#   total_amount_usd   computed from sum of line item amount_usd values
#   → amount_to_words(total_amount_usd)  e.g. "One Thousand Two Hundred USD Only"
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — VALIDITY & SHIPMENT TABLE
# Total width = 180mm  |  1 column: [180mm]  |  4 rows
# ─────────────────────────────────────────────────────────────────────────────
#
#   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
#   │ Validity for Acceptance: invoice.validity_for_acceptance                                           │ Row 0
#   ├────────────────────────────────────────────────────────────────────────────────────────────────────┤
#   │ Validity for Shipment:   invoice.validity_for_shipment                                             │ Row 1
#   ├────────────────────────────────────────────────────────────────────────────────────────────────────┤
#   │ Partial Shipment:        bool_yn(invoice.partial_shipment)  → "Yes" / "No"                        │ Row 2
#   │                          (CharField: "ALLOWED" → "Yes", "NOT_ALLOWED" → "No")                     │
#   ├────────────────────────────────────────────────────────────────────────────────────────────────────┤
#   │ Transshipment:           bool_yn(invoice.transshipment)     → "Yes" / "No"                        │ Row 3
#   └────────────────────────────────────────────────────────────────────────────────────────────────────┘
#                                            180mm                                       Total = 180mm
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — MT103 ADVISORY + DECLARATION  (plain Paragraphs, full width)
# ─────────────────────────────────────────────────────────────────────────────
#   Static text — no model variables.
#   Line 1: MT103 payment tracing instruction.
#   Line 2: Declaration of invoice accuracy.
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — BANK DETAILS  (conditional: only if invoice.bank is set)
# Total width = 180mm  |  2 columns: [60mm label | 120mm value]
# Three sub-sections printed as separate tables, each with a grey header row.
# Optional fields (swift, iban, routing_number, ad_code) only printed when non-empty.
# Intermediary Bank sub-section only printed when intermediary_bank_name is set.
# ─────────────────────────────────────────────────────────────────────────────
#
#   Sub-section 1 — BENEFICIARY DETAILS (always shown)
#   ┌──────────────────────┬──────────────────────────────────────────────────┐
#   │ BENEFICIARY DETAILS (merged header, grey background)                   │
#   ├──────────────────────┼──────────────────────────────────────────────────┤
#   │ Beneficiary Name     │ bank.beneficiary_name                            │
#   │ Bank Name            │ bank.bank_name                                   │
#   │ Bank Country         │ bank.bank_country.name                           │
#   │ Branch Name          │ bank.branch_name                                 │
#   │ Branch Address       │ bank.branch_address                              │
#   │ Account No.          │ bank.account_number                              │
#   │ Account Type         │ bank.account_type  (Current/Savings/Checking)    │
#   │ Currency             │ bank.currency.code                               │
#   └──────────────────────┴──────────────────────────────────────────────────┘
#
#   Sub-section 2 — ROUTING & IDENTIFIERS (shown if any field is non-empty)
#   ┌──────────────────────┬──────────────────────────────────────────────────┐
#   │ ROUTING & IDENTIFIERS (merged header, grey background)                 │
#   ├──────────────────────┼──────────────────────────────────────────────────┤
#   │ SWIFT / BIC Code     │ bank.swift_code          (if set)                │
#   │ IBAN                 │ bank.iban                (if set)                │
#   │ Routing No. / IFSC   │ bank.routing_number      (if set)                │
#   │ AD Code              │ bank.ad_code             (if set)                │
#   └──────────────────────┴──────────────────────────────────────────────────┘
#
#   Sub-section 3 — INTERMEDIARY BANK (shown only when intermediary_bank_name is set)
#   ┌──────────────────────┬──────────────────────────────────────────────────┐
#   │ INTERMEDIARY BANK (merged header, grey background)                     │
#   ├──────────────────────┼──────────────────────────────────────────────────┤
#   │ Bank Name            │ bank.intermediary_bank_name                      │
#   │ Account No.          │ bank.intermediary_account_number                 │
#   │ SWIFT / BIC Code     │ bank.intermediary_swift_code                     │
#   │ Currency             │ bank.intermediary_currency.code                  │
#   └──────────────────────┴──────────────────────────────────────────────────┘
#       60mm label                   120mm value                  Total = 180mm
#   Variable: bank = invoice.bank (FK → Bank model)
#
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10 — TERMS & CONDITIONS  (conditional: only if invoice.tc_content set)
# Starts on a new page. Full width Paragraphs.
# ─────────────────────────────────────────────────────────────────────────────
#   Variable    Source
#   ──────────  ──────────────────────────────────────────────────────────────
#   tc_content  invoice.tc_content  (Tiptap HTML → stripped via strip_html())
#               Split on double-newlines → individual Paragraph flowables
#
# HOW TO MODIFY:
# - Change table widths via colWidths lists (keep total = 180mm).
# - Adjust cell padding via TableStyle LEFT/RIGHT/TOP/BOTTOMPADDING.
# - Change font/size via ParagraphStyle (style_text, style_label, style_small).
# - Watermark threshold: change APPROVED import in add_footer().
# - Bank section: conditionally rendered — check `if bank:` block (~line 542).
# - T&C section:  conditionally rendered — check `if tc_content.strip():` block.
#
# FIELD MAPPING (pdf1/ reference name → actual Django model field):
#   invoice.number                    → invoice.pi_number
#   invoice.date                      → invoice.pi_date
#   invoice.incoterm.code             → invoice.incoterms.code       (FK: 'incoterms')
#   invoice.payment_term.name         → invoice.payment_terms.name   (FK: 'payment_terms')
#   invoice.port_loading.name         → invoice.port_of_loading.name
#   invoice.port_discharge.name       → invoice.port_of_discharge.name
#   invoice.pre_carriage.name         → invoice.pre_carriage_by.name
#   invoice.marks_and_nos             → (no model field — cell left blank)
#   invoice.kind_of_packages          → (no model field — cell left blank)
#   invoice.bank_charges              → (no model field — omitted)
#   invoice.terms_and_conditions      → invoice.tc_content
#   invoice.partial_shipment          → CharField "ALLOWED"/"NOT_ALLOWED"
#   invoice.transshipment             → CharField "ALLOWED"/"NOT_ALLOWED"
#   invoice.total_amount_usd          → computed: sum(li.amount_usd)
#   it.hs_code                        → it.hsn_code
#   it.unit_price_usd                 → it.rate_usd
#   it.uom (string)                   → it.uom.abbreviation  (UOM FK)
#   line_items.filter(is_active=True) → .all()  (no is_active on ProformaInvoiceLineItem)
#   exp.address / exp.email_id        → org.addresses relation helpers
# ============================================================================

Constraint #20: generate_proforma_invoice_pdf_bytes() returns bytes in-memory — never
writes to disk.
"""
import re
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe(v: Any, default: str = "") -> str:
    return default if v is None else str(v)


def fmt_money(v: Any) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return safe(v)


def fmt_qty(v: Any) -> str:
    try:
        return f"{float(v):,.3f}"
    except Exception:
        return safe(v)


def amount_to_words(n: Any, currency: str = "USD") -> str:
    try:
        from num2words import num2words
        n = int(float(n or 0))
        words = num2words(n).title()
        return f"{words} {currency} Only"
    except Exception:
        return ""


def bool_yn(v: Any) -> str:
    """Convert 'ALLOWED'/'NOT_ALLOWED' CharField or boolean to 'Yes'/'No'."""
    if isinstance(v, str):
        return "Yes" if v.upper() == "ALLOWED" else "No"
    try:
        return "Yes" if bool(v) else "No"
    except Exception:
        return "No"


# ---------------------------------------------------------------------------
# Organisation address helpers
# (Organisation has no direct address/email fields; go via .addresses relation)
# ---------------------------------------------------------------------------

def _org_address_str(org) -> str:
    """Return a single comma-joined address string from the Organisation's first address."""
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        if not addr:
            return ""
        parts = []
        if addr.line1:
            parts.append(addr.line1)
        if addr.line2:
            parts.append(addr.line2)
        city_state = ", ".join(filter(None, [addr.city, addr.state]))
        if city_state:
            parts.append(city_state)
        if getattr(addr, "pin", ""):
            parts.append(addr.pin)
        if getattr(addr, "country", None):
            parts.append(addr.country.name)
        return ", ".join(parts)
    except Exception:
        return ""


def _org_email(org) -> str:
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        return addr.email if addr else ""
    except Exception:
        return ""


def _org_country_name(org) -> str:
    """Return country name from the Organisation's first address."""
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        if addr and getattr(addr, "country", None):
            return addr.country.name
        return ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main PDF generation function
# ---------------------------------------------------------------------------

def generate_proforma_invoice_pdf_bytes(invoice) -> bytes:
    """
    Build Proforma Invoice PDF bytes matching the pdf1/ reference layout,
    with all field names mapped to the actual Django model.

    Constraint #20: built entirely in-memory; never written to disk.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "PICompanyHeader", parent=styles["Normal"],
        fontSize=16, leading=20, spaceAfter=6,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "PITitle", parent=styles["Normal"],
        fontSize=12, leading=15, spaceAfter=12,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "PILabel", parent=styles["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "PIText", parent=styles["Normal"],
        fontSize=9, leading=11,
    )
    style_small = ParagraphStyle(
        "PISmall", parent=styles["Normal"],
        fontSize=8, leading=10,
    )

    # Determine if this is a non-approved document (needs DRAFT watermark, FR-08.3)
    from apps.workflow.constants import APPROVED
    is_draft = getattr(invoice, "status", None) != APPROVED

    def add_footer(canvas, _doc):
        # Draw faint diagonal DRAFT watermark on non-approved documents (FR-08.3).
        # alpha=0.07 produces the '/ca .07' ExtGState entry that tests check for.
        if is_draft:
            from reportlab.lib.colors import HexColor
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 80)
            # alpha=0.07 produces the '/ca .07' ExtGState entry the test checks for.
            canvas.setFillColor(HexColor('#CC1A1A'), alpha=0.07)
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DRAFT")
            canvas.restoreState()
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            "This is a computer-generated document. Signature is not required.",
        )
        canvas.restoreState()

    story = []

    # ---- Data extraction -------------------------------------------------------
    exp = invoice.exporter
    cons = invoice.consignee

    # Country names — sourced from Organisation's first address
    origin_country = _org_country_name(exp)
    final_dest_obj = getattr(invoice, "country_of_final_destination", None)
    final_country = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""

    # Consignee address for the main table
    cons_name = safe(getattr(cons, "name", ""))
    cons_address = _org_address_str(cons)
    cons_email = _org_email(cons)
    cons_country = _org_country_name(cons)

    address_parts = []
    if cons_address:
        address_parts.append(cons_address)
    if cons_country:
        address_parts.append(cons_country)
    address_line = ", ".join(address_parts)

    cons_lines = [x for x in [cons_name, address_line, cons_email] if x]
    consignee_details_html = "<br/>".join(cons_lines)

    # Incoterms & payment terms — FK field names are 'incoterms' and 'payment_terms'
    incoterm_obj = getattr(invoice, "incoterms", None)
    incoterm_disp = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""

    payment_term_obj = getattr(invoice, "payment_terms", None)
    payment_term_name = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""

    # Port and carriage — FK field names differ from pdf1/ reference
    port_of_loading_obj = getattr(invoice, "port_of_loading", None)
    port_loading = safe(getattr(port_of_loading_obj, "name", "")) if port_of_loading_obj else ""

    port_of_discharge_obj = getattr(invoice, "port_of_discharge", None)
    port_discharge = safe(getattr(port_of_discharge_obj, "name", "")) if port_of_discharge_obj else ""

    final_dest_location_obj = getattr(invoice, "final_destination", None)
    final_dest = safe(getattr(final_dest_location_obj, "name", "")) if final_dest_location_obj else ""

    pre_carriage_obj = getattr(invoice, "pre_carriage_by", None)
    pre_carriage = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""

    por_pre_obj = getattr(invoice, "place_of_receipt_by_pre_carrier", None)
    por_pre = safe(getattr(por_pre_obj, "name", "")) if por_pre_obj else ""

    bank = getattr(invoice, "bank", None)

    # Exporter details for the summary table
    exp_name = safe(getattr(exp, "name", ""))
    exp_address = _org_address_str(exp)
    exp_email = _org_email(exp)
    exp_iec = safe(getattr(exp, "iec_code", ""))
    exp_country = _org_country_name(exp)

    exp_detail_parts = []
    if exp_address:
        exp_detail_parts.append(exp_address)
    if exp_country:
        exp_detail_parts.append(exp_country)
    if exp_email:
        exp_detail_parts.append(exp_email)
    exp_detail_html = "<br/>".join([exp_name] + exp_detail_parts)

    # PI number and date — actual field names are pi_number and pi_date
    pi_number = safe(getattr(invoice, "pi_number", ""))
    pi_date = safe(getattr(invoice, "pi_date", ""))
    buyer_order_no = safe(getattr(invoice, "buyer_order_no", ""))
    buyer_order_date = safe(getattr(invoice, "buyer_order_date", ""))
    other_references = safe(getattr(invoice, "other_references", ""))

    # ---- Document header -------------------------------------------------------
    story.append(Paragraph(exp_name, style_company_header))
    story.append(Paragraph("PROFORMA INVOICE CUM SALES CONTRACT", style_title))
    story.append(Spacer(1, 8))

    # ---- Main information table (4 rows, 4 columns) ---------------------------
    #
    # Visual layout:
    #   Col 0-1 (rows 0-1): Exporter block (merged)
    #   Col 2   (row 0):    PI No & Date
    #   Col 3   (row 0):    Buyer Order No and Date
    #   Col 2   (row 1):    Country of Origin of Goods
    #   Col 3   (row 1):    Country of Final Destination
    #   Col 0-1 (rows 2-3): Consignee block (merged)
    #   Col 2   (rows 2-3): Buyer if other than consignee (merged vertically)
    #   Col 3   (rows 2-3): Other reference(s) (merged vertically)
    #
    buyer_obj = getattr(invoice, "buyer", None)
    buyer_name = safe(getattr(buyer_obj, "name", "")) if buyer_obj else cons_name

    # Build full buyer details (name + address + country + email)
    if buyer_obj:
        buyer_address = _org_address_str(buyer_obj)
        buyer_email = _org_email(buyer_obj)
        buyer_country = _org_country_name(buyer_obj)
        buyer_addr_parts = []
        if buyer_address:
            buyer_addr_parts.append(buyer_address)
        if buyer_country:
            buyer_addr_parts.append(buyer_country)
        buyer_addr_line = ", ".join(buyer_addr_parts)
        buyer_lines = [x for x in [buyer_name, buyer_addr_line, buyer_email] if x]
        buyer_details_html = "<br/>".join(buyer_lines)
    else:
        buyer_details_html = cons_name  # fallback: same as consignee

    main_info_data = [
        # Row 0
        [
            Paragraph(f"<b>Exporter:</b><br/>{exp_detail_html}", style_text),
            "",
            Paragraph(
                f"<b>Proforma Invoice No &amp; Date:</b><br/>{pi_number} &amp; {pi_date}",
                style_text,
            ),
            Paragraph(
                f"<b>Buyer Order No and Date:</b><br/>{buyer_order_no} &amp; {buyer_order_date}",
                style_text,
            ),
        ],
        # Row 1
        [
            "", "",
            Paragraph(f"<b>Country of Origin of Goods:</b><br/>{origin_country}", style_text),
            Paragraph(f"<b>Country of Final Destination:</b><br/>{final_country}", style_text),
        ],
        # Row 2
        [
            Paragraph(f"<b>Consignee:</b><br/>{consignee_details_html}", style_text),
            "",
            Paragraph(f"<b>Buyer if other than consignee</b><br/>{buyer_details_html}", style_text),
            Paragraph(f"<b>Other reference(s):</b><br/>{other_references}", style_text),
        ],
        # Row 3
        [
            "", "", "", "",
        ],
    ]

    main_info_table_top = Table(
        main_info_data,
        colWidths=[36 * mm, 36 * mm, 54 * mm, 54 * mm],
    )
    main_info_table_top.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        # Merge: Exporter block col 0-1, rows 0-1
        ("SPAN",         (0, 0), (1, 1)),
        # Col 2 row 0: PI No & Date (standalone); col 3 row 0: Buyer Order (standalone)
        # Row 1 col 2: Country of Origin (standalone); col 3: Country of Final Destination (standalone)
        # Merge: Consignee col 0-1, rows 2-3
        ("SPAN",         (0, 2), (1, 3)),
        # Merge: Buyer col 2 only, rows 2-3
        ("SPAN",         (2, 2), (2, 3)),
        # Merge: Other References col 3 only, rows 2-3
        ("SPAN",         (3, 2), (3, 3)),
    ]))

    # Second table (rows 6-7 in reference): Pre-carriage / Vessel / Ports
    #   Row 0: Pre-Carriage | Place of Receipt | Vessel/Flight | Incoterms | Payment Terms
    #   Row 1: Port of Loading | Port of Discharge | Final Destination | Marks | Packages
    # The model has no marks_and_nos or kind_of_packages fields, so those cells are blank.
    main_info_data_bottom = [
        [
            Paragraph(f"<b>Pre-Carriaged By:</b><br/>{pre_carriage}", style_text),
            Paragraph(f"<b>Place of Receipt by Pre-Carrier:</b><br/>{por_pre}", style_text),
            Paragraph(f"<b>Vessel/Flight No:</b><br/>{safe(invoice.vessel_flight_no)}", style_text),
            Paragraph(f"<b>Incoterms:</b><br/>{incoterm_disp}", style_text),
            Paragraph(f"<b>Payment Terms:</b><br/>{payment_term_name}", style_text),
        ],
        [
            Paragraph(f"<b>Port of Loading:</b><br/>{port_loading}", style_text),
            Paragraph(f"<b>Port of Discharge:</b><br/>{port_discharge}", style_text),
            Paragraph(f"<b>Final Destination:</b><br/>{final_dest}", style_text),
            Paragraph("<b>Marks &amp; Nos/Container No</b><br/>", style_text),
            Paragraph("<b>No &amp; Kind of Packages</b><br/>", style_text),
        ],
    ]
    main_info_table_bottom = Table(
        main_info_data_bottom,
        colWidths=[36 * mm, 36 * mm, 36 * mm, 36 * mm, 36 * mm],
    )
    main_info_table_bottom.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))

    story.append(main_info_table_top)
    story.append(main_info_table_bottom)
    story.append(Spacer(1, 10))

    # ---- Line items table -----------------------------------------------------
    li_header = [
        Paragraph("<b>Sr.</b>", style_label),
        Paragraph("<b>HSN Code</b>", style_label),
        Paragraph("<b>Item Code</b>", style_label),
        Paragraph("<b>Description of Goods</b>", style_label),
        Paragraph("<b>Qty</b>", style_label),
        Paragraph("<b>Rate (USD)</b>", style_label),
        Paragraph("<b>Amount (USD)</b>", style_label),
    ]
    li_rows = [li_header]
    total_amount_usd = Decimal("0.00")

    # ProformaInvoiceLineItem has no is_active field; query with .all()
    for idx, it in enumerate(invoice.line_items.all().order_by("id"), start=1):
        uom_obj = getattr(it, "uom", None)
        uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
        amount = getattr(it, "amount_usd", None)
        if amount is not None:
            try:
                total_amount_usd += Decimal(str(amount))
            except Exception:
                pass
        li_rows.append([
            Paragraph(str(idx), style_text),
            Paragraph(safe(it.hsn_code), style_text),    # hsn_code (not hs_code)
            Paragraph(safe(it.item_code), style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{fmt_qty(it.quantity)} {uom_display}".strip(), style_text),
            Paragraph(fmt_money(it.rate_usd), style_text),   # rate_usd (not unit_price_usd)
            Paragraph(fmt_money(amount), style_text),
        ])

    # Col widths: 10+24+24+50+22+26+24 = 180mm
    li_table = Table(
        li_rows,
        colWidths=[10 * mm, 24 * mm, 24 * mm, 50 * mm, 22 * mm, 26 * mm, 24 * mm],
    )
    li_table.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND",   (0, 0), (-1, 0), colors.white),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (4, 1), (6, -1), "RIGHT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 10))

    # ---- Totals section -------------------------------------------------------
    # Mirrors the on-screen totals card exactly:
    #   - Additional charges breakdown (when charges exist and no cost breakdown)
    #   - Grand Total Amount (when no incoterm is set)
    #   - Cost Breakdown with FOB Value + seller-borne fields (for non-EXW incoterms)
    #   - Invoice Total (Amount Payable) (whenever an incoterm is set)

    # Compute charges total
    charges_list = list(invoice.charges.all().order_by("id"))
    charges_total = Decimal("0.00")
    for charge in charges_list:
        charges_total += Decimal(str(charge.amount_usd or 0))

    # FOB Value = line items + additional charges
    grand_total = total_amount_usd + charges_total

    # Incoterm seller fields map (matches frontend INCOTERM_SELLER_FIELDS)
    _SELLER_FIELDS = {
        "EXW": [],
        "FCA": [],
        "FOB": [],
        "CFR": ["freight"],
        "CPT": ["freight"],
        "CIF": ["freight", "insurance_amount"],
        "CIP": ["freight", "insurance_amount"],
        "DAP": ["freight", "insurance_amount"],
        "DPU": ["freight", "insurance_amount", "destination_charges"],
        "DDP": ["freight", "insurance_amount", "import_duty", "destination_charges"],
    }
    _FIELD_LABELS = {
        "freight":             "Freight",
        "insurance_amount":    "Insurance Amount",
        "import_duty":         "Import Duty",
        "destination_charges": "Destination Charges",
    }
    seller_fields = _SELLER_FIELDS.get(incoterm_disp, [])
    show_cost_breakdown = bool(incoterm_disp) and incoterm_disp != "EXW"

    # Compute invoice total = grand_total + applicable seller-borne fields
    invoice_total_pdf = grand_total
    for field in seller_fields:
        val = getattr(invoice, field, None)
        if val is not None:
            try:
                invoice_total_pdf += Decimal(str(val))
            except Exception:
                pass

    # The amount used for "Amount in Words" is the final payable total
    final_total = invoice_total_pdf if incoterm_disp else grand_total

    # Build rows: [label | value], right-align value column
    totals_rows = []

    # Item Total + each charge (only when charges exist and no cost breakdown section)
    if charges_list and not show_cost_breakdown:
        totals_rows.append([
            Paragraph("Item Total", style_text),
            Paragraph(f"${fmt_money(total_amount_usd)}", style_text),
        ])
        for charge in charges_list:
            totals_rows.append([
                Paragraph(safe(charge.description), style_text),
                Paragraph(f"${fmt_money(charge.amount_usd)}", style_text),
            ])

    # Grand Total Amount — only when no incoterm is set
    if not incoterm_disp:
        totals_rows.append([
            Paragraph("<b>Grand Total Amount</b>", style_label),
            Paragraph(f"<b>${fmt_money(grand_total)}</b>", style_label),
        ])

    # Cost Breakdown section — for all incoterms except EXW
    if show_cost_breakdown:
        totals_rows.append([
            Paragraph(f"<b>Cost Breakdown ({incoterm_disp})</b>", style_label),
            Paragraph("", style_text),
        ])
        totals_rows.append([
            Paragraph("FOB Value", style_text),
            Paragraph(f"${fmt_money(grand_total)}", style_text),
        ])
        for field in seller_fields:
            val = getattr(invoice, field, None)
            val_str = f"${fmt_money(val)}" if val is not None else "—"
            totals_rows.append([
                Paragraph(_FIELD_LABELS.get(field, field), style_text),
                Paragraph(val_str, style_text),
            ])

    # Invoice Total (Amount Payable) — shown whenever an incoterm is selected
    if incoterm_disp:
        totals_rows.append([
            Paragraph("<b>Invoice Total (Amount Payable)</b>", style_label),
            Paragraph(f"<b>${fmt_money(invoice_total_pdf)}</b>", style_label),
        ])

    if totals_rows:
        totals_table = Table(totals_rows, colWidths=[140 * mm, 40 * mm])
        totals_table.setStyle(TableStyle([
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",         (1, 0), (1, -1),  "RIGHT"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 4))

    # Amount in words — reflects the final payable total
    story.append(Paragraph(
        f"<b>Amount in Words:</b> {amount_to_words(final_total, currency='USD')}",
        style_text,
    ))
    story.append(Spacer(1, 10))

    # ---- Validity and terms table ---------------------------------------------
    # partial_shipment / transshipment are CharFields: "ALLOWED" / "NOT_ALLOWED"
    validity_data = [
        [Paragraph(
            f"<b>Validity for Acceptance:</b> {safe(invoice.validity_for_acceptance)}",
            style_text,
        )],
        [Paragraph(
            f"<b>Validity for Shipment:</b> {safe(invoice.validity_for_shipment)}",
            style_text,
        )],
        [Paragraph(
            f"<b>Partial Shipment:</b> {bool_yn(invoice.partial_shipment)}",
            style_text,
        )],
        [Paragraph(
            f"<b>Transshipment:</b> {bool_yn(invoice.transshipment)}",
            style_text,
        )],
    ]
    validity_table = Table(validity_data, colWidths=[180 * mm])
    validity_table.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(validity_table)
    story.append(Spacer(1, 10))

    # ---- MT103 advisory + declaration -----------------------------------------
    story.append(Paragraph(
        "Request your bank to send MT 103 Message to our bank and send us copy of this "
        "message to trace &amp; claim the payment from our bank.",
        style_text,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Declaration:</b> We declare that this invoice shows the actual price of the "
        "goods described and that all particulars are true and correct.",
        style_text,
    ))
    story.append(Spacer(1, 10))

    # ---- Bank details ---------------------------------------------------------
    # Printed in three sections matching the Bank model structure:
    #   1. Beneficiary Details  — always shown
    #   2. Routing & Identifiers — optional fields shown only when non-empty
    #   3. Intermediary Bank    — shown only when intermediary_bank_name is set
    # Layout: 2 columns [label 60mm | value 120mm] = 180mm total.
    if bank:
        bank_style = TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ])

        def _bank_row(label, value):
            return [
                Paragraph(f"<b>{label}</b>", style_label),
                Paragraph(safe(value), style_text),
            ]

        # Section 1: Beneficiary Details (all fields always present on the model)
        bank_country_name = safe(getattr(bank.bank_country, "name", "")) if getattr(bank, "bank_country", None) else ""
        currency_code = safe(getattr(bank.currency, "code", "")) if getattr(bank, "currency", None) else ""
        account_type_display = safe(bank.account_type).title() if bank.account_type else ""

        beneficiary_data = [
            [Paragraph("<b>BENEFICIARY DETAILS</b>", style_label), Paragraph("", style_text)],
            _bank_row("Beneficiary Name",  bank.beneficiary_name),
            _bank_row("Bank Name",         bank.bank_name),
            _bank_row("Bank Country",      bank_country_name),
            _bank_row("Branch Name",       bank.branch_name),
            _bank_row("Branch Address",    bank.branch_address),
            _bank_row("Account No.",       bank.account_number),
            _bank_row("Account Type",      account_type_display),
            _bank_row("Currency",          currency_code),
        ]
        beneficiary_table = Table(beneficiary_data, colWidths=[60 * mm, 120 * mm])
        beneficiary_table.setStyle(TableStyle([
            *bank_style._cmds,
            # Section header spans both columns
            ("SPAN",       (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (1, 0), colors.lightgrey),
        ]))
        story.append(beneficiary_table)
        story.append(Spacer(1, 4))

        # Section 2: Routing & Identifiers — only rows with a saved value
        routing_rows = [
            [Paragraph("<b>ROUTING &amp; IDENTIFIERS</b>", style_label), Paragraph("", style_text)],
        ]
        if bank.swift_code:
            routing_rows.append(_bank_row("SWIFT / BIC Code", bank.swift_code))
        if bank.iban:
            routing_rows.append(_bank_row("IBAN", bank.iban))
        if bank.routing_number:
            routing_rows.append(_bank_row("Routing No. / IFSC", bank.routing_number))
        if bank.ad_code:
            routing_rows.append(_bank_row("AD Code", bank.ad_code))

        if len(routing_rows) > 1:  # at least one identifier field is set
            routing_table = Table(routing_rows, colWidths=[60 * mm, 120 * mm])
            routing_table.setStyle(TableStyle([
                *bank_style._cmds,
                ("SPAN",       (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (1, 0), colors.lightgrey),
            ]))
            story.append(routing_table)
            story.append(Spacer(1, 4))

        # Section 3: Intermediary Bank — only when all four fields are saved
        if safe(bank.intermediary_bank_name):
            intermediary_currency_code = (
                safe(getattr(bank.intermediary_currency, "code", ""))
                if getattr(bank, "intermediary_currency", None) else ""
            )
            intermediary_data = [
                [Paragraph("<b>INTERMEDIARY BANK</b>", style_label), Paragraph("", style_text)],
                _bank_row("Bank Name",       bank.intermediary_bank_name),
                _bank_row("Account No.",     bank.intermediary_account_number),
                _bank_row("SWIFT / BIC Code", bank.intermediary_swift_code),
                _bank_row("Currency",        intermediary_currency_code),
            ]
            intermediary_table = Table(intermediary_data, colWidths=[60 * mm, 120 * mm])
            intermediary_table.setStyle(TableStyle([
                *bank_style._cmds,
                ("SPAN",       (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (1, 0), colors.lightgrey),
            ]))
            story.append(intermediary_table)
            story.append(Spacer(1, 4))

        story.append(Spacer(1, 6))

    # ---- Terms & Conditions (new page) ----------------------------------------
    # The actual field is tc_content (not terms_and_conditions).
    # Use strip_html() from pdf.utils so Tiptap HTML (paragraphs, lists, bold, etc.)
    # is converted to plain text with double-newline paragraph breaks, then render
    # each paragraph as a separate Paragraph flowable — matching the original layout.
    tc_content = getattr(invoice, "tc_content", "") or ""
    if tc_content.strip():
        from pdf.utils import strip_html
        story.append(PageBreak())
        story.append(Paragraph("<b>Additional Terms &amp; Conditions</b>", style_label))
        story.append(Spacer(1, 6))

        plain = strip_html(tc_content)
        for para in plain.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, style_small))
                story.append(Spacer(1, 4))

    # ---- Build the PDF --------------------------------------------------------
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
