"""
Certificate of Analysis PDF Generator
Returns bytes in-memory — never writes to disk (Rule #9).
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.colors import HexColor, white

# Import shared design constants
from pdf.base import (
    FONT_HEADING, FONT_LABEL, FONT_BODY,
    SIZE_COMPANY, SIZE_DOC_TITLE, SIZE_BODY, SIZE_TABLE, SIZE_TABLE_HDR,
    MARGIN_H, MARGIN_TOP, MARGIN_BOTTOM, CONTENT_W,
)

NAVY = HexColor('#1a2a5e')
LIGHT_GREY = HexColor('#F0F0F0')


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
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP + 5 * mm,
        bottomMargin=MARGIN_BOTTOM,
    )

    body_style = ParagraphStyle("coa_body", fontName=FONT_BODY, fontSize=SIZE_BODY, leading=13)
    header_label_style = ParagraphStyle("coa_header_lbl", fontName=FONT_LABEL, fontSize=SIZE_BODY, leading=13)
    table_hdr_style = ParagraphStyle("coa_tbl_hdr", fontName=FONT_LABEL, fontSize=SIZE_TABLE_HDR, textColor=white, leading=11)
    table_cell_style = ParagraphStyle("coa_tbl_cell", fontName=FONT_BODY, fontSize=SIZE_TABLE, leading=11)
    small_style = ParagraphStyle("coa_small", fontName=FONT_BODY, fontSize=7, leading=10)
    sig_style = ParagraphStyle("sig", fontName=FONT_BODY, fontSize=SIZE_BODY, alignment=TA_CENTER, leading=14)
    footer_style = ParagraphStyle("footer", fontName=FONT_BODY, fontSize=7, alignment=TA_CENTER, leading=10)

    story = []

    # -------------------------------------------------------------------------
    # 1. Company header block — uses footer_organisation for company details
    # -------------------------------------------------------------------------
    org = coa.footer_organisation
    org_name = _safe(org.name) if org else ""

    # Build address lines from all addresses on the footer org
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

    header_data = [[
        Paragraph(
            f"<b>{org_name}</b>",
            ParagraphStyle("org_name", fontName=FONT_HEADING, fontSize=SIZE_COMPANY, leading=22),
        )
    ]]
    if cin:
        header_data.append([Paragraph(f"CIN: {cin}", body_style)])
    for addr_text in org_addresses:
        header_data.append([Paragraph(addr_text, small_style)])

    header_table = Table(header_data, colWidths=[CONTENT_W])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------------------
    # 2. Document title + COA number
    # -------------------------------------------------------------------------
    story.append(Paragraph(
        "<u><b>Certificate of Analysis</b></u>",
        ParagraphStyle(
            "coa_title", fontName=FONT_HEADING, fontSize=SIZE_DOC_TITLE + 1,
            alignment=TA_CENTER, leading=18, spaceAfter=4,
        ),
    ))
    story.append(Paragraph(
        f"<b>{_safe(coa.coa_number)}</b>",
        ParagraphStyle(
            "coa_num", fontName=FONT_LABEL, fontSize=SIZE_BODY,
            alignment=TA_CENTER, leading=13, spaceAfter=4,
        ),
    ))
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------------------
    # 3. Header info block — product, customer, batch, dates, etc.
    # -------------------------------------------------------------------------
    pg = coa.product_grade
    product_name = pg.product.name if pg else ""
    grade = pg.grade if pg else ""
    customer_name = coa.customer.name if coa.customer else ""

    # Supplied quantity: "N x V uom package_type"
    try:
        vol_str = f"{coa.package_volume.normalize():f}".rstrip("0").rstrip(".")
    except Exception:
        vol_str = str(coa.package_volume or "")
    uom_abbr = coa.package_uom.abbreviation if coa.package_uom else ""
    pkg_type_name = coa.package_type.name if coa.package_type else ""
    supplied_qty = f"{coa.package_count} x {vol_str} {uom_abbr} {pkg_type_name}"

    date_despatch = _fmt_date(coa.date_of_despatch) if coa.date_of_despatch else "XXXX"

    info_rows = [
        ("Name of the Product", product_name),
        ("Grade", grade),
        ("Name of the Customer", customer_name),
        ("Batch No", coa.batch_number),
        ("Supplied Quantity", supplied_qty),
        ("Date of Despatch", date_despatch),
        ("Date of Manufacture", _fmt_date(coa.date_of_manufacture)),
        ("Date of Retest", _fmt_date(coa.date_of_retest)),
        ("Date and time of sampling", _fmt_datetime(coa.date_time_of_sampling)),
        ("Date and time of analysis", _fmt_datetime(coa.date_time_of_analysis)),
    ]

    info_data = [
        [Paragraph(f"<b>{label} :</b>", header_label_style), Paragraph(value, body_style)]
        for label, value in info_rows
    ]
    info_table = Table(info_data, colWidths=[CONTENT_W * 0.42, CONTENT_W * 0.58])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    # -------------------------------------------------------------------------
    # 4. Test parameters table
    # Columns: S.No | Characteristic | Unit | Spec Min | Spec Max | Specification | Results | Test Method
    # -------------------------------------------------------------------------
    col_widths = [
        CONTENT_W * 0.05,   # S.No
        CONTENT_W * 0.22,   # Characteristic
        CONTENT_W * 0.08,   # Unit
        CONTENT_W * 0.10,   # Spec Min
        CONTENT_W * 0.10,   # Spec Max
        CONTENT_W * 0.15,   # Spec Description
        CONTENT_W * 0.15,   # Results
        CONTENT_W * 0.15,   # Test Method
    ]

    table_data = [[
        Paragraph("<b>S.No</b>", table_hdr_style),
        Paragraph("<b>Characteristic</b>", table_hdr_style),
        Paragraph("<b>Unit</b>", table_hdr_style),
        Paragraph("<b>Spec Min</b>", table_hdr_style),
        Paragraph("<b>Spec Max</b>", table_hdr_style),
        Paragraph("<b>Specification</b>", table_hdr_style),
        Paragraph("<b>Results</b>", table_hdr_style),
        Paragraph("<b>Test Method</b>", table_hdr_style),
    ]]

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
            spec_desc_str = p.spec_description
            result_str = p.result_text

        method_str = p.test_method.code if p.test_method else ""

        table_data.append([
            Paragraph(str(p.s_no), table_cell_style),
            Paragraph(_safe(p.parameter.name if p.parameter else ""), table_cell_style),
            Paragraph(unit_str, table_cell_style),
            Paragraph(spec_min_str, table_cell_style),
            Paragraph(spec_max_str, table_cell_style),
            Paragraph(spec_desc_str, table_cell_style),
            Paragraph(result_str, table_cell_style),
            Paragraph(method_str, table_cell_style),
        ])

    param_table = Table(table_data, colWidths=col_widths)

    table_style = [
        # Header row: dark navy background, white text
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_LABEL),
        ("FONTSIZE", (0, 0), (-1, 0), SIZE_TABLE_HDR),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]
    # Alternating row shading for readability
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))

    param_table.setStyle(TableStyle(table_style))
    story.append(param_table)
    story.append(Spacer(1, 8 * mm))

    # -------------------------------------------------------------------------
    # 5. Signature section — analyst and QC incharge
    # -------------------------------------------------------------------------
    from apps.workflow.constants import APPROVED
    from datetime import date as date_class
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
        Paragraph(analyst_col, sig_style),
        Paragraph("", sig_style),   # Center column: company seal placeholder
        Paragraph(qc_col, sig_style),
    ]]
    sig_table = Table(sig_data, colWidths=[CONTENT_W / 3, CONTENT_W / 3, CONTENT_W / 3])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 6 * mm))

    # -------------------------------------------------------------------------
    # 6. Footer — repeat footer_organisation details below a hairline rule
    # -------------------------------------------------------------------------
    footer_lines = [f"<b>{org_name}</b>"]
    if cin:
        footer_lines.append(f"CIN: {cin}")
    for addr_text in org_addresses:
        footer_lines.append(addr_text)

    footer_para = Paragraph("<br/>".join(footer_lines), footer_style)
    footer_table = Table([[footer_para]], colWidths=[CONTENT_W])
    footer_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.grey),
    ]))
    story.append(footer_table)

    doc.build(story)
    buf.seek(0)
    return buf
