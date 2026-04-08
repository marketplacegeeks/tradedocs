"""
Proforma Invoice PDF Generator

Generates professional Proforma Invoice / Cum Sales Contract PDFs using ReportLab.
Constraint #20: Returns bytes in-memory — never writes to disk.
"""
import re
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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


# ============================================================================
# CONSTANTS & UTILITIES
# ============================================================================

def safe(v: Any, default: str = "") -> str:
    """Safely convert value to string."""
    return default if v is None else str(v)


def fmt_money(v: Any) -> str:
    """Format number as money with comma separators and exactly 2 decimal places."""
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return safe(v)


def fmt_qty(v: Any) -> str:
    """Format quantity with 3 decimal places."""
    try:
        s = f"{float(v):,.3f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    except Exception:
        return safe(v)


def amount_to_words(n: Any, currency: str = "USD") -> str:
    """Convert amount to words."""
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


def _org_address_str(org) -> str:
    """Return comma-joined address string from Organisation's first address."""
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
    """Get email from organisation's first address."""
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        return addr.email if addr else ""
    except Exception:
        return ""


def _org_country_name(org) -> str:
    """Return country name from Organisation's first address."""
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        if addr and getattr(addr, "country", None):
            return addr.country.name
        return ""
    except Exception:
        return ""


# ============================================================================
# MAIN PDF GENERATOR
# ============================================================================

def generate_proforma_invoice_pdf_bytes(invoice) -> bytes:
    """
    Generate Proforma Invoice PDF with professional black and white design.

    Args:
        invoice: ProformaInvoice model instance

    Returns:
        bytes: PDF content in-memory
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Define professional styles
    style_company_header = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=18,
        leading=22,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    style_title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        spaceAfter=16,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
    )

    style_text = ParagraphStyle(
        "Text",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    style_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    )

    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    # Check if document is draft
    from apps.workflow.constants import APPROVED
    is_draft = getattr(invoice, "status", None) != APPROVED

    # Custom canvas for watermark and footer
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for page_num, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                self._draw_footer(page_num, total_pages)
                super().showPage()
            super().save()

        def _draw_footer(self, page_num, total_pages):
            # Draw watermark if draft
            if is_draft:
                from reportlab.lib.colors import HexColor as _HexColor
                self.saveState()
                self.setFont("Helvetica-Bold", 80)
                self.setFillColor(_HexColor('#CC0000'), alpha=0.15)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()

            # Draw footer
            self.saveState()
            self.setFont("Helvetica", 8)
            self.drawCentredString(
                A4[0] / 2, 12 * mm,
                "This is a computer generated document and does not require signature",
            )
            self.setFont("Helvetica", 7)
            self.drawCentredString(
                A4[0] / 2, 8 * mm,
                f"Page {page_num} of {total_pages}",
            )
            self.restoreState()

    story = []

    # ========================================================================
    # SECTION 1: DOCUMENT HEADER
    # ========================================================================

    exp = invoice.exporter
    exp_name = safe(getattr(exp, "name", ""))
    exp_address = _org_address_str(exp)
    exp_email = _org_email(exp)
    _exp_addr_obj = exp.addresses.first() if exp else None
    exp_iec = safe(getattr(_exp_addr_obj, "iec_code", ""))
    exp_country = _org_country_name(exp)

    exp_detail_parts = []
    if exp_address:
        exp_detail_parts.append(exp_address)
    if exp_country:
        exp_detail_parts.append(exp_country)
    if exp_email:
        exp_detail_parts.append(exp_email)
    exp_detail_html = "<br/>".join([exp_name] + exp_detail_parts)

    story.append(Paragraph(exp_name, style_company_header))
    story.append(Paragraph("PROFORMA INVOICE CUM SALES CONTRACT", style_title))

    # Separator line
    line_table = Table([[""]], colWidths=[180 * mm])
    line_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 10))

    # ========================================================================
    # SECTION 2: MAIN INFO TABLE (TOP HALF)
    # ========================================================================

    cons = invoice.consignee
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

    buyer_obj = getattr(invoice, "buyer", None)
    buyer_name = safe(getattr(buyer_obj, "name", "")) if buyer_obj else cons_name

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
        buyer_details_html = cons_name

    origin_country = _org_country_name(exp)
    final_dest_obj = getattr(invoice, "country_of_final_destination", None)
    final_country = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""

    pi_number = safe(getattr(invoice, "pi_number", ""))
    pi_date = safe(getattr(invoice, "pi_date", ""))
    buyer_order_no = safe(getattr(invoice, "buyer_order_no", ""))
    buyer_order_date = safe(getattr(invoice, "buyer_order_date", ""))
    other_references = safe(getattr(invoice, "other_references", ""))

    main_info_data = [
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
        [
            "", "",
            Paragraph(f"<b>Country of Origin of Goods:</b><br/>{origin_country}", style_text),
            Paragraph(f"<b>Country of Final Destination:</b><br/>{final_country}", style_text),
        ],
        [
            Paragraph(f"<b>Consignee:</b><br/>{consignee_details_html}", style_text),
            "",
            Paragraph(f"<b>Buyer if other than consignee:</b><br/>{buyer_details_html}", style_text),
            Paragraph(f"<b>Other reference(s):</b><br/>{other_references}", style_text),
        ],
        [
            "", "", "", "",
        ],
    ]

    main_info_table_top = Table(
        main_info_data,
        colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm],
    )
    main_info_table_top.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (0, 0), (1, 1)),
        ("SPAN", (0, 2), (1, 3)),
        ("SPAN", (2, 2), (2, 3)),
        ("SPAN", (3, 2), (3, 3)),
    ]))

    # ========================================================================
    # SECTION 3: MAIN INFO TABLE (BOTTOM HALF)
    # ========================================================================

    incoterm_obj = getattr(invoice, "incoterms", None)
    incoterm_disp = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""

    payment_term_obj = getattr(invoice, "payment_terms", None)
    payment_term_name = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""

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

    info_rows_b = Table(
        [
            [
                Paragraph(f"<b>Pre-Carriaged By:</b><br/>{pre_carriage}", style_text),
                Paragraph(f"<b>Place of Receipt by Pre-Carrier:</b><br/>{por_pre}", style_text),
                Paragraph(f"<b>Vessel/Flight No:</b><br/>{safe(invoice.vessel_flight_no)}", style_text),
            ],
            [
                Paragraph("<b>No &amp; Kind of Packages</b><br/>", style_text),
                Paragraph("<b>Marks &amp; Nos/Container No</b><br/>", style_text),
                Paragraph(f"<b>Payment Terms:</b><br/>{payment_term_name}", style_text),
            ],
        ],
        colWidths=[60 * mm, 60 * mm, 60 * mm],
    )
    info_rows_b.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    info_row_a = Table(
        [[
            Paragraph(f"<b>Port of Loading:</b><br/>{port_loading}", style_text),
            Paragraph(f"<b>Port of Discharge:</b><br/>{port_discharge}", style_text),
            Paragraph(f"<b>Final Destination:</b><br/>{final_dest}", style_text),
            Paragraph(f"<b>Incoterms:</b><br/>{incoterm_disp}", style_text),
        ]],
        colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm],
    )
    info_row_a.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(main_info_table_top)
    story.append(info_rows_b)
    story.append(info_row_a)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 4: LINE ITEMS TABLE
    # ========================================================================

    li_header = [
        Paragraph("<b>Sr.</b>", style_table_header),
        Paragraph("<b>HSN Code</b>", style_table_header),
        Paragraph("<b>Item Code</b>", style_table_header),
        Paragraph("<b>Description of Goods</b>", style_table_header),
        Paragraph("<b>Qty</b>", style_table_header),
        Paragraph("<b>Rate (USD)</b>", style_table_header),
        Paragraph("<b>Amount (USD)</b>", style_table_header),
    ]
    li_rows = [li_header]
    total_amount_usd = Decimal("0.00")

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
            Paragraph(safe(it.hsn_code), style_text),
            Paragraph(safe(it.item_code), style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{fmt_qty(it.quantity)} {uom_display}".strip(), style_text),
            Paragraph(fmt_money(it.rate_usd), style_text),
            Paragraph(fmt_money(amount), style_text),
        ])

    li_table = Table(
        li_rows,
        colWidths=[10 * mm, 24 * mm, 24 * mm, 40 * mm, 27 * mm, 31 * mm, 24 * mm],
    )
    li_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (4, 1), (6, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 5: TOTALS SECTION
    # ========================================================================

    charges_list = list(invoice.charges.all().order_by("id"))
    charges_total = Decimal("0.00")
    for charge in charges_list:
        charges_total += Decimal(str(charge.amount_usd or 0))

    grand_total = total_amount_usd + charges_total

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
        "freight": "Freight",
        "insurance_amount": "Insurance Amount",
        "import_duty": "Import Duty",
        "destination_charges": "Destination Charges",
    }
    seller_fields = _SELLER_FIELDS.get(incoterm_disp, [])
    show_cost_breakdown = bool(incoterm_disp) and incoterm_disp != "EXW"

    invoice_total_pdf = grand_total
    for field in seller_fields:
        val = getattr(invoice, field, None)
        if val is not None:
            try:
                invoice_total_pdf += Decimal(str(val))
            except Exception:
                pass

    final_total = invoice_total_pdf if incoterm_disp else grand_total

    totals_rows = []

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

    if not incoterm_disp:
        totals_rows.append([
            Paragraph("<b>Grand Total Amount</b>", style_label),
            Paragraph(f"<b>${fmt_money(grand_total)}</b>", style_label),
        ])

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
            # Skip freight/insurance rows if the user has not filled in a value
            if val is None:
                continue
            totals_rows.append([
                Paragraph(_FIELD_LABELS.get(field, field), style_text),
                Paragraph(f"${fmt_money(val)}", style_text),
            ])

    if incoterm_disp:
        totals_rows.append([
            Paragraph("<b>Invoice Total (Amount Payable)</b>", style_label),
            Paragraph(f"<b>${fmt_money(invoice_total_pdf)}</b>", style_label),
        ])

    if totals_rows:
        totals_table = Table(totals_rows, colWidths=[140 * mm, 40 * mm])
        totals_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 6))

    # ========================================================================
    # SECTION 6: AMOUNT IN WORDS
    # ========================================================================

    words_table = Table(
        [[Paragraph(f"<b>Amount in Words:</b> {amount_to_words(final_total, currency='USD')}", style_text)]],
        colWidths=[180 * mm],
    )
    words_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(words_table)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 7: VALIDITY & SHIPMENT TABLE
    # ========================================================================

    validity_data = [
        [
            Paragraph(f"<b>Validity for Acceptance:</b> {safe(invoice.validity_for_acceptance)}", style_text),
            Paragraph(f"<b>Validity for Shipment:</b> {safe(invoice.validity_for_shipment)}", style_text),
        ],
        [
            Paragraph(f"<b>Partial Shipment:</b> {bool_yn(invoice.partial_shipment)}", style_text),
            Paragraph(f"<b>Transshipment:</b> {bool_yn(invoice.transshipment)}", style_text),
        ],
    ]
    validity_table = Table(validity_data, colWidths=[90 * mm, 90 * mm])
    validity_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(validity_table)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 8: DECLARATION
    # ========================================================================

    decl_text = (
        "<b>Declaration:</b> We declare that this invoice shows the actual price of the "
        "goods described and that all particulars are true and correct."
    )
    if getattr(invoice, "bank_charges_to_buyer", False):
        decl_text += (
            "<br/><b>BANK CHARGES:</b> WITHIN INDIA ON ACCOUNT OF BENEFICIARY &amp; "
            "OUTSIDE OF INDIA ON ACCOUNT OF BUYER"
        )
    decl_table = Table(
        [[Paragraph(decl_text, style_text)]],
        colWidths=[180 * mm],
    )
    decl_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(decl_table)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 9: BANK DETAILS
    # ========================================================================

    bank = getattr(invoice, "bank", None)
    if bank:
        bank_lines = []
        bank_lines.append(f"<b>BENEFICIARY NAME:</b> {safe(bank.beneficiary_name)}")
        bank_lines.append(f"<b>BANK NAME:</b> {safe(bank.bank_name)}")
        bank_lines.append(f"<b>BRANCH NAME:</b> {safe(bank.branch_name)}")
        bank_lines.append(f"<b>BRANCH ADDRESS:</b> {safe(bank.branch_address)}")
        bank_lines.append(f"<b>A/C NO.:</b> {safe(bank.account_number)}")
        if bank.routing_number:
            bank_lines.append(f"<b>IFSC CODE:</b> {safe(bank.routing_number)}")
        if bank.swift_code:
            bank_lines.append(f"<b>SWIFT CODE:</b> {safe(bank.swift_code)}")
        if bank.iban:
            bank_lines.append(f"<b>IBAN:</b> {safe(bank.iban)}")

        if safe(bank.intermediary_bank_name):
            intermediary_currency_code = (
                safe(getattr(bank.intermediary_currency, "code", ""))
                if getattr(bank, "intermediary_currency", None) else ""
            )
            bank_lines.append(
                f"<b>Intermediary Institution Routing for Currency</b> {intermediary_currency_code} "
                f"<b>A/C No.:</b> {safe(bank.intermediary_account_number)} "
                f"The Bank of {safe(bank.intermediary_bank_name)} "
                f"<b>SWIFT Code:</b> {safe(bank.intermediary_swift_code)}"
            )

        bank_lines.append(
            "Request your bank to send MT 103 Message to our bank and send us copy of this "
            "message to trace &amp; claim the payment from our bank."
        )

        bank_rows = [[Paragraph(line, style_text)] for line in bank_lines]
        bank_box = Table(bank_rows, colWidths=[180 * mm])
        bank_box.setStyle(TableStyle([
            # Use all 4 explicit line commands instead of BOX so that when the
            # table splits across pages every fragment keeps all 4 borders.
            ("LINEABOVE",  (0, 0),  (-1, 0),  1.2, colors.black),
            ("LINEBELOW",  (0, -1), (-1, -1), 1.2, colors.black),
            ("LINEBEFORE", (0, 0),  (0, -1),  1.2, colors.black),
            ("LINEAFTER",  (-1, 0), (-1, -1), 1.2, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(bank_box)
        story.append(Spacer(1, 6))

    # ========================================================================
    # SECTION 10: TERMS & CONDITIONS
    # ========================================================================

    tc_content = getattr(invoice, "tc_content", "") or ""
    if tc_content.strip():
        story.append(PageBreak())

        tc_header = Table(
            [[Paragraph("<b>Additional Terms &amp; Conditions</b>", style_label)]],
            colWidths=[180 * mm],
        )
        tc_header.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tc_header)
        story.append(Spacer(1, 8))

        from pdf.utils import html_to_rl_flowables
        story.extend(html_to_rl_flowables(tc_content, style_small, spacer_pt=5))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_pi_pdf(pi):
    """Wrapper used by the PI view — returns an in-memory BytesIO buffer."""
    import io
    pdf_bytes = generate_proforma_invoice_pdf_bytes(pi)
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
