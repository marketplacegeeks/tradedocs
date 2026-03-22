"""
Purchase Order PDF Generator

Generates professional Purchase Order PDFs using ReportLab.
Constraint #9: Returns bytes in-memory — never writes to disk.
"""
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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
# UTILITIES
# ============================================================================

def _safe(v, default="") -> str:
    return default if v is None else str(v)


def _fmt_money(v) -> str:
    """Format number with comma separators, strip trailing zeros."""
    try:
        s = f"{float(v):,.2f}".rstrip("0").rstrip(".")
        return s
    except Exception:
        return _safe(v)


def _fmt_qty(v) -> str:
    try:
        s = f"{float(v):,.3f}".rstrip("0").rstrip(".")
        return s
    except Exception:
        return _safe(v)


def _addr_lines(addr_obj) -> list[str]:
    """Convert an OrganisationAddress object to a list of display lines."""
    if not addr_obj:
        return []
    parts = []
    if addr_obj.line1:
        parts.append(addr_obj.line1)
    if addr_obj.line2:
        parts.append(addr_obj.line2)
    city_state = ", ".join(filter(None, [addr_obj.city, addr_obj.state]))
    if city_state:
        parts.append(city_state)
    if addr_obj.pin:
        parts.append(addr_obj.pin)
    if getattr(addr_obj, "country", None):
        parts.append(addr_obj.country.name)
    return parts


def _org_first_address(org):
    """Return the first OrganisationAddress for an org, or None."""
    if not org:
        return None
    try:
        return org.addresses.first()
    except Exception:
        return None


# ============================================================================
# MAIN PDF GENERATOR
# ============================================================================

def generate_purchase_order_pdf_bytes(po) -> bytes:
    """
    Generate a Purchase Order PDF.

    Args:
        po: PurchaseOrder model instance (with prefetched line_items)

    Returns:
        bytes: in-memory PDF content
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

    style_title = ParagraphStyle(
        "POTitle",
        parent=styles["Normal"],
        fontSize=14,
        leading=18,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "POLabel",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "POText",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    style_small = ParagraphStyle(
        "POSmall",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    )
    style_th = ParagraphStyle(
        "POTh",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    style_right = ParagraphStyle(
        "PORight",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
    )
    style_right_bold = ParagraphStyle(
        "PORightBold",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        alignment=TA_RIGHT,
    )

    from apps.workflow.constants import APPROVED
    is_draft = getattr(po, "status", None) != APPROVED

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
            if is_draft:
                from reportlab.lib.colors import HexColor as _HexColor
                self.saveState()
                self.setFont("Helvetica-Bold", 80)
                self.setFillColor(_HexColor("#CC0000"), alpha=0.15)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()

            self.saveState()
            self.setFont("Helvetica", 8)
            self.drawCentredString(
                A4[0] / 2, 12 * mm,
                "This is a computer generated document and does not require signature",
            )
            self.setFont("Helvetica", 7)
            self.drawCentredString(A4[0] / 2, 8 * mm, f"Page {page_num} of {total_pages}")
            self.restoreState()

    story = []

    # ========================================================================
    # SECTION 1: DOCUMENT TITLE
    # ========================================================================

    story.append(Paragraph("PURCHASE ORDER", style_title))

    line_table = Table([[""]], colWidths=[180 * mm])
    line_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(line_table)

    # ========================================================================
    # SECTION 2: VENDOR + PO DETAILS HEADER
    # ========================================================================

    vendor = getattr(po, "vendor", None)
    vendor_name = _safe(getattr(vendor, "name", ""))
    vendor_addr = _org_first_address(vendor)
    vendor_addr_lines = _addr_lines(vendor_addr)
    vendor_detail_html = "<br/>".join([vendor_name] + vendor_addr_lines) if vendor_name else "—"

    delivery_addr = getattr(po, "delivery_address", None)
    delivery_lines = _addr_lines(delivery_addr)
    delivery_html = "<br/>".join(delivery_lines) if delivery_lines else "—"

    currency_obj = getattr(po, "currency", None)
    currency_code = _safe(getattr(currency_obj, "code", ""))

    payment_terms_obj = getattr(po, "payment_terms", None)
    payment_terms_name = _safe(getattr(payment_terms_obj, "name", "")) if payment_terms_obj else "—"

    country_obj = getattr(po, "country_of_origin", None)
    country_name = _safe(getattr(country_obj, "name", "")) if country_obj else "—"

    internal_contact = getattr(po, "internal_contact", None)
    contact_name = _safe(getattr(internal_contact, "get_full_name", lambda: "")()) if internal_contact else "—"
    contact_phone = ""
    if internal_contact:
        cc = _safe(getattr(internal_contact, "phone_country_code", ""))
        ph = _safe(getattr(internal_contact, "phone_number", ""))
        if cc and ph:
            contact_phone = f"{cc} {ph}"

    header_data = [
        [
            Paragraph(f"<b>Vendor / Supplier:</b><br/>{vendor_detail_html}", style_text),
            Paragraph(
                f"<b>PO No:</b> {_safe(po.po_number)}<br/>"
                f"<b>Date:</b> {_safe(po.po_date)}<br/>"
                f"<b>Customer No:</b> {_safe(po.customer_no) or '—'}",
                style_text,
            ),
        ],
        [
            Paragraph(f"<b>Delivery Address:</b><br/>{delivery_html}", style_text),
            Paragraph(
                f"<b>Internal Contact:</b> {contact_name}<br/>"
                + (f"<b>Phone:</b> {contact_phone}<br/>" if contact_phone else "")
                + f"<b>Currency:</b> {currency_code or '—'}",
                style_text,
            ),
        ],
    ]

    header_table = Table(header_data, colWidths=[90 * mm, 90 * mm])
    header_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))

    # ========================================================================
    # SECTION 3: DOCUMENT DETAILS STRIP
    # ========================================================================

    tx_type = _safe(getattr(po, "transaction_type", ""))
    tx_labels = {
        "IGST": "IGST (Inter-State)",
        "CGST_SGST": "CGST+SGST (Same State)",
        "ZERO_RATED": "Zero Rated (Export)",
    }
    tx_display = tx_labels.get(tx_type, tx_type or "—")

    details_data = [[
        Paragraph(f"<b>Payment Terms:</b><br/>{payment_terms_name}", style_text),
        Paragraph(f"<b>Country of Origin:</b><br/>{country_name}", style_text),
        Paragraph(f"<b>Time of Delivery:</b><br/>{_safe(po.time_of_delivery) or '—'}", style_text),
        Paragraph(f"<b>Transaction Type:</b><br/>{tx_display}", style_text),
    ]]
    details_table = Table(details_data, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm])
    details_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 10))

    # ========================================================================
    # SECTION 4: LINE ITEMS TABLE (tax columns vary by transaction_type)
    # ========================================================================

    line_items = list(po.line_items.all().order_by("sort_order", "id"))

    # Build dynamic column headers and data based on transaction_type
    if tx_type == "IGST":
        headers = [
            Paragraph("<b>#</b>", style_th),
            Paragraph("<b>Description</b>", style_th),
            Paragraph("<b>HSN Code</b>", style_th),
            Paragraph("<b>Mfr</b>", style_th),
            Paragraph("<b>Qty</b>", style_th),
            Paragraph("<b>Unit Price</b>", style_th),
            Paragraph("<b>Taxable Amt</b>", style_th),
            Paragraph("<b>IGST %</b>", style_th),
            Paragraph("<b>IGST Amt</b>", style_th),
            Paragraph("<b>Total</b>", style_th),
        ]
        col_widths = [8*mm, 42*mm, 18*mm, 18*mm, 14*mm, 18*mm, 18*mm, 12*mm, 15*mm, 17*mm]
        right_cols = {4, 5, 6, 7, 8, 9}
    elif tx_type == "CGST_SGST":
        headers = [
            Paragraph("<b>#</b>", style_th),
            Paragraph("<b>Description</b>", style_th),
            Paragraph("<b>HSN Code</b>", style_th),
            Paragraph("<b>Mfr</b>", style_th),
            Paragraph("<b>Qty</b>", style_th),
            Paragraph("<b>Unit Price</b>", style_th),
            Paragraph("<b>Taxable Amt</b>", style_th),
            Paragraph("<b>CGST %</b>", style_th),
            Paragraph("<b>CGST Amt</b>", style_th),
            Paragraph("<b>SGST %</b>", style_th),
            Paragraph("<b>SGST Amt</b>", style_th),
            Paragraph("<b>Total</b>", style_th),
        ]
        col_widths = [7*mm, 35*mm, 15*mm, 14*mm, 12*mm, 16*mm, 16*mm, 10*mm, 12*mm, 10*mm, 12*mm, 15*mm]
        right_cols = {4, 5, 6, 7, 8, 9, 10, 11}
    else:
        # ZERO_RATED — no tax columns
        headers = [
            Paragraph("<b>#</b>", style_th),
            Paragraph("<b>Description</b>", style_th),
            Paragraph("<b>Item Code</b>", style_th),
            Paragraph("<b>HSN Code</b>", style_th),
            Paragraph("<b>Mfr</b>", style_th),
            Paragraph("<b>Qty</b>", style_th),
            Paragraph("<b>Unit Price</b>", style_th),
            Paragraph("<b>Total</b>", style_th),
        ]
        col_widths = [8*mm, 50*mm, 22*mm, 18*mm, 18*mm, 16*mm, 22*mm, 26*mm]
        right_cols = {5, 6, 7}

    li_rows = [headers]
    grand_total = Decimal("0.00")

    for idx, item in enumerate(line_items, start=1):
        uom_obj = getattr(item, "uom", None)
        uom_display = _safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
        qty_str = f"{_fmt_qty(item.quantity)} {uom_display}".strip()
        item_total = item.total or Decimal("0.00")
        try:
            grand_total += Decimal(str(item_total))
        except Exception:
            pass

        if tx_type == "IGST":
            row = [
                Paragraph(str(idx), style_text),
                Paragraph(_safe(item.description), style_text),
                Paragraph(_safe(item.hsn_code), style_text),
                Paragraph(_safe(item.manufacturer), style_text),
                Paragraph(qty_str, style_right),
                Paragraph(_fmt_money(item.unit_price), style_right),
                Paragraph(_fmt_money(item.taxable_amount), style_right),
                Paragraph(_safe(item.igst_percent) or "—", style_right),
                Paragraph(_fmt_money(item.igst_amount) if item.igst_amount else "—", style_right),
                Paragraph(_fmt_money(item_total), style_right_bold),
            ]
        elif tx_type == "CGST_SGST":
            row = [
                Paragraph(str(idx), style_text),
                Paragraph(_safe(item.description), style_text),
                Paragraph(_safe(item.hsn_code), style_text),
                Paragraph(_safe(item.manufacturer), style_text),
                Paragraph(qty_str, style_right),
                Paragraph(_fmt_money(item.unit_price), style_right),
                Paragraph(_fmt_money(item.taxable_amount), style_right),
                Paragraph(_safe(item.cgst_percent) or "—", style_right),
                Paragraph(_fmt_money(item.cgst_amount) if item.cgst_amount else "—", style_right),
                Paragraph(_safe(item.sgst_percent) or "—", style_right),
                Paragraph(_fmt_money(item.sgst_amount) if item.sgst_amount else "—", style_right),
                Paragraph(_fmt_money(item_total), style_right_bold),
            ]
        else:
            row = [
                Paragraph(str(idx), style_text),
                Paragraph(_safe(item.description), style_text),
                Paragraph(_safe(item.item_code), style_text),
                Paragraph(_safe(item.hsn_code), style_text),
                Paragraph(_safe(item.manufacturer), style_text),
                Paragraph(qty_str, style_right),
                Paragraph(_fmt_money(item.unit_price), style_right),
                Paragraph(_fmt_money(item_total), style_right_bold),
            ]
        li_rows.append(row)

    # Totals row spanning all columns except the last two (label + amount)
    n_cols = len(headers)
    totals_row = [""] * n_cols
    totals_row[n_cols - 2] = Paragraph("<b>Grand Total</b>", style_label)
    totals_row[n_cols - 1] = Paragraph(f"<b>{_fmt_money(grand_total)}</b>", style_right_bold)
    li_rows.append(totals_row)

    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # Totals row style
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8E8E8")),
        ("SPAN", (0, -1), (n_cols - 3, -1)),
    ]
    for c in right_cols:
        cmds.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))

    li_table = Table(li_rows, colWidths=col_widths, repeatRows=1)
    li_table.setStyle(TableStyle(cmds))
    story.append(li_table)
    story.append(Spacer(1, 12))

    # ========================================================================
    # SECTION 5: BANK DETAILS (optional)
    # ========================================================================

    bank = getattr(po, "bank", None)
    if bank:
        bank_lines = [
            f"<b>Beneficiary Name:</b> {_safe(bank.beneficiary_name)}",
            f"<b>Bank Name:</b> {_safe(bank.bank_name)}",
            f"<b>Branch:</b> {_safe(bank.branch_name)}",
            f"<b>Account No.:</b> {_safe(bank.account_number)}",
        ]
        if bank.routing_number:
            bank_lines.append(f"<b>IFSC / Routing:</b> {_safe(bank.routing_number)}")
        if bank.swift_code:
            bank_lines.append(f"<b>SWIFT Code:</b> {_safe(bank.swift_code)}")
        if bank.iban:
            bank_lines.append(f"<b>IBAN:</b> {_safe(bank.iban)}")

        bank_rows = [[Paragraph(line, style_text)] for line in bank_lines]
        bank_box = Table(bank_rows, colWidths=[180 * mm])
        bank_box.setStyle(TableStyle([
            ("LINEABOVE",  (0, 0),  (-1, 0),  1.2, colors.black),
            ("LINEBELOW",  (0, -1), (-1, -1), 1.2, colors.black),
            ("LINEBEFORE", (0, 0),  (0, -1),  1.2, colors.black),
            ("LINEAFTER",  (-1, 0), (-1, -1), 1.2, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(bank_box)
        story.append(Spacer(1, 8))

    # ========================================================================
    # SECTION 6: REMARKS (optional)
    # ========================================================================

    remarks = _safe(getattr(po, "remarks", "")).strip()
    if remarks:
        remarks_box = Table(
            [[Paragraph(f"<b>Remarks:</b> {remarks}", style_text)]],
            colWidths=[180 * mm],
        )
        remarks_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(remarks_box)
        story.append(Spacer(1, 8))

    # ========================================================================
    # SECTION 7: TERMS & CONDITIONS (optional, new page)
    # ========================================================================

    tc_content = _safe(getattr(po, "tc_content", "")).strip()
    if tc_content:
        story.append(PageBreak())
        tc_header = Table(
            [[Paragraph("<b>Terms &amp; Conditions</b>", style_label)]],
            colWidths=[180 * mm],
        )
        tc_header.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tc_header)
        story.append(Spacer(1, 8))
        from pdf.utils import html_to_rl_flowables
        story.extend(html_to_rl_flowables(tc_content, style_small, spacer_pt=5))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_po_pdf(po):
    """Wrapper used by the PO view — returns an in-memory BytesIO buffer."""
    import io
    pdf_bytes = generate_purchase_order_pdf_bytes(po)
    buf = io.BytesIO(pdf_bytes)
    buf.seek(0)
    return buf
