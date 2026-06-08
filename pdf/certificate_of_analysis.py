"""
Certificate of Analysis PDF Generator
Returns bytes in-memory — never writes to disk (Rule #9).
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether

NAVY = colors.HexColor('#1A2B4B')
LIGHT_GREY = colors.HexColor('#F0F0F0')
ROW_TINT = colors.HexColor('#EEF1FF')

# Matches the _GRID_STYLE used by packing_list_generator for visual consistency
_GRID_STYLE = [
    ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]


def _safe(v, default=""):
    """Coerce None or any value to a safe string."""
    return default if v is None else str(v)


def _fmt_date(d):
    """Format a date object as DD.MM.YYYY, returning 'XXXX' if None."""
    if d is None:
        return "XXXX"
    try:
        return d.strftime("%d.%m.%Y")
    except Exception:
        return str(d)


def _fmt_datetime(dt):
    """Format a datetime object as DD.MM.YYYY – HH:MM."""
    if dt is None:
        return ""
    try:
        return dt.strftime("%d.%m.%Y \u2013 %H:%M")
    except Exception:
        return str(dt)


def generate_coa_pdf(coa) -> BytesIO:
    """
    Generate a COA PDF for the given CertificateOfAnalysis instance.
    Returns a BytesIO buffer ready to stream — never written to disk.
    """
    from apps.workflow.constants import APPROVED
    from datetime import date as date_class

    buf = BytesIO()

    styles = getSampleStyleSheet()

    style_company = ParagraphStyle(
        "COACompany", parent=styles["Normal"],
        fontSize=18, leading=22, spaceAfter=2,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "COATitle", parent=styles["Normal"],
        fontSize=13, leading=16, spaceAfter=14,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_small = ParagraphStyle(
        "COASmall", parent=styles["Normal"],
        fontSize=8, leading=11, alignment=TA_CENTER,
    )
    style_label = ParagraphStyle(
        "COALabel", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "COAText", parent=styles["Normal"],
        fontSize=9, leading=12,
    )
    style_label_white_center = ParagraphStyle(
        "COALabelWhiteCenter", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )
    style_text_white_center = ParagraphStyle(
        "COATextWhiteCenter", parent=styles["Normal"],
        fontSize=9, leading=12,
        textColor=colors.white, alignment=TA_CENTER,
    )
    style_tbl_hdr = ParagraphStyle(
        "COATblHdr", parent=styles["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )
    style_tbl_cell = ParagraphStyle(
        "COATblCell", parent=styles["Normal"],
        fontSize=9, leading=11,
    )
    style_sig = ParagraphStyle(
        "COASig", parent=styles["Normal"],
        fontSize=9, leading=14, alignment=TA_CENTER,
    )

    # -------------------------------------------------------------------------
    # Gather org / address data (used in both header and footer callback)
    # -------------------------------------------------------------------------
    org = coa.footer_organisation
    org_name = _safe(org.name) if org else ""

    org_addresses = []
    if org:
        for addr in org.addresses.select_related("country").all():
            parts = [addr.line1]
            if addr.line2:
                parts.append(addr.line2)
            parts.append(addr.city)
            if addr.state:
                parts.append(addr.state)
            if addr.pin:
                parts.append(addr.pin)
            org_addresses.append(", ".join(parts))

    # CIN — from first address where tax_type contains "CIN"
    cin = ""
    if org:
        for addr in org.addresses.all():
            if addr.tax_type and "CIN" in addr.tax_type.upper():
                cin = addr.tax_code
                break

    is_draft = coa.status != APPROVED

    # -------------------------------------------------------------------------
    # Canvas callbacks — footer with hairline rule + disclaimer + page number
    # and DRAFT watermark for non-approved documents
    # -------------------------------------------------------------------------
    def _on_page(canvas, doc):
        if is_draft:
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 80)
            canvas.setFillColor(colors.HexColor('#CC0000'), alpha=0.15)
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DRAFT")
            canvas.restoreState()

        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, 17 * mm, A4[0] - 15 * mm, 17 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 12 * mm,
            "This is a computer generated document and does not require signature",
        )
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0] / 2, 8 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    PAGE_W = 180 * mm
    col_third = PAGE_W / 3

    story = []

    # -------------------------------------------------------------------------
    # 1. Company header block
    # -------------------------------------------------------------------------
    story.append(Paragraph(org_name, style_company))
    if cin:
        story.append(Paragraph(f"CIN: {cin}", style_small))
    for addr_text in org_addresses:
        story.append(Paragraph(addr_text, style_small))

    # Hairline separator (matches PL style)
    sep = Table([[""]], colWidths=[PAGE_W])
    sep.setStyle(TableStyle([
        ("LINEABOVE",      (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING",     (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(sep)
    story.append(Spacer(1, 6))

    # -------------------------------------------------------------------------
    # 2. Document title + COA number
    # -------------------------------------------------------------------------
    story.append(Paragraph("Certificate of Analysis", style_title))

    # -------------------------------------------------------------------------
    # 3. Header info block — COA No. / Product / Customer in a navy header row
    # -------------------------------------------------------------------------
    pg = coa.product_grade
    product_name = pg.product.name if pg else ""
    grade_str = pg.grade if pg else ""
    customer_name = coa.customer.name if coa.customer else ""

    coa_header_data = [[
        Paragraph(f"<b>COA No.</b><br/>{_safe(coa.coa_number)}", style_text_white_center),
        Paragraph(f"<b>Product / Grade</b><br/>{product_name} / {grade_str}", style_text_white_center),
        Paragraph(f"<b>Customer</b><br/>{customer_name}", style_text_white_center),
    ]]
    coa_header_tbl = Table(coa_header_data, colWidths=[col_third, col_third, col_third])
    coa_header_tbl.setStyle(TableStyle(_GRID_STYLE + [
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR",  (0, 0), (-1, -1), colors.white),
    ]))
    coa_header_tbl.hAlign = "LEFT"
    story.append(coa_header_tbl)

    # -------------------------------------------------------------------------
    # 4. Info rows — batch, dates, quantities
    # -------------------------------------------------------------------------
    try:
        vol_str = f"{coa.package_volume.normalize():f}".rstrip("0").rstrip(".")
    except Exception:
        vol_str = str(coa.package_volume or "")
    uom_abbr = coa.package_uom.abbreviation if coa.package_uom else ""
    pkg_type_name = coa.package_type.name if coa.package_type else ""
    supplied_qty = f"{coa.package_count} x {vol_str} {uom_abbr} {pkg_type_name}"

    date_despatch = _fmt_date(coa.date_of_despatch) if coa.date_of_despatch else "XXXX"

    # Optional PL / CI reference rows
    pl_ci_rows = []
    if coa.packing_list_id:
        pl_ci_rows.append(("Packing List No.", _safe(coa.packing_list.pl_number)))
        try:
            ci_num = coa.packing_list.commercial_invoice.ci_number
            if ci_num:
                pl_ci_rows.append(("Commercial Invoice No.", _safe(ci_num)))
        except Exception:
            pass

    info_rows = [
        ("Batch No.", _safe(coa.batch_number)),
        ("Supplied Quantity", supplied_qty),
        ("Date of Despatch", date_despatch),
        ("Date of Manufacture", _fmt_date(coa.date_of_manufacture)),
        ("Date of Retest", _fmt_date(coa.date_of_retest)),
        ("Date and Time of Sampling", _fmt_datetime(coa.date_time_of_sampling)),
        ("Date and Time of Analysis", _fmt_datetime(coa.date_time_of_analysis)),
        *pl_ci_rows,
    ]

    info_data = [
        [Paragraph(f"<b>{label}</b>", style_label), Paragraph(value, style_text)]
        for label, value in info_rows
    ]
    info_table = Table(info_data, colWidths=[PAGE_W * 0.42, PAGE_W * 0.58])
    info_table.setStyle(TableStyle(_GRID_STYLE))
    info_table.hAlign = "LEFT"
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    # -------------------------------------------------------------------------
    # 5. Test parameters table
    # Columns: S.No | Characteristic | Unit | Spec Min | Spec Max | Specification | Results | Test Method
    # -------------------------------------------------------------------------
    col_widths = [
        PAGE_W * 0.05,   # S.No
        PAGE_W * 0.22,   # Characteristic
        PAGE_W * 0.08,   # Unit
        PAGE_W * 0.10,   # Spec Min
        PAGE_W * 0.10,   # Spec Max
        PAGE_W * 0.15,   # Spec Description
        PAGE_W * 0.15,   # Results
        PAGE_W * 0.15,   # Test Method
    ]

    # Section header row spanning all columns
    section_hdr = [[
        Paragraph("<b>TEST RESULTS</b>", style_label_white_center),
        "", "", "", "", "", "", "",
    ]]
    col_headers = [[
        Paragraph("<b>S.No</b>", style_tbl_hdr),
        Paragraph("<b>Characteristic</b>", style_tbl_hdr),
        Paragraph("<b>Unit</b>", style_tbl_hdr),
        Paragraph("<b>Spec Min</b>", style_tbl_hdr),
        Paragraph("<b>Spec Max</b>", style_tbl_hdr),
        Paragraph("<b>Specification</b>", style_tbl_hdr),
        Paragraph("<b>Results</b>", style_tbl_hdr),
        Paragraph("<b>Test Method</b>", style_tbl_hdr),
    ]]

    table_data = section_hdr + col_headers

    params = list(coa.parameters.select_related("unit", "parameter", "test_method").all())
    for p in params:
        unit_str = p.unit.abbreviation if p.unit else "\u2013"
        if p.spec_type == "QUANTITATIVE":
            spec_min_str = str(p.spec_min).rstrip("0").rstrip(".") if p.spec_min is not None else "\u2013"
            spec_max_str = str(p.spec_max).rstrip("0").rstrip(".") if p.spec_max is not None else "\u2013"
            spec_desc_str = ""
            result_str = str(p.result_value).rstrip("0").rstrip(".") if p.result_value is not None else ""
        else:
            spec_min_str = ""
            spec_max_str = ""
            spec_desc_str = _safe(p.spec_description)
            result_str = _safe(p.result_text)

        method_str = p.test_method.code if p.test_method else ""

        table_data.append([
            Paragraph(str(p.s_no), style_tbl_cell),
            Paragraph(_safe(p.parameter.name if p.parameter else ""), style_tbl_cell),
            Paragraph(unit_str, style_tbl_cell),
            Paragraph(spec_min_str, style_tbl_cell),
            Paragraph(spec_max_str, style_tbl_cell),
            Paragraph(spec_desc_str, style_tbl_cell),
            Paragraph(result_str, style_tbl_cell),
            Paragraph(method_str, style_tbl_cell),
        ])

    param_table = Table(table_data, colWidths=col_widths, repeatRows=2)

    tbl_style = [
        ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # Row 0: full-width section title
        ("SPAN",       (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        # Row 1: column header row
        ("BACKGROUND", (0, 1), (-1, 1), NAVY),
        ("TEXTCOLOR",  (0, 1), (-1, 1), colors.white),
        ("ALIGN",      (0, 1), (-1, 1), "CENTER"),
    ]
    # Alternating row shading starting from first data row (index 2)
    for i in range(2, len(table_data)):
        if i % 2 == 0:
            tbl_style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))

    param_table.setStyle(TableStyle(tbl_style))
    param_table.hAlign = "LEFT"
    story.append(param_table)
    story.append(Spacer(1, 8 * mm))

    # -------------------------------------------------------------------------
    # 6. Signature section — analyst and QC incharge
    # -------------------------------------------------------------------------
    if coa.status == APPROVED:
        sig_date = _fmt_date(coa.updated_at.date())
    else:
        sig_date = _fmt_date(date_class.today())

    analyst_col = (
        "_________________________<br/>"
        "Analyst<br/>"
        f"{_safe(coa.analyst_name)}<br/>"
        f"Date : {sig_date}"
    )
    qc_col = (
        "_________________________<br/>"
        "QC Incharge<br/>"
        f"{_safe(coa.qc_incharge_name)}<br/>"
        f"Date : {sig_date}"
    )

    sig_data = [[
        Paragraph(analyst_col, style_sig),
        Paragraph("", style_sig),   # Center column: company seal placeholder
        Paragraph(qc_col, style_sig),
    ]]
    sig_table = Table(sig_data, colWidths=[col_third, col_third, col_third])
    sig_table.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    sig_table.hAlign = "LEFT"
    story.append(KeepTogether([sig_table]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf
