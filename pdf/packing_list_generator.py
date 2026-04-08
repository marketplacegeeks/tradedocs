"""
Packing List PDF generator — restructured layout.

Table 1  References           PL No | CI No | PI No  (3 cols)
Table 2  Exporter             conditional on FACTORY address
           with FACTORY  →  row0: merged "Exporter" label
                             row1: Office | Registered | Factory | Other Refs  (4 cols)
           without FACTORY →  row0: merged "Exporter" label
                             row1: Office | Registered | Other Refs            (3 cols)
Table 3  Parties              conditional on notify_party
           with notify   →  Buyer | Consignee | Notify Party  (3 cols)
           without notify →  Buyer | Consignee               (2 cols)
Table 4  Shipping             single 4-col × 2-row table so column borders align
           row1: Pre-carriage by | Place of Receipt | Port of Loading | Port of Discharge
           row2: Final Destination | Country of Final Destination | Country of Origin | Vessel/Flight No.
Table 5  Terms                Payment Terms | Incoterms  (2 cols, 1 row)
[unchanged] Container section (container header → weights → items → grand totals)

Assumptions:
  - Exporter name rendered as bold heading above all tables (unchanged from before).
  - If an address type (OFFICE / REGISTERED / FACTORY) does not exist for the exporter,
    that cell is left blank — no fallback to first address.
  - CI number is pulled via packing_list.commercial_invoice.first(); blank if none exists yet.
  - Table 4 uses a single Table so all 4 column dividers align across both rows.
  - Buyer cell: shows buyer org if set; otherwise mirrors consignee (so cell is never empty).

Constraint #20: generate_packing_list_pdf_bytes() returns bytes in-memory — never writes to disk.
"""
from decimal import Decimal
from io import BytesIO
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def safe(v: Any, default: str = "") -> str:
    """Return empty string for None, otherwise str(v)."""
    return default if v is None else str(v)


def _fmt_decimal(v: Optional[Decimal], places: int = 3) -> str:
    """Format a Decimal to a fixed number of decimal places."""
    if v is None:
        return ""
    try:
        return f"{Decimal(v):.{places}f}"
    except Exception:
        try:
            return f"{float(v):.{places}f}"
        except Exception:
            return str(v)


def _org_address_by_type(org, address_type: str):
    """Return the OrganisationAddress of the given type, or None."""
    if not org:
        return None
    try:
        return org.addresses.filter(address_type=address_type).first()
    except Exception:
        return None


def _format_address_html(org, addr) -> str:
    """
    Build a multi-line HTML string for an organisation + address following the
    standard packing-list address block format:
      Line 1 — Organisation name
      Line 2 — Address line 1
      Line 3 — Address line 2
      Line 4 — City, Pin, State, Country (comma-separated)
      Line 5 — Phone number
      Line 6 — Email address
      Line 7 — IEC code  (e.g. IEC: ABCD1234567)
      Line 8 — Tax code  (e.g. GSTIN: 27ABCDE1234F1Z5)
    Any field that is absent is simply omitted.
    """
    parts = []

    if org:
        name = safe(getattr(org, "name", ""))
        if name:
            parts.append(name)

    if addr:
        if getattr(addr, "line1", ""):
            parts.append(addr.line1)

        if getattr(addr, "line2", ""):
            parts.append(addr.line2)

        city_parts = []
        for field in ("city", "pin", "state"):
            val = getattr(addr, field, "")
            if val:
                city_parts.append(val)
        country = getattr(addr, "country", None)
        if country:
            city_parts.append(safe(getattr(country, "name", "")))
        if city_parts:
            parts.append(", ".join(city_parts))

        phone_cc = getattr(addr, "phone_country_code", "")
        phone_no = getattr(addr, "phone_number", "")
        if phone_cc and phone_no:
            parts.append(f"Ph: {phone_cc} {phone_no}")
        elif phone_no:
            parts.append(f"Ph: {phone_no}")

        email = getattr(addr, "email", "")
        if email:
            parts.append(email)

    if addr:
        iec = getattr(addr, "iec_code", "")
        if iec:
            parts.append(f"IEC: {iec}")

        tax_type = getattr(addr, "tax_type", "")
        tax_code_val = getattr(addr, "tax_code", "")
        if tax_type and tax_code_val:
            parts.append(f"{tax_type}: {tax_code_val}")

    return "<br/>".join(parts)


def _party_html(label: str, org) -> str:
    """
    Build a labelled party cell (e.g. Buyer, Consignee, Notify Party).
    Uses the first available address for contact details.
    """
    if not org:
        return f"<b>{label}</b>"
    addr = None
    try:
        addr = org.addresses.first()
    except Exception:
        pass
    body = _format_address_html(org, addr)
    return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"


def _make_pl_styles():
    """
    Build and return the paragraph styles used in the PL PDF.
    Names are prefixed 'PL' to avoid collisions when embedded in a combined doc.
    """
    base = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "PLCompanyHeader", parent=base["Normal"],
        fontSize=18, leading=22, spaceAfter=4,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "PLTitle", parent=base["Normal"],
        fontSize=13, leading=16, spaceAfter=14,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "PLLabel", parent=base["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
    )
    style_label_center = ParagraphStyle(
        "PLLabelCenter", parent=base["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    style_text = ParagraphStyle(
        "PLText", parent=base["Normal"],
        fontSize=9, leading=12,
    )
    style_small = ParagraphStyle(
        "PLSmall", parent=base["Normal"],
        fontSize=8, leading=11,
    )
    return style_company_header, style_title, style_label, style_label_center, style_text, style_small


_GRID_STYLE = [
    ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]


def build_pl_story(packing_list, styles):
    """
    Build and return the list of story flowables for the Packing List section.

    Args:
        packing_list: PackingList model instance.
        styles: tuple returned by _make_pl_styles().

    Returns:
        list of ReportLab flowables (does NOT include a trailing PageBreak).
    """
    (style_company_header, style_title,
     style_label, style_label_center,
     style_text, style_small) = styles

    story = []

    PAGE_W = 180 * mm

    exp = getattr(packing_list, "exporter", None)
    exporter_name = safe(getattr(exp, "name", ""))

    story.append(Paragraph(exporter_name, style_company_header))
    story.append(Paragraph("Packing List / Weight Note", style_title))

    line_table = Table([[""]], colWidths=[180 * mm])
    line_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 10))

    pi_obj = getattr(packing_list, "proforma_invoice", None)
    pi_number = safe(getattr(pi_obj, "pi_number", "")) if pi_obj else ""

    pl_number = safe(getattr(packing_list, "pl_number", ""))

    ci_number = ""
    try:
        ci_obj = packing_list.commercial_invoice
        if ci_obj:
            ci_number = safe(getattr(ci_obj, "ci_number", ""))
    except Exception:
        pass

    col_2 = PAGE_W / 2
    col_3 = PAGE_W / 3

    office_addr = _org_address_by_type(exp, "OFFICE") or _org_address_by_type(exp, "REGISTERED")
    reg_addr = _org_address_by_type(exp, "REGISTERED")
    factory_addr = _org_address_by_type(exp, "FACTORY")

    def _exp_cell(label: str, addr) -> str:
        body = _format_address_html(exp, addr)
        return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"

    office_cell_html = _exp_cell("Corporate Office", office_addr)
    reg_cell_html = _exp_cell("Registered Address", reg_addr)
    factory_cell_html = _exp_cell("Factory Address", factory_addr)

    ref_lines = []
    po_no = safe(getattr(packing_list, "po_number", ""))
    po_date = safe(getattr(packing_list, "po_date", "")) if getattr(packing_list, "po_date", None) else ""
    lc_no = safe(getattr(packing_list, "lc_number", ""))
    lc_date = safe(getattr(packing_list, "lc_date", "")) if getattr(packing_list, "lc_date", None) else ""
    bl_no = safe(getattr(packing_list, "bl_number", ""))
    bl_date = safe(getattr(packing_list, "bl_date", "")) if getattr(packing_list, "bl_date", None) else ""
    so_no = safe(getattr(packing_list, "so_number", ""))
    so_date = safe(getattr(packing_list, "so_date", "")) if getattr(packing_list, "so_date", None) else ""
    other_ref = safe(getattr(packing_list, "other_references", ""))
    other_ref_date = safe(getattr(packing_list, "other_references_date", "")) if getattr(packing_list, "other_references_date", None) else ""

    if po_no:
        ref_lines.append(f"<b>PO No/Date:</b> {po_no}{' / ' + po_date if po_date else ''}")
    if lc_no:
        ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{' / ' + lc_date if lc_date else ''}")
    if bl_no:
        ref_lines.append(f"<b>BL No/Date:</b> {bl_no}{' / ' + bl_date if bl_date else ''}")
    if so_no:
        ref_lines.append(f"<b>SO No/Date:</b> {so_no}{' / ' + so_date if so_date else ''}")
    if other_ref:
        ref_lines.append(f"<b>Other Ref/Date:</b> {other_ref}{' / ' + other_ref_date if other_ref_date else ''}")

    refs_cell_html = (
        "<b>Other References</b><br/>" + "<br/>".join(ref_lines)
        if ref_lines
        else "<b>Other References</b>"
    )

    col_4 = PAGE_W / 4

    header_data = [[
        Paragraph("<b>Exporter</b>", style_label),
        "",
        Paragraph(f"<b>Packing List No.</b><br/>{pl_number}", style_text),
        Paragraph(f"<b>Commercial Invoice No.</b><br/>{ci_number or '—'}", style_text),
    ]]
    header_tbl = Table(header_data, colWidths=[col_4, col_4, col_4, col_4])
    header_tbl.setStyle(TableStyle(_GRID_STYLE + [
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
    ]))
    header_tbl.hAlign = "LEFT"
    story.append(header_tbl)

    if factory_addr:
        exp_data = [[
            Paragraph(office_cell_html, style_text),
            Paragraph(reg_cell_html, style_text),
            Paragraph(factory_cell_html, style_text),
        ]]
        exp_tbl = Table(exp_data, colWidths=[col_3, col_3, col_3])
    else:
        exp_data = [[
            Paragraph(office_cell_html, style_text),
            Paragraph(reg_cell_html, style_text),
        ]]
        exp_tbl = Table(exp_data, colWidths=[col_2, col_2])

    exp_tbl.setStyle(TableStyle(_GRID_STYLE))
    exp_tbl.hAlign = "LEFT"
    story.append(exp_tbl)

    cons = getattr(packing_list, "consignee", None)
    buyer = getattr(packing_list, "buyer", None)
    notify_party = getattr(packing_list, "notify_party", None)

    buyer_org = buyer if buyer else cons
    buyer_cell_html = _party_html("Buyer", buyer_org)
    cons_cell_html = _party_html("Consignee", cons)

    if notify_party:
        notify_cell_html = _party_html("Notify Party", notify_party)
        party_data = [[
            Paragraph(buyer_cell_html, style_text),
            Paragraph(cons_cell_html, style_text),
            Paragraph(notify_cell_html, style_text),
        ]]
        party_tbl = Table(party_data, colWidths=[col_3, col_3, col_3])
    else:
        party_data = [[
            Paragraph(buyer_cell_html, style_text),
            Paragraph(cons_cell_html, style_text),
        ]]
        party_tbl = Table(party_data, colWidths=[col_2, col_2])

    party_tbl.hAlign = "LEFT"
    party_tbl.setStyle(TableStyle(_GRID_STYLE))
    story.append(party_tbl)

    pre_carriage_obj = getattr(packing_list, "pre_carriage_by", None)
    pre_carriage_val = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""

    place_receipt_obj = getattr(packing_list, "place_of_receipt_by_pre_carrier", None)
    place_receipt_val = safe(getattr(place_receipt_obj, "name", "")) if place_receipt_obj else ""

    port_loading_obj = getattr(packing_list, "port_of_loading", None)
    port_loading_val = safe(getattr(port_loading_obj, "name", "")) if port_loading_obj else ""

    port_discharge_obj = getattr(packing_list, "port_of_discharge", None)
    port_discharge_val = safe(getattr(port_discharge_obj, "name", "")) if port_discharge_obj else ""

    final_dest_obj = getattr(packing_list, "final_destination", None)
    final_dest_val = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""

    dest_country_obj = getattr(packing_list, "country_of_final_destination", None)
    dest_country_val = safe(getattr(dest_country_obj, "name", "")) if dest_country_obj else ""

    origin_country_obj = getattr(packing_list, "country_of_origin", None)
    origin_country_val = safe(getattr(origin_country_obj, "name", "")) if origin_country_obj else ""

    vessel_val = safe(getattr(packing_list, "vessel_flight_no", ""))

    col_4 = PAGE_W / 4
    shipping_data = [
        [
            Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_val}", style_text),
            Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}", style_text),
            Paragraph(f"<b>Port of Loading</b><br/>{port_loading_val}", style_text),
            Paragraph(f"<b>Port of Discharge</b><br/>{port_discharge_val}", style_text),
        ],
        [
            Paragraph(f"<b>Final Destination</b><br/>{final_dest_val}", style_text),
            Paragraph(f"<b>Country of Final Destination</b><br/>{dest_country_val}", style_text),
            Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_country_val}", style_text),
            Paragraph(f"<b>Vessel / Flight No.</b><br/>{vessel_val}", style_text),
        ],
    ]
    shipping_tbl = Table(shipping_data, colWidths=[col_4, col_4, col_4, col_4])
    shipping_tbl.hAlign = "LEFT"
    shipping_tbl.setStyle(TableStyle(_GRID_STYLE))
    story.append(shipping_tbl)

    payment_term_obj = getattr(packing_list, "payment_terms", None)
    payment_term_val = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""

    incoterm_obj = getattr(packing_list, "incoterms", None)
    incoterm_val = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""

    terms_data = [[
        Paragraph(f"<b>Payment Terms</b><br/>{payment_term_val}", style_text),
        Paragraph(f"<b>Incoterms</b><br/>{incoterm_val}", style_text),
        Paragraph(refs_cell_html, style_text),
    ]]
    terms_tbl = Table(terms_data, colWidths=[col_3, col_3, col_3])
    terms_tbl.hAlign = "LEFT"
    terms_tbl.setStyle(TableStyle(_GRID_STYLE))
    story.append(terms_tbl)

    story.append(Spacer(1, 12))

    total_net = Decimal("0.000")
    total_tare = Decimal("0.000")
    total_gross = Decimal("0.000")

    for cont in packing_list.containers.all().order_by("id"):
        cont_ref = safe(getattr(cont, "container_ref", ""))
        marks = safe(getattr(cont, "marks_numbers", ""))

        cont_header = Table(
            [[
                Paragraph(f"<b>Container:</b> {cont_ref}", style_text),
                Paragraph(f"<b>Marks &amp; Numbers:</b> {marks}", style_text),
            ]],
            colWidths=[col_2, col_2],
        )
        cont_header.hAlign = "LEFT"
        cont_header.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        tare_val = getattr(cont, "tare_weight", None)
        gross_val = getattr(cont, "gross_weight", None)

        net_val = None
        try:
            computed_net = sum(
                item.net_material_weight
                for item in cont.items.all()
                if item.net_material_weight is not None
            )
            net_val = computed_net
        except Exception:
            pass

        try:
            if net_val is not None:
                total_net += Decimal(str(net_val))
            if tare_val is not None:
                total_tare += Decimal(str(tare_val))
            if gross_val is not None:
                total_gross += Decimal(str(gross_val))
        except Exception:
            pass

        weights_table = Table(
            [[
                Paragraph("<b>Net Material Wt</b>", style_label),
                Paragraph(f"{_fmt_decimal(net_val, 3)} KGS" if net_val is not None else "-", style_text),
                Paragraph("<b>Tare Weight</b>", style_label),
                Paragraph(f"{_fmt_decimal(tare_val, 3)} KGS" if tare_val is not None else "-", style_text),
                Paragraph("<b>Gross Weight</b>", style_label),
                Paragraph(f"{_fmt_decimal(gross_val, 3)} KGS" if gross_val is not None else "-", style_text),
            ]],
            colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm],
        )
        weights_table.hAlign = "LEFT"
        weights_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("ALIGN", (3, 0), (3, 0), "RIGHT"),
            ("ALIGN", (5, 0), (5, 0), "RIGHT"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
        ]))

        item_header = [
            Paragraph("<b>Sr.</b>", style_label_center),
            Paragraph("<b>HSN Code</b>", style_label_center),
            Paragraph("<b>Item Code</b>", style_label_center),
            Paragraph("<b>Description</b>", style_label_center),
            Paragraph("<b>Batch No.</b>", style_label_center),
            Paragraph("<b>Quantity of Items</b>", style_label_center),
            Paragraph("<b>Type of Package</b>", style_label_center),
            Paragraph("<b>Material Unit</b>", style_label_center),
            Paragraph("<b>Net Weight Per Item</b>", style_label_center),
            Paragraph("<b>Weight per empty package</b>", style_label_center),
            Paragraph("<b>Net Material Wt</b>", style_label_center),
            Paragraph("<b>Gross Weight</b>", style_label_center),
        ]
        item_rows = [item_header]
        sr = 0
        for it in cont.items.all().order_by("id"):
            sr += 1
            uom_obj = getattr(it, "uom", None)
            uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
            pkg_obj = getattr(it, "type_of_package", None)
            pkg_display = safe(getattr(pkg_obj, "name", "")) if pkg_obj else ""

            item_rows.append([
                Paragraph(str(sr), style_text),
                Paragraph(safe(getattr(it, "hsn_code", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "item_code", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "description", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "batch_details", "")) or "-", style_text),
                Paragraph(_fmt_decimal(getattr(it, "no_of_packages", None)) or "-", style_text),
                Paragraph(pkg_display or "-", style_text),
                Paragraph(uom_display or "-", style_text),
                Paragraph(_fmt_decimal(getattr(it, "qty_per_package", None)) or "-", style_text),
                Paragraph(_fmt_decimal(getattr(it, "weight_per_unit_packaging", None)) or "-", style_text),
                Paragraph(_fmt_decimal(getattr(it, "net_material_weight", None)) or "-", style_text),
                Paragraph(_fmt_decimal(getattr(it, "item_gross_weight", None)) or "-", style_text),
            ])

        # 12 columns: Sr | HSN | Item Code | Desc | Batch | No.Pkg | Type | Unit | Qty/Pkg | Wt/Unit | Net Mat | Gross
        items_table = Table(
            item_rows,
            colWidths=[8*mm, 16*mm, 16*mm, 30*mm, 18*mm, 14*mm, 18*mm, 13*mm, 14*mm, 14*mm, 14*mm, 15*mm],
            repeatRows=1,
        )
        items_table.hAlign = "LEFT"
        items_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (0, 0), 6),
            ("BOTTOMPADDING", (0, 0), (0, 0), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ]))

        story.append(KeepTogether([cont_header, weights_table, items_table]))
        story.append(Spacer(1, 10))

    totals_tbl = Table(
        [[
            Paragraph("<b>Total Net Material Wt</b>", style_label),
            Paragraph(f"{_fmt_decimal(total_net, 3)} KGS", style_text),
            Paragraph("<b>Total Tare Weight</b>", style_label),
            Paragraph(f"{_fmt_decimal(total_tare, 3)} KGS", style_text),
            Paragraph("<b>Total Gross Weight</b>", style_label),
            Paragraph(f"{_fmt_decimal(total_gross, 3)} KGS", style_text),
        ]],
        colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm],
    )
    totals_tbl.hAlign = "LEFT"
    totals_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("ALIGN", (3, 0), (3, 0), "RIGHT"),
        ("ALIGN", (5, 0), (5, 0), "RIGHT"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Quantities and UOM as per container item details.", style_small))

    return story


def generate_packing_list_pdf_bytes(packing_list) -> bytes:
    """
    Generate a standalone Packing List PDF.
    Constraint #20: built entirely in-memory; never written to disk.
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

    def add_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 12 * mm,
            "This is a computer generated document and does not require signature",
        )
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(
            A4[0] / 2, 8 * mm,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    styles = _make_pl_styles()
    story = build_pl_story(packing_list, styles)
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
