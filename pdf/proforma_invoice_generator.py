"""
Proforma Invoice PDF generator — pdf1/ reference layout, mapped to actual model fields.

Field mapping summary (pdf1/ attribute → actual model field):
  invoice.number                     → invoice.pi_number
  invoice.date                       → invoice.pi_date
  invoice.incoterm.code              → invoice.incoterms.code      (FK field is 'incoterms')
  invoice.payment_term.name          → invoice.payment_terms.name  (FK field is 'payment_terms')
  invoice.port_loading.name          → invoice.port_of_loading.name
  invoice.port_discharge.name        → invoice.port_of_discharge.name
  invoice.pre_carriage.name          → invoice.pre_carriage_by.name
  invoice.marks_and_nos              → (field does not exist — omitted)
  invoice.kind_of_packages           → (field does not exist — omitted)
  invoice.bank_charges               → (field does not exist — omitted)
  invoice.terms_and_conditions       → invoice.tc_content
  invoice.partial_shipment / transshipment → CharField ("ALLOWED"/"NOT_ALLOWED")
  invoice.total_amount_usd           → computed: sum(li.amount_usd)
  it.hs_code                         → it.hsn_code
  it.unit_price_usd                  → it.rate_usd
  it.uom (string)                    → it.uom.abbreviation  (UOM FK)
  line_items.filter(is_active=True)  → .all()  (no is_active on ProformaInvoiceLineItem)
  exp.address / exp.email_id         → org.addresses helper functions

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

    # ---- Main information table (Rows 0-5, 4 columns) -------------------------
    #
    # Visual layout:
    #   Col 0-1 (rows 0-2): Exporter block
    #   Col 2-3 (row 0):    PI No & Date
    #   Col 2-3 (row 1):    Buyer Order No and Date
    #   Col 2-3 (row 2):    Other reference(s)
    #   Col 0-1 (rows 3-5): Consignee block
    #   Col 2-3 (rows 3-4): Buyer if other than consignee
    #   Col 2   (row 5):    Country of Origin
    #   Col 3   (row 5):    Country of Final Destination
    #
    buyer_obj = getattr(invoice, "buyer", None)
    buyer_name = safe(getattr(buyer_obj, "name", "")) if buyer_obj else cons_name

    main_info_data = [
        # Row 0
        [
            Paragraph(
                f"<b>Exporter:</b><br/>{exp_detail_html}",
                style_text,
            ),
            "",
            Paragraph(
                f"<b>Proforma Invoice No &amp; Date:</b><br/>{pi_number} &amp; {pi_date}",
                style_text,
            ),
            "",
        ],
        # Row 1
        [
            "", "",
            Paragraph(
                f"<b>Buyer Order No and Date:</b><br/>{buyer_order_no} &amp; {buyer_order_date}",
                style_text,
            ),
            "",
        ],
        # Row 2
        [
            "", "",
            Paragraph(f"<b>Other reference(s):</b><br/>{other_references}", style_text),
            "",
        ],
        # Row 3
        [
            Paragraph(f"<b>Consignee:</b><br/>{consignee_details_html}", style_text),
            "",
            Paragraph(f"<b>Buyer if other than consignee</b><br/>{buyer_name}", style_text),
            "",
        ],
        # Row 4
        ["", "", "", ""],
        # Row 5
        [
            "", "",
            Paragraph(f"<b>Country of Origin of Goods:</b><br/>{origin_country}", style_text),
            Paragraph(f"<b>Country of Final Destination:</b><br/>{final_country}", style_text),
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
        # Merge: Exporter block col 0-1, rows 0-2
        ("SPAN",         (0, 0), (1, 2)),
        # Merge: PI No & Date col 2-3, row 0
        ("SPAN",         (2, 0), (3, 0)),
        # Merge: Buyer Order col 2-3, row 1
        ("SPAN",         (2, 1), (3, 1)),
        # Merge: Other refs col 2-3, row 2
        ("SPAN",         (2, 2), (3, 2)),
        # Merge: Consignee col 0-1, rows 3-5
        ("SPAN",         (0, 3), (1, 5)),
        # Merge: Buyer col 2-3, rows 3-4
        ("SPAN",         (2, 3), (3, 4)),
        # Row 5 col 2 and col 3 remain separate (Country of Origin / Final Destination)
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

    # ---- Total amount table ---------------------------------------------------
    amount_table = Table(
        [[
            Paragraph("<b>Amount Chargeable in:</b> USD", style_text),
            Paragraph("<b>Total</b>", style_text),
            Paragraph(f"${fmt_money(total_amount_usd)}", style_text),
        ]],
        colWidths=[100 * mm, 40 * mm, 40 * mm],
    )
    amount_table.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 4))

    # Amount in words
    story.append(Paragraph(
        f"<b>Amount in Words:</b> {amount_to_words(total_amount_usd, currency='USD')}",
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
    if bank:
        beneficiary_data = [
            [Paragraph(f"<b>BENEFICIARY NAME:</b> {safe(bank.beneficiary_name)}", style_text)],
            [Paragraph(f"<b>BANK NAME:</b> {safe(bank.bank_name)}", style_text)],
            [Paragraph(f"<b>BRANCH NAME:</b> {safe(bank.branch_name)}", style_text)],
            [Paragraph(f"<b>BRANCH ADDRESS:</b> {safe(bank.branch_address)}", style_text)],
            [Paragraph(f"<b>A/C NO.:</b> {safe(bank.account_number)}", style_text)],
            [Paragraph(f"<b>SWIFT CODE:</b> {safe(bank.swift_code)}", style_text)],
        ]
        beneficiary_table = Table(beneficiary_data, colWidths=[180 * mm])
        beneficiary_table.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ]))
        story.append(beneficiary_table)
        story.append(Spacer(1, 10))

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
