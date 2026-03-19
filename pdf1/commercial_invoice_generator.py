"""
PDF Generation for Commercial Invoices using ReportLab

This module generates Draft and Final PDF versions of Commercial Invoices.
- Draft PDF is available before approval and shows a diagonal 'DRAFT' watermark
- Final PDF is available only after approval

Layout is simplified and consistent with proforma style:
- Company header
- Invoice summary table
- Line items table
- Totals section
- Bank/beneficiary section

COMMERCIAL INVOICE PDF LAYOUT GUIDE (ASCII VISUAL + HOW TO TWEAK)
This guide mirrors the style used in the Packing List generator and explains
the layout so you can safely adjust widths/paddings/fonts if needed.

PAGE:
- A4 portrait (210mm x 297mm)
- Margins: left=15mm, right=15mm, top=10mm, bottom=15mm
- Effective content width ≈ 210 - (15+15) = 180mm (target width for tables)

STORY ORDER:
1) Company header (centered)
2) Title "COMMERCIAL INVOICE" (centered)
3) Summary grid (1 row x 4 columns)
4) Line items table (with headers)
5) Totals section (amount local + total USD)
6) Bank/Beneficiary block (single column)
7) Declaration (paragraph)
8) Footer on each page (canvas callback)

SUMMARY GRID (Total width = 180mm):
- Single row, four columns with widths: [60mm | 40mm | 50mm | 30mm]
- Cells (left to right):
  (0) Exporter block (multi-line)
  (1) Invoice No & Date
  (2) Consignee (multi-line)
  (3) Incoterms / Payment

ASCII:
┌──────────────────────────────┬────────────────┬─────────────────────────┬──────────────┐
│ Exporter                     │ Invoice No &   │ Consignee               │ Incoterms /  │
│ name, addr, country, email   │ Date           │ name, addr, country,    │ Payment      │
│                              │                │ email                   │              │
└──────────────────────────────┴────────────────┴─────────────────────────┴──────────────┘
   60mm                           40mm               50mm                     30mm   Total=180mm

LINE ITEMS TABLE (Total width ≈ 180mm):
- Columns (mm): [10 | 24 | 24 | 60 | 18 | 22 | 22]
- Headers: Sr. | HSN Code | Item Code | Description of Goods | Qty | Rate (USD) | Amount (USD)

ASCII (widths annotated):
┌────┬──────────┬──────────┬────────────────────────────────────────┬──────┬────────────┬────────────┐
│ Sr │ HSN Code │ Item     │ Description of Goods                  │ Qty  │ Rate (USD) │ Amount     │
│10mm│ 24mm     │ 24mm     │ 60mm                                   │ 18mm │ 22mm       │ 22mm       │
├────┼──────────┼──────────┼────────────────────────────────────────┼──────┼────────────┼────────────┤
│ rows… (Qty/Rate/Amount right-aligned)                                                                   │
└────┴──────────┴──────────┴────────────────────────────────────────┴──────┴────────────┴────────────┘

TOTALS SECTION (Total width = 180mm):
- Four cells, widths: [50mm | 40mm | 60mm | 30mm]
  [Amount (Local) | value] [Total Amount (USD) | $value]

ASCII:
┌──────────────────────┬──────────┬────────────────────────────┬─────────┐
│ Amount (Local)       │ value    │ Total Amount (USD)         │ $value  │
└──────────────────────┴──────────┴────────────────────────────┴─────────┘
   50mm                  40mm         60mm                        30mm   Total=180mm

BANK / BENEFICIARY SECTION (Total width = 180mm):
- Single column table, width 180mm, multiple stacked rows:
  - BENEFICIARY NAME
  - BANK NAME
  - BRANCH NAME
  - BRANCH ADDRESS
  - A/C NO.
  - SWIFT CODE

HOW TO MODIFY:
- Adjust table widths by editing the colWidths lists near their respective Table(...) definitions.
  Keep the total ≈180mm to fit within margins.
- Tweak paddings via TableStyle LEFT/RIGHT/TOP/BOTTOMPADDING entries.
- Change fonts/sizes in _styles() ParagraphStyles.
- Right-alignment for numeric cells is controlled via TableStyle 'ALIGN' directives.
- The "DRAFT" watermark and footer are drawn in canvas callbacks (_draft_watermark and _footer).

WATERMARK/FOOTER:
- Draft watermark is applied in on_page() when draft=True.
- Footer is centered text applied to each page via on_page().
"""

import re
from io import BytesIO
from typing import Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from num2words import num2words


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
        n = int(float(n or 0))
        words = num2words(n).title()
        return f"{words} {currency} Only"
    except Exception:
        return ""


def _styles():
    styles = getSampleStyleSheet()
    style_company_header = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=16,
        leading=20,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=12,
        leading=15,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "Text",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
    )
    style_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )
    return style_company_header, style_title, style_label, style_text, style_small


def _footer(canvas, doc):
    canvas.saveState()
    page_width = A4[0]
    footer_text = "This is a computer-generated document. Signature is not required."
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(page_width / 2, 10 * mm, footer_text)
    canvas.restoreState()


def _draft_watermark(canvas):
    # Large diagonal DRAFT watermark
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 60)
    canvas.setFillColorRGB(0.9, 0.3, 0.3, 0.12)  # Light red with alpha simulated via light color
    canvas.translate(300, 400)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "DRAFT")
    canvas.restoreState()


def generate_commercial_invoice_pdf_bytes(invoice, draft: bool = False) -> bytes:
    """
    Build Commercial Invoice PDF bytes.

    Args:
        invoice: CommercialInvoice instance
        draft: If True, includes 'DRAFT' watermark and intended for pre-approval viewing
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

    style_company_header, style_title, style_label, style_text, style_small = _styles()

    story = []

    # Header
    exp = invoice.exporter
    cons = invoice.consignee
    bank = invoice.bank

    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("COMMERCIAL INVOICE", style_title))
    story.append(Spacer(1, 8))

    # SUMMARY BLOCKS above line items (sourced from the linked Packing List)
    # Grid: 2 rows x 4 columns with widths [60mm | 60mm | 30mm | 30mm]
    # Row 0: "Exporter:" spans col 0-1, PI No/Date in col 2, col 3 reserved (blank)
    # Row 1: Corporate Office | Registered Office | References (spans col 2-3)
    pl = getattr(invoice, "packing_list", None)
    pi = getattr(pl, "proforma_invoice", None) if pl else None

    # Exporter details
    exp_lines = []
    exp_lines.append(safe(getattr(exp, "name", "")))
    # IEC Code
    if getattr(exp, "iec_code", ""):
        exp_lines.append(f"IEC Code: {safe(getattr(exp, 'iec_code', ''))}")
    if getattr(exp, "address", ""):
        exp_lines.append(safe(getattr(exp, "address", "")))
    if getattr(exp, "country", None):
        exp_country = getattr(exp, "country", None)
        exp_lines.append(safe(getattr(exp_country, "name", exp_country)))
    if getattr(exp, "email_id", ""):
        exp_lines.append(safe(getattr(exp, "email_id", "")))
    exporter_details_html = "<b>Corporate Office</b><br/>" + "<br/>".join([ln for ln in exp_lines if ln])

    # Registered address
    reg = getattr(exp, "registered_address_details", None)
    reg_lines = []
    if reg:
        if getattr(reg, "name", ""):
            reg_lines.append(safe(getattr(reg, "name", "")))
        if getattr(reg, "address", ""):
            reg_lines.append(safe(getattr(reg, "address", "")))
        if getattr(reg, "country", None):
            reg_country = getattr(reg, "country", None)
            reg_lines.append(safe(getattr(reg_country, "name", reg_country)))
        contact_bits = []
        if getattr(reg, "phone", ""):
            contact_bits.append(f"Phone: {safe(getattr(reg, 'phone', ''))}")
        if getattr(reg, "email", ""):
            contact_bits.append(f"Email: {safe(getattr(reg, 'email', ''))}")
        if contact_bits:
            reg_lines.append(" • ".join(contact_bits))
    reg_html = "<b>Registered Office</b><br/>" + "<br/>".join([ln for ln in reg_lines if ln])

    # References from Packing List
    ref_lines = []
    po_no = safe(getattr(pl, "po_number", "")) if pl else ""
    po_date = safe(getattr(pl, "po_date", "")) if (pl and getattr(pl, "po_date", None)) else ""
    lc_no = safe(getattr(pl, "lc_number", "")) if pl else ""
    lc_date = safe(getattr(pl, "lc_date", "")) if (pl and getattr(pl, "lc_date", None)) else ""
    bl_no = safe(getattr(pl, "bl_number", "")) if pl else ""
    bl_date = safe(getattr(pl, "bl_date", "")) if (pl and getattr(pl, "bl_date", None)) else ""
    so_no = safe(getattr(pl, "so_number", "")) if pl else ""
    so_date = safe(getattr(pl, "so_date", "")) if (pl and getattr(pl, "so_date", None)) else ""
    other_ref = safe(getattr(pl, "other_ref", "")) if pl else ""
    other_ref_date = safe(getattr(pl, "other_ref_date", "")) if (pl and getattr(pl, "other_ref_date", None)) else ""

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

    ci_no_date = ""
    ci_no = safe(getattr(invoice, "invoice_number", "")) or safe(getattr(invoice, "number", ""))
    ci_dt = safe(getattr(invoice, "date", ""))
    ci_no_date = f"{ci_no}{(' / ' + ci_dt) if ci_dt else ''}"

    summary_top_data = [
        [
            Paragraph("<b>Exporter:</b>", style_label),  # (0,0) spans 0-1
            "",
            Paragraph(f"<b>Invoice Date:</b><br/>{ci_dt}", style_text),  # (2,0)
            Paragraph(f"<b>Invoice No:</b><br/>{ci_no}", style_text),  # (3,0)
        ],
        [
            Paragraph(exporter_details_html, style_text),  # (0,1)
            Paragraph(reg_html, style_text),               # (1,1)
            Paragraph("<br/>".join(ref_lines), style_text),# (2,1)
            "",                                            # (3,1) merged with (2,1)
        ],
    ]
    summary_top = Table(summary_top_data, colWidths=[60 * mm, 60 * mm, 30 * mm, 30 * mm])
    summary_top.hAlign = 'LEFT'
    summary_top.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (0, 0), (1, 0)),  # "Exporter:" across col 0-1
        ('SPAN', (2, 1), (3, 1)),  # References across col 2-3
    ]))
    story.append(summary_top)
    story.append(Spacer(1, 0))

    # NOTIFY PARTY (captured for row with country columns)
    notify_text = safe(getattr(pl, "notify_party", "")) if pl else ""

    # Consignee and Buyer blocks (two columns)
    cons_lines = []
    cons_name = safe(getattr(cons, "name", ""))
    cons_addr = safe(getattr(cons, "address", ""))
    cons_country = safe(getattr(getattr(cons, "country", None), "name", None))
    cons_email = safe(getattr(cons, "email_id", ""))
    if cons_name: cons_lines.append(cons_name)
    if cons_addr: cons_lines.append(cons_addr)
    if cons_country: cons_lines.append(cons_country)
    if cons_email: cons_lines.append(cons_email)
    consignee_html = "<br/>".join(cons_lines)

    buyer_obj = getattr(invoice, "buyer", None)
    buyer_lines = []
    if buyer_obj:
        b_name = safe(getattr(buyer_obj, "name", ""))
        b_addr = safe(getattr(buyer_obj, "address", ""))
        b_country = safe(getattr(getattr(buyer_obj, "country", None), "name", None))
        b_email = safe(getattr(buyer_obj, "email", ""))
        if b_name: buyer_lines.append(b_name)
        if b_addr: buyer_lines.append(b_addr)
        if b_country: buyer_lines.append(b_country)
        if b_email: buyer_lines.append(b_email)
    buyer_html = "<br/>".join([ln for ln in buyer_lines if ln])

    cons_buyer_data = [[
        Paragraph("<b>Consignee</b><br/>" + consignee_html, style_text),
        Paragraph("<b>Buyer</b><br/>" + (buyer_html or ""), style_text),
    ]]
    cons_buyer_tbl = Table(cons_buyer_data, colWidths=[90 * mm, 90 * mm])
    cons_buyer_tbl.hAlign = 'LEFT'
    cons_buyer_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(cons_buyer_tbl)
    story.append(Spacer(1, 0))

    # Countries (origin/destination) + Notify Party on same row
    origin_country_name = ""
    final_destination_country_name = ""
    if pl and getattr(pl, "origin_country", None):
        origin_country_name = safe(getattr(pl.origin_country, "name", ""))
    else:
        origin_country_name = safe(getattr(getattr(exp, "country", None), "name", None))
    if pl and getattr(pl, "final_destination_country", None):
        final_destination_country_name = safe(getattr(pl.final_destination_country, "name", ""))
    else:
        fd_obj = getattr(pl, "final_destination", None) if pl else None
        final_destination_country_name = safe(getattr(getattr(fd_obj, "country", None), "name", None))

    notify_countries_data = [[
        Paragraph("<b>Notify Party</b><br/>" + (notify_text or ""), style_text),
        Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_country_name}", style_text),
        Paragraph(f"<b>Country of Final Destination</b><br/>{final_destination_country_name}", style_text),
    ]]
    notify_countries_tbl = Table(notify_countries_data, colWidths=[90 * mm, 45 * mm, 45 * mm])
    notify_countries_tbl.hAlign = 'LEFT'
    notify_countries_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(notify_countries_tbl)
    story.append(Spacer(1, 0))

    # Pre-carriage / Receipt / Vessel / Incoterms / Payment Terms
    pre_carriage_name = safe(getattr(getattr(pl, "pre_carriage", None), "name", None)) if pl else ""
    por_pre = safe(getattr(getattr(pl, "place_of_receipt_by_pre_carrier", None), "name", None)) if pl else ""
    vessel_no = safe(getattr(pl, "vessel_flight_no", "")) if pl else ""
    incoterm_code = safe(getattr(getattr(invoice, "incoterm", None), "code", None))
    payment_term_name = safe(getattr(getattr(invoice, "payment_term", None), "name", None))

    # Ports (names) from PL for combined table
    pol = safe(getattr(getattr(pl, "port_loading", None), "name", None)) if pl else ""
    pod = safe(getattr(getattr(pl, "port_discharge", None), "name", None)) if pl else ""
    final_dest_name = safe(getattr(getattr(pl, "final_destination", None), "name", None)) if pl else ""

    # Combined Shipping & Ports table: 2 rows x 6 columns (30mm each, total 180mm)
    combined_data = [
        [
            Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_name}", style_text),
            Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{por_pre}", style_text),
            Paragraph(f"<b>Vessel/Flight No.</b><br/>{vessel_no}", style_text),
            Paragraph(f"<b>Incoterms</b><br/>{incoterm_code}<br/><b>Payment Terms</b><br/>{payment_term_name}", style_text),
            "",  # merged area (part 2)
            "",  # merged area (part 3)
        ],
        [
            Paragraph(f"<b>Port of Loading</b><br/>{pol}", style_text),
            Paragraph(f"<b>Port of Discharge</b><br/>{pod}", style_text),
            Paragraph(f"<b>Final Destination</b><br/>{final_dest_name}", style_text),
            "", "", ""
        ]
    ]
    combined_tbl = Table(combined_data, colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm])
    combined_tbl.hAlign = 'LEFT'
    combined_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Merge the Incoterms/Payment Terms cell across Row 0 Col 4 to Row 1 Col 6 (0-based: (3,0) to (5,1))
        ('SPAN', (3, 0), (5, 1)),
    ]))
    story.append(combined_tbl)
    story.append(Spacer(1, 6))


    # Ports section merged into combined shipping/ports table above




    # Line items
    li_header = [
        Paragraph("<b>Sr.</b>", style_label),
        Paragraph("<b>HSN Code</b>", style_label),
        Paragraph("<b>No & Kind of Packages</b>", style_label),
        Paragraph("<b>Item Code</b>", style_label),
        Paragraph("<b>Description of Goods</b>", style_label),
        Paragraph("<b>Qty</b>", style_label),
        Paragraph("<b>Rate (USD)</b>", style_label),
        Paragraph("<b>Amount (USD)</b>", style_label),
    ]
    li_rows = [li_header]

    # Build packages lookup from Packing List container items (by item_code)
    packages_map = {}
    try:
        if pl:
            for cnt in pl.containers.filter(is_active=True):
                for pitem in cnt.items.filter(is_active=True):
                    key = safe(getattr(pitem, "item_code", ""))
                    val = safe(getattr(pitem, "packages_number_and_kind", ""))
                    if not key:
                        continue
                    if key not in packages_map:
                        packages_map[key] = set()
                    if val:
                        packages_map[key].add(val)
    except Exception:
        pass

    items_qs = invoice.line_items.filter(is_active=True).order_by("created_at")
    idx = 0
    for it in items_qs:
        idx += 1
        pkg_text = ""
        try:
            pkset = packages_map.get(safe(getattr(it, "item_code", "")), None)
            if pkset:
                pkg_text = " ; ".join(sorted(list(pkset)))
        except Exception:
            pass
        li_rows.append([
            Paragraph(str(idx), style_text),
            Paragraph(safe(it.hs_code), style_text),
            Paragraph(safe(pkg_text), style_text),
            Paragraph(safe(it.item_code), style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{fmt_qty(it.quantity)} {safe(it.unit)}", style_text),
            Paragraph(fmt_money(it.unit_price_usd), style_text),
            Paragraph(fmt_money(it.amount_usd), style_text),
        ])

    li_table = Table(li_rows, colWidths=[10 * mm, 22 * mm, 28 * mm, 22 * mm, 52 * mm, 16 * mm, 15 * mm, 15 * mm])
    li_table.hAlign = 'LEFT'
    li_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 10))

    # Totals (from Packing List) and Charges (from Commercial Invoice) - moved below line items
    total_net_val = 0
    total_gross_val = 0
    try:
        if pl:
            for c in pl.containers.filter(is_active=True):
                try:
                    total_net_val += float(c.net_weight or 0)
                except Exception:
                    total_net_val += (c.net_weight or 0) or 0
                try:
                    total_gross_val += float(c.gross_weight or 0)
                except Exception:
                    total_gross_val += (c.gross_weight or 0) or 0
    except Exception:
        pass

    lc_details_val = safe(getattr(invoice, "lc_details", ""))

    fob_rate_val = fmt_money(getattr(invoice, "fob_rate", 0))
    freight_val = fmt_money(getattr(invoice, "freight", 0))
    insurance_val = fmt_money(getattr(invoice, "insurance", 0))

    totals_charges_data = [
        [
            Paragraph(f"<b>Total Net Weight:</b> {fmt_qty(total_net_val)}", style_text),
            Paragraph(f"<b>FOB Rate:</b> {fob_rate_val}", style_text),
        ],
        [
            Paragraph(f"<b>Total Gross Weight:</b> {fmt_qty(total_gross_val)}", style_text),
            Paragraph(f"<b>Freight:</b> {freight_val}", style_text),
        ],
        [
            Paragraph(f"<b>L/C Details:</b> {lc_details_val}", style_text),
            Paragraph(f"<b>Insurance:</b> {insurance_val}", style_text),
        ],
    ]
    totals_charges_tbl = Table(totals_charges_data, colWidths=[90 * mm, 90 * mm])
    totals_charges_tbl.hAlign = 'LEFT'
    totals_charges_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_charges_tbl)
    story.append(Spacer(1, 6))

    # Totals section
    total_usd = fmt_money(invoice.total_amount_usd)
    amount_local = fmt_money(invoice.amount)

    totals_data = [[
        Paragraph("<b>Amount (Local):</b>", style_text),
        Paragraph(amount_local, style_text),
        Paragraph("<b>Total Amount (USD):</b>", style_text),
        Paragraph(f"${total_usd}", style_text),
    ]]
    totals_table = Table(totals_data, colWidths=[50 * mm, 40 * mm, 60 * mm, 30 * mm])
    totals_table.hAlign = 'LEFT'
    totals_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 6))

    # Amount in words (USD only)
    amount_in_words_str = amount_to_words(invoice.total_amount_usd, currency="USD")
    if amount_in_words_str:
        story.append(Paragraph(f"<b>Amount in Words:</b> {amount_in_words_str}", style_text))
        story.append(Spacer(1, 10))

    # Declaration above bank table
    story.append(Paragraph("Declaration: We declare that this invoice shows actual price of the goods described and that all particulars are true and correct.", style_text))
    story.append(Spacer(1, 6))

    # Bank details section (if available)
    if bank:
        beneficiary_data = [
            [Paragraph(f"<b>BENEFICIARY NAME:</b> {safe(getattr(bank, 'beneficiary_name', ''))}", style_text)],
            [Paragraph(f"<b>BANK NAME:</b> {safe(getattr(bank, 'bank_name', ''))}", style_text)],
            [Paragraph(f"<b>BRANCH NAME:</b> {safe(getattr(bank, 'branch_name', ''))}", style_text)],
            [Paragraph(f"<b>BRANCH ADDRESS:</b> {safe(getattr(bank, 'branch_address', ''))}", style_text)],
            [Paragraph(f"<b>A/C NO.:</b> {safe(getattr(bank, 'account_number', ''))}", style_text)],
            [Paragraph(f"<b>SWIFT CODE:</b> {safe(getattr(bank, 'swift_code', ''))}", style_text)],
        ]
        beneficiary_table = Table(beneficiary_data, colWidths=[180 * mm])
        beneficiary_table.hAlign = 'LEFT'
        beneficiary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(beneficiary_table)
        story.append(Spacer(1, 10))


    # Build callbacks
    def on_page(canvas, doc):
        if draft:
            _draft_watermark(canvas)
        _footer(canvas, doc)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes