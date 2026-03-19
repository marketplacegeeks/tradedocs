from io import BytesIO
from decimal import Decimal
from typing import Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

# ============================================================================
# PACKING LIST PDF LAYOUT GUIDE (ASCII VISUAL + HOW TO TWEAK)
# ============================================================================
# This file generates a PACKING LIST PDF using ReportLab platypus Tables.
# Use this guide to understand the layout and safely modify widths/paddings/fonts.
#
# PAGE:
# - A4 portrait (210mm x 297mm)
# - Margins: left=10mm, right=10mm, top=10mm, bottom=10mm
# - Effective content width ≈ 210 - (10+10) = 190mm
# - We target 180mm total width for tables to leave room for borders/padding
#
#
#
# SUMMARY BLOCKS (Total width = 180mm):
# - Two rows x four columns: [60mm | 60mm | 30mm | 30mm]
#   Row 0:
#     - Columns 0-1 merged: "Exporter:"
#     - Column 2: PI No/Date
#     - Column 3: reserved (blank)
#   Row 1:
#     - Column 0: Corporate Office (Exporter details: name, address, country, email)
#     - Column 1: Registered Office (registered address details: name, street, country, phone/email)
#     - Columns 2-3 merged: References list
#         PO No/Date, LC No/Date, B/L No/Date, SO No/Date, Other Ref/Date
#
#   ASCII:
#   ┌────────────────────────────────────────────┬────────────────────────────┬──────────────┬──────────────┐
#   │ Exporter: (merged across col 0-1)         │                            │ PI No/Date   │ (reserved)   │  Row 0
#   ├────────────────────────────────────────────┼────────────────────────────┼──────────────┴──────────────┤
#   │ Corporate Office:                          │ Registered Office:         │ References (merged across    │  Row 1
#   │ name, addr, country, email                 │ name, street, country,     │ col 2-3): PO/LC/B/L/SO/Other │
#   │                                            │ phone/email                 │ Ref/Date                     │
#   └────────────────────────────────────────────┴────────────────────────────┴──────────────────────────────┘
#        60mm (col 0)                                  60mm (col 1)           30mm (col 2)   30mm (col 3)   Total=180mm
#
# REGISTERED ADDRESS (EXPORTER):
# - Embedded within Summary Blocks: Row 1, Column 1 of the 2x4 summary grid
# - No separate block below summary; details now appear alongside exporter details
#
#   ASCII (within summary grid):
#   Row 1:
#     Col 0 → Exporter details (name, address, country, email)
#     Col 1 → Registered Address (name, street, country, phone/email)
#     Col 2-3 (merged) → References list
#
# NOTIFY PARTY (OPTIONAL) (Total width = 180mm):
# - Two columns: [35mm label | 145mm content]
#   ┌────────────┬──────────────────────────────────────────────────────────┐
#   │ Notify     │ Notify Party text                                        │
#   │ Party      │                                                          │
#   └────────────┴──────────────────────────────────────────────────────────┘
#     35mm label        145mm content                         Total=180mm
#
# CONTAINER HEADER (Total width = 180mm):
# - Two columns: [90mm | 90mm]
#   ┌──────────────────────────┬────────────────────────────────────────────┐
#   │ Container: REF           │ Marks & Numbers                            │
#   └──────────────────────────┴────────────────────────────────────────────┘
#      90mm left                     90mm right                 Total=180mm
#
# ITEMS TABLE (Total width = 180mm, repeat header across pages):
# - Columns (mm): [12 | 20 | 32 | 60 | 18 | 14 | 12 | 12]
#   Headers:  Sr. | HSN/Item | Packages (No & Kind) | Description of Goods | Qty | Net | Tare | Gross
#
#   ASCII (widths annotated):
#   ┌──────┬────────┬────────────────────┬──────────────────────────────┬──────┬──────┬──────┬──────┐
#   │ Sr.  │ HSN/   │ Packages (No &     │ Description of Goods         │ Qty  │ Net  │ Tare │ Gross│
#   │ 12mm │ Item   │ Kind) 32mm         │ 60mm                         │ 18mm │ 14mm │ 12mm │ 12mm │
#   ├──────┼────────┼────────────────────┼──────────────────────────────┼──────┼──────┼──────┼──────┤
#   │ rows… (repeat header on page break, numbers aligned right for Qty/weights)               │
#   └──────┴────────┴────────────────────┴──────────────────────────────┴──────┴──────┴──────┴──────┘
#                 12   20         32                  60         18    14    12    12    => Total=180mm
#
# TOTALS ROW (Total width = 180mm):
# - Pairs: [34mm label | 26mm value] x 3 (Net, Tare, Gross)
#   ┌───────────────────────┬──────────┬───────────────────────┬──────────┬───────────────────────┬──────────┐
#   │ Total Net Weight      │ value    │ Total Tare Weight     │ value    │ Total Gross Weight    │ value    │
#   └───────────────────────┴──────────┴───────────────────────┴──────────┴───────────────────────┴──────────┘
#     34mm label 26mm val   34mm label 26mm val   34mm label 26mm val   => Total=180mm
#
# HOW TO MODIFY:
# - Change table widths via colWidths lists (keep total ~180mm).
# - Adjust paddings via TableStyle LEFT/RIGHT/TOP/BOTTOMPADDING.
# - Change fonts/sizes via ParagraphStyle (style_text, style_label, etc.).
# - repeatRows=1 ensures item headers repeat on new pages.
# - KeepTogether ties container header and its items to avoid split headers.
#
# LEGAL-FORM MATCH (exact coordinates):
# - To match an official legal form exactly, overlay a background PDF and draw text at fixed x,y
#   using ReportLab canvas/BaseDocTemplate. Provide that template and coordinates to implement.
# ============================================================================

def safe(v: Any, default: str = "") -> str:
    return default if v is None else str(v)


def _fmt_decimal(v: Optional[Decimal], places: int = 3) -> str:
    if v is None:
        return ""
    try:
        return f"{Decimal(v):.{places}f}"
    except Exception:
        try:
            return f"{float(v):.{places}f}"
        except Exception:
            return str(v)


def generate_packing_list_pdf_bytes(packing_list) -> bytes:
    """
    Generate a Packing List PDF from the PackingList model, using container/items data.
    Only the API gate should ensure status == APPROVED; this function assumes a valid instance.
    """
    buffer = BytesIO()
    # PAGE & MARGIN SETTINGS:
    # Adjust margins here (in mm). Content width ≈ A4 width - (left+right) = 210 - 20 = 190 mm.
    # We target 180 mm for tables to account for borders/padding.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    # STYLES:
    # Change font sizes or families here if you need larger/smaller text or different fonts.
    styles = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=16,
        leading=20,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    )

    style_title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=12,
        leading=15,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold"
    )

    style_text = ParagraphStyle(
        "Text",
        parent=styles["Normal"],
        fontSize=9,
        leading=11
    )

    style_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )

    # FOOTER:
    # Modify this function to change the footer text or add page numbers, watermarks, etc.
    def add_footer(canvas, _doc):
        canvas.saveState()
        page_width = A4[0]
        footer_text = "This is a computer-generated document. Signature is not required."
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(page_width / 2, 10 * mm, footer_text)
        canvas.restoreState()

    story = []

    # Header entities
    exp = getattr(packing_list, "exporter", None)
    cons = getattr(packing_list, "consignee", None)
    pi = getattr(packing_list, "proforma_invoice", None)

    # Company header
    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("Packing List, Weight Note", style_title))
    story.append(Spacer(1, 6))


    # SUMMARY BLOCKS (Total width = 180mm) - 2 rows x 4 columns per spec
    # Row 0:
    #   - Columns 0-1 merged, show label "Exporter:"
    #   - Column 2 shows PI (invoice) number and date
    #   - Column 3 left blank (reserved)
    # Row 1:
    #   - Column 0: Exporter details (name, address, country, email)
    #   - Column 1: Registered address details (if available)
    #   - Columns 2-3 merged: references list (PO/LC/B/L/SO/Other with dates)
    #
    # Column widths: [60mm, 60mm, 30mm, 30mm] => total 180mm
    exp_lines = []
    exp_lines.append(safe(getattr(exp, "name", "")))
    if getattr(exp, "address", ""):
        exp_lines.append(safe(getattr(exp, "address", "")))
    if getattr(exp, "country", None):
        exp_lines.append(safe(getattr(exp, "country", "")))
    if getattr(exp, "email_id", ""):
        exp_lines.append(safe(getattr(exp, "email_id", "")))
    exporter_details_html = "<b>Corporate Office</b><br/>" + "<br/>".join([ln for ln in exp_lines if ln])

    reg = getattr(exp, "registered_address_details", None)
    reg_lines = []
    if reg:
        if getattr(reg, "name", ""):
            reg_lines.append(safe(getattr(reg, "name", "")))
        if getattr(reg, "address", ""):
            reg_lines.append(safe(getattr(reg, "address", "")))
        if getattr(reg, "country", None):
            reg_lines.append(safe(getattr(reg, "country", "")))
        contact_bits = []
        if getattr(reg, "phone", ""):
            contact_bits.append(f"Phone: {safe(getattr(reg, 'phone', ''))}")
        if getattr(reg, "email", ""):
            contact_bits.append(f"Email: {safe(getattr(reg, 'email', ''))}")
        if contact_bits:
            reg_lines.append(" • ".join(contact_bits))
    reg_html = "<b>Registered Office</b><br/>" + "<br/>".join([ln for ln in reg_lines if ln])

    ref_lines = []
    po_no = safe(getattr(packing_list, "po_number", ""))
    po_date = safe(getattr(packing_list, "po_date", "")) if getattr(packing_list, "po_date", None) else ""
    lc_no = safe(getattr(packing_list, "lc_number", ""))
    lc_date = safe(getattr(packing_list, "lc_date", "")) if getattr(packing_list, "lc_date", None) else ""
    bl_no = safe(getattr(packing_list, "bl_number", ""))
    bl_date = safe(getattr(packing_list, "bl_date", "")) if getattr(packing_list, "bl_date", None) else ""
    so_no = safe(getattr(packing_list, "so_number", ""))
    so_date = safe(getattr(packing_list, "so_date", "")) if getattr(packing_list, "so_date", None) else ""
    other_ref = safe(getattr(packing_list, "other_ref", ""))
    other_ref_date = safe(getattr(packing_list, "other_ref_date", "")) if getattr(packing_list, "other_ref_date", None) else ""

    if po_no:
        ref_lines.append(f"<b>PO No/Date:</b> {po_no}{(' / ' + po_date) if po_date else ''}")
    if lc_no:
        ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{(' / ' + lc_date) if lc_date else ''}")
    if bl_no:
        ref_lines.append(f"<b>B/L No/Date:</b> {bl_no}{(' / ' + bl_date) if bl_date else ''}")
    if so_no:
        ref_lines.append(f"<b>SO No/Date:</b> {so_no}{(' / ' + so_date) if so_date else ''}")
    if other_ref:
        ref_lines.append(f"<b>Other Ref/Date:</b> {other_ref}{(' / ' + other_ref_date) if other_ref_date else ''}")

    pi_no_date = ""
    if pi:
        pi_no = safe(getattr(pi, "number", ""))
        pi_dt = safe(getattr(pi, "date", ""))
        pi_no_date = f"{pi_no}{(' / ' + pi_dt) if pi_dt else ''}"
    inv_no = safe(getattr(packing_list, "invoice_number", ""))
    iec_code = safe(getattr(exp, "iec_code", ""))

    # Build Consignee details
    cons_lines = []
    cons_lines.append(safe(getattr(cons, "name", "")))
    if getattr(cons, "address", ""):
        cons_lines.append(safe(getattr(cons, "address", "")))
    if getattr(cons, "country", None):
        cons_lines.append(safe(getattr(cons, "country", "")))
    cons_contact_bits = []
    if getattr(cons, "phone_no", ""):
        cons_contact_bits.append(f"Phone: {safe(getattr(cons, 'phone_no', ''))}")
    if getattr(cons, "email_id", ""):
        cons_contact_bits.append(f"Email: {safe(getattr(cons, 'email_id', ''))}")
    if cons_contact_bits:
        cons_lines.append(" • ".join(cons_contact_bits))
    cons_html = "<b>Consignee</b><br/>" + "<br/>".join([ln for ln in cons_lines if ln])

    # Build Buyer details only if different from Consignee
    buyer = getattr(packing_list, "buyer", None)
    show_buyer = False
    buyer_html = ""
    if buyer:
        buyer_name = safe(getattr(buyer, "name", ""))
        cons_name = safe(getattr(cons, "name", ""))
        if buyer_name.strip().lower() != cons_name.strip().lower():
            show_buyer = True
            buyer_lines = []
            buyer_lines.append(buyer_name)
            if getattr(buyer, "address", ""):
                buyer_lines.append(safe(getattr(buyer, "address", "")))
            if getattr(buyer, "country", None):
                buyer_lines.append(safe(getattr(buyer, "country", "")))
            buyer_contact_bits = []
            if getattr(buyer, "phone", ""):
                buyer_contact_bits.append(f"Phone: {safe(getattr(buyer, 'phone', ''))}")
            if getattr(buyer, "email", ""):
                buyer_contact_bits.append(f"Email: {safe(getattr(buyer, 'email', ''))}")
            if buyer_contact_bits:
                buyer_lines.append(" • ".join(buyer_contact_bits))
            buyer_html = "<b>Buyer</b><br/>" + "<br/>".join([ln for ln in buyer_lines if ln])

    # Notify Party
    notify_text = safe(getattr(packing_list, 'notify_party', ''))
    notify_html = f"<b>Notify Party</b><br/>{notify_text}" if notify_text else "<b>Notify Party</b>"

    # Origin and Final Destination Countries (from linked ProformaInvoice if available)
    # Prefer PackingList's countries; fallback to linked ProformaInvoice
    origin_country = getattr(packing_list, "origin_country", None) or (getattr(pi, "origin_country", None) if pi else None)
    dest_country = getattr(packing_list, "final_destination_country", None) or (getattr(pi, "final_destination_country", None) if pi else None)
    # Display robustly: prefer Country.name, otherwise use object's string (e.g., "Name (ISO)") or raw value
    origin_name = safe(getattr(origin_country, "name", None) or origin_country) if origin_country else ""
    dest_name = safe(getattr(dest_country, "name", None) or dest_country) if dest_country else ""

    # SUMMARY TOP (Rows 0-1): keep original column widths 60/60/30/30
    summary_top_data = [
        [
            Paragraph("<b>Exporter:</b>", style_label),  # (0,0)
            "",                                          # (1,0) merged with (0,0)
            Paragraph(f"<b>IEC Code:</b><br/>{iec_code}", style_text),      # (2,0)
            Paragraph(f"<b>Invoice No:</b><br/>{inv_no}", style_text)       # (3,0)
        ],
        [
            Paragraph(exporter_details_html, style_text),            # (0,1)
            Paragraph(reg_html, style_text),                         # (1,1)
            Paragraph("<br/>".join(ref_lines), style_text),          # (2,1)
            ""                                                       # (3,1) merged with (2,1)
        ]
    ]
    summary_top = Table(summary_top_data, colWidths=[50 * mm, 50 * mm, 40 * mm, 40 * mm])
    summary_top.hAlign = 'LEFT'
    summary_top.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (0, 0), (1, 0)),  # Row 0: "Exporter:" across col 0-1
        ('SPAN', (2, 1), (3, 1)),  # Row 1: references across col 2-3
    ]))
    story.append(summary_top)
    story.append(Spacer(1, 0))

    # Buyer and Consignee block (90mm each, total 180mm) placed above summary bottom (Notify/Origin/Destination)
    buyer_display_html = ""
    if buyer_html:
        buyer_display_html = buyer_html
    else:
        cons_fallback_lines = []
        cons_fallback_lines.append(safe(getattr(cons, "name", "")))
        if getattr(cons, "address", ""):
            cons_fallback_lines.append(safe(getattr(cons, "address", "")))
        cons_country_obj = getattr(cons, "country", None)
        if cons_country_obj:
            cons_fallback_lines.append(safe(getattr(cons_country_obj, "name", cons_country_obj)))
        if cons_contact_bits:
            cons_fallback_lines.append(" • ".join(cons_contact_bits))
        buyer_display_html = "<b>Buyer</b><br/>" + "<br/>".join([ln for ln in cons_fallback_lines if ln])

    buyer_cons_tbl = Table(
        [
            [
                Paragraph(cons_html, style_text),
                Paragraph(buyer_display_html, style_text),
            ]
        ],
        colWidths=[90 * mm, 90 * mm]
    )
    buyer_cons_tbl.hAlign = 'LEFT'
    buyer_cons_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(buyer_cons_tbl)
    story.append(Spacer(1, 0))

    # SUMMARY BOTTOM (Notify + Origin/Destination): equal-width columns 45/45/45/45
    summary_bottom_data = [
        [
            Paragraph(notify_html, style_text),  # (0,0) merged with (1,0)
            "",
            Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_name}", style_text),
            Paragraph(f"<b>Country of Final Destination</b><br/>{dest_name}", style_text),
        ]
    ]
    summary_bottom = Table(summary_bottom_data, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm])
    summary_bottom.hAlign = 'LEFT'
    summary_bottom.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (0, 0), (1, 0)),  # Notify Party across col 0-1
    ]))
    story.append(summary_bottom)
    story.append(Spacer(1, 0))


    # THIRD TABLE: 6 columns x 2 rows, with last three columns merged across both rows
    # Values sourced from linked ProformaInvoice if available
    # Prefer PackingList header fields, fallback to ProformaInvoice if not set
    pre_carriage_val = safe(str(getattr(packing_list, "pre_carriage", ""))) if getattr(packing_list, "pre_carriage", None) else (safe(str(getattr(pi, "pre_carriage", ""))) if pi and getattr(pi, "pre_carriage", None) else "")
    place_receipt_val = safe(str(getattr(packing_list, "place_of_receipt_by_pre_carrier", ""))) if getattr(packing_list, "place_of_receipt_by_pre_carrier", None) else (safe(str(getattr(pi, "place_of_receipt_by_pre_carrier", ""))) if pi and getattr(pi, "place_of_receipt_by_pre_carrier", None) else "")
    vessel_flight_val = safe(getattr(packing_list, "vessel_flight_no", "")) or (safe(getattr(pi, "vessel_flight_no", "")) if pi else "")
    port_loading_val = safe(str(getattr(packing_list, "port_loading", ""))) if getattr(packing_list, "port_loading", None) else (safe(str(getattr(pi, "port_loading", ""))) if pi and getattr(pi, "port_loading", None) else "")
    port_discharge_val = safe(str(getattr(packing_list, "port_discharge", ""))) if getattr(packing_list, "port_discharge", None) else (safe(str(getattr(pi, "port_discharge", ""))) if pi and getattr(pi, "port_discharge", None) else "")
    final_destination_val = safe(str(getattr(packing_list, "final_destination", ""))) if getattr(packing_list, "final_destination", None) else (safe(str(getattr(pi, "final_destination", ""))) if pi and getattr(pi, "final_destination", None) else "")

    incoterm_str = safe(str(getattr(packing_list, "incoterm", ""))) if getattr(packing_list, "incoterm", None) else (safe(str(getattr(pi, "incoterm", ""))) if pi and getattr(pi, "incoterm", None) else "")
    payment_term_str = safe(str(getattr(packing_list, "payment_term", ""))) if getattr(packing_list, "payment_term", None) else (safe(str(getattr(pi, "payment_term", ""))) if pi and getattr(pi, "payment_term", None) else "")
    terms_merged_html = "<b>Incoterms:</b> " + incoterm_str + ("<br/>" if incoterm_str or payment_term_str else "") + "<b>Payment Terms:</b> " + payment_term_str

    third_data = [
        [
            Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_val}", style_text),              # (0,0)
            Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}", style_text),  # (1,0)
            Paragraph(f"<b>Vessel/Flight No.</b><br/>{vessel_flight_val}", style_text),           # (2,0)
            Paragraph(terms_merged_html, style_text),                                             # (3,0) merged area start
            "",                                                                                   # (4,0)
            "",                                                                                   # (5,0)
        ],
        [
            Paragraph(f"<b>Port of Loading</b><br/>{port_loading_val}", style_text),              # (0,1)
            Paragraph(f"<b>Port of Discharge</b><br/>{port_discharge_val}", style_text),          # (1,1)
            Paragraph(f"<b>Final Destination</b><br/>{final_destination_val}", style_text),       # (2,1)
            "",                                                                                   # (3,1)
            "",                                                                                   # (4,1)
            "",                                                                                   # (5,1)
        ]
    ]
    third_tbl = Table(third_data, colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm])
    third_tbl.hAlign = 'LEFT'
    third_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Merge last three columns (4-6 in 1-based index => 3..5 in 0-based) across both rows
        ('SPAN', (3, 0), (5, 1)),
    ]))
    story.append(third_tbl)
    story.append(Spacer(1, 6))


    # Containers and items
    total_net = Decimal("0.000")
    total_tare = Decimal("0.000")
    total_gross = Decimal("0.000")

    containers_qs = packing_list.containers.filter(is_active=True).order_by("created_at")
    container_index = 0
    for cont in containers_qs:
        container_index += 1
        # Container header block
        cont_header = Table(
            [[
                Paragraph(f"<b>Container:</b> {safe(getattr(cont, 'container_reference', ''))}", style_text),
                Paragraph(f"<b>Marks & Numbers:</b> {safe(getattr(cont, 'marks_and_numbers', ''))}", style_text),
            ]],
            colWidths=[90 * mm, 90 * mm]
        )
        cont_header.hAlign = 'LEFT'
        cont_header.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        # Weights summary for this container
        net_val = getattr(cont, "net_weight", None)
        tare_val = getattr(cont, "tare_weight", None)
        gross_val = getattr(cont, "gross_weight", None)
        try:
            if net_val is not None:
                total_net += Decimal(net_val)
            if tare_val is not None:
                total_tare += Decimal(tare_val)
            if gross_val is not None:
                total_gross += Decimal(gross_val)
            else:
                total_gross += (Decimal(net_val) if net_val is not None else Decimal("0")) + (Decimal(tare_val) if tare_val is not None else Decimal("0"))
        except Exception:
            pass

        weights_table_data = [[
            Paragraph("<b>Net Weight</b>", style_label), Paragraph(_fmt_decimal(net_val, 3) or "-", style_text),
            Paragraph("<b>Tare Weight</b>", style_label), Paragraph(_fmt_decimal(tare_val, 3) or "-", style_text),
            Paragraph("<b>Gross Weight</b>", style_label), Paragraph(_fmt_decimal(gross_val, 3) or "-", style_text),
        ]]
        weights_table = Table(weights_table_data, colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm])
        weights_table.hAlign = 'LEFT'
        weights_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ]))

        # ITEMS TABLE FOR THIS CONTAINER:
        # - colWidths (below) define the exact width of each column and must sum to ~180 mm:
        #   [Sr., HSN/Item, Packages, Description, Qty, Net, Tare, Gross]
        #   Default: [12, 20, 32, 60, 18, 14, 12, 12] mm (sum = 180)
        # - repeatRows=1 will repeat the header on subsequent pages
        # - Reduce paddings to fit more rows per page (see TableStyle paddings)
        # - KeepTogether([cont_header, items_table]) tries to keep header+items on the same page
        # To change column widths, update the 'colWidths' list below but keep the sum at ~180 mm.
        # Items table for this container
        item_header = [
            Paragraph("<b>Sr.</b>", style_label),
            Paragraph("<b>HSN/Item</b>", style_label),
            Paragraph("<b>No & Kind of Packages</b>", style_label),
            Paragraph("<b>Description of Goods</b>", style_label),
            Paragraph("<b>Qty</b>", style_label),
            Paragraph("<b>UOM</b>", style_label),
            Paragraph("<b>Batch Details</b>", style_label),
        ]
        item_rows = [item_header]
        sr = 0
        items_qs = cont.items.filter(is_active=True).order_by("created_at")
        for it in items_qs:
            sr += 1
            # prepare display fields
            hsn_item = " ".join(x for x in [
                safe(getattr(it, "hsn_code", "")),
                f"({safe(getattr(it, 'item_code', ''))})" if getattr(it, "item_code", "") else ""
            ] if x).strip()
            qty_display = _fmt_decimal(getattr(it, "quantity", None))
            uom_display = safe(getattr(it, "uom", ""))


            item_rows.append([
                Paragraph(str(sr), style_text),
                Paragraph(hsn_item or "-", style_text),
                Paragraph(safe(getattr(it, "packages_number_and_kind", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "description_of_goods", "")) or "-", style_text),
                Paragraph(qty_display or "-", style_text),
                Paragraph(uom_display or "-", style_text),
                Paragraph(safe(getattr(it, "batch_details", "")) or "-", style_text),
            ])

        items_table = Table(
            item_rows,
            colWidths=[12 * mm, 20 * mm, 32 * mm, 60 * mm, 18 * mm, 12 * mm, 26 * mm],  # total width = 180 mm
            repeatRows=1
        )
        items_table.hAlign = 'LEFT'
        items_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Sr.
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Qty column
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        block = KeepTogether([cont_header, weights_table, items_table])
        story.append(block)
        story.append(Spacer(1, 6))


    # Totals row for Net, Tare, Gross across all containers
    totals_data = [
        [
            Paragraph("<b>Total Net Weight</b>", style_label), Paragraph(_fmt_decimal(total_net, 3), style_text),
            Paragraph("<b>Total Tare Weight</b>", style_label), Paragraph(_fmt_decimal(total_tare, 3), style_text),
            Paragraph("<b>Total Gross Weight</b>", style_label), Paragraph(_fmt_decimal(total_gross, 3), style_text),
        ]
    ]
    totals_tbl = Table(totals_data, colWidths=[34 * mm, 26 * mm, 34 * mm, 26 * mm, 34 * mm, 26 * mm])
    totals_tbl.hAlign = 'LEFT'
    totals_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
        ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 6))

    # Optional note about units
    story.append(Paragraph("Quantities and UOM as per container item details.", style_small))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes