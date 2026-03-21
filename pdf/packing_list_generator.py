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


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Address helpers
# ---------------------------------------------------------------------------

def _org_address_by_type(org, address_type: str):
    """Return the OrganisationAddress of the given type, or None."""
    if not org:
        return None
    try:
        return org.addresses.filter(address_type=address_type).first()
    except Exception:
        return None


def _address_lines_html(addr) -> str:
    """
    Build a multi-line HTML string from an OrganisationAddress instance.
    Returns empty string if addr is None.
    """
    if not addr:
        return ""
    parts = []
    if getattr(addr, "line1", ""):
        parts.append(addr.line1)
    if getattr(addr, "line2", ""):
        parts.append(addr.line2)
    city_state = ", ".join(filter(None, [
        getattr(addr, "city", ""),
        getattr(addr, "state", ""),
    ]))
    if city_state:
        parts.append(city_state)
    if getattr(addr, "pin", ""):
        parts.append(addr.pin)
    if getattr(addr, "country", None):
        parts.append(addr.country.name)
    # Contact details on a single line
    contact_bits = []
    if getattr(addr, "phone_country_code", "") and getattr(addr, "phone_number", ""):
        contact_bits.append(f"Ph: {addr.phone_country_code} {addr.phone_number}")
    elif getattr(addr, "phone_number", ""):
        contact_bits.append(f"Ph: {addr.phone_number}")
    if getattr(addr, "email", ""):
        contact_bits.append(f"Email: {addr.email}")
    if contact_bits:
        parts.append(" • ".join(contact_bits))
    return "<br/>".join(parts)


def _party_html(label: str, org) -> str:
    """
    Build a labelled party cell (e.g. Buyer, Consignee, Notify Party).
    Uses the first available address for phone/email.
    """
    if not org:
        return f"<b>{label}</b>"
    name = safe(getattr(org, "name", ""))
    # Use first address for contact details
    addr = None
    try:
        addr = org.addresses.first()
    except Exception:
        pass
    addr_html = _address_lines_html(addr)
    lines = [f"<b>{label}</b>", name]
    if addr_html:
        lines.append(addr_html)
    return "<br/>".join(ln for ln in lines if ln)


# ---------------------------------------------------------------------------
# Paragraph style factory
# ---------------------------------------------------------------------------

def _make_pl_styles():
    """
    Build and return the paragraph styles used in the PL PDF.
    Names are prefixed 'PL' to avoid collisions when embedded in a combined doc.
    """
    base = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "PLCompanyHeader", parent=base["Normal"],
        fontSize=14, leading=18, spaceAfter=4,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "PLTitle", parent=base["Normal"],
        fontSize=11, leading=14, spaceAfter=8,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "PLLabel", parent=base["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
    )
    style_label_center = ParagraphStyle(
        "PLLabelCenter", parent=base["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    style_text = ParagraphStyle(
        "PLText", parent=base["Normal"],
        fontSize=8, leading=10,
    )
    style_small = ParagraphStyle(
        "PLSmall", parent=base["Normal"],
        fontSize=7, leading=9,
    )
    return style_company_header, style_title, style_label, style_label_center, style_text, style_small


# ---------------------------------------------------------------------------
# Common table style (grid + padding)
# ---------------------------------------------------------------------------

_GRID_STYLE = [
    ("GRID",          (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 5),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ("TOPPADDING",    (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------

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

    # Usable page width with 10mm margins on each side: 190mm
    PAGE_W = 190 * mm

    # ------------------------------------------------------------------
    # Header: Exporter name + document title
    # ------------------------------------------------------------------
    exp = getattr(packing_list, "exporter", None)
    exporter_name = safe(getattr(exp, "name", ""))

    story.append(Paragraph(exporter_name, style_company_header))
    story.append(Paragraph("Packing List / Weight Note", style_title))

    # ------------------------------------------------------------------
    # Table 1 — References  (3 equal cols)
    # ------------------------------------------------------------------

    # Pull PI number from the linked Proforma Invoice
    pi_obj = getattr(packing_list, "proforma_invoice", None)
    pi_number = safe(getattr(pi_obj, "pi_number", "")) if pi_obj else ""

    pl_number = safe(getattr(packing_list, "pl_number", ""))

    # Pull CI number — commercial_invoice is a reverse OneToOneField, so access
    # the object directly (not via .first()).
    ci_number = ""
    try:
        ci_obj = packing_list.commercial_invoice
        if ci_obj:
            ci_number = safe(getattr(ci_obj, "ci_number", ""))
    except Exception:
        pass

    col_3 = PAGE_W / 3

    # ------------------------------------------------------------------
    # Table 2 — Exporter  (conditional: 4 cols with FACTORY, 3 cols without)
    # ------------------------------------------------------------------

    # Fetch address types. Corporate Office falls back to Registered if no OFFICE address exists.
    office_addr = _org_address_by_type(exp, "OFFICE") or _org_address_by_type(exp, "REGISTERED")
    reg_addr    = _org_address_by_type(exp, "REGISTERED")
    factory_addr = _org_address_by_type(exp, "FACTORY")

    iec_code = safe(getattr(exp, "iec_code", "")) if exp else ""

    # Build Office address cell content
    office_html = _address_lines_html(office_addr)
    office_cell_html = (
        f"<b>Corporate Office</b><br/>{office_html}{'<br/>IEC: ' + iec_code if iec_code else ''}"
        if office_addr
        else (f"<b>Corporate Office</b><br/>IEC: {iec_code}" if iec_code else "<b>Corporate Office</b>")
    )

    # Build Registered address cell content
    reg_html = _address_lines_html(reg_addr)
    reg_cell_html = (
        f"<b>Registered Address</b><br/>{reg_html}"
        if reg_html
        else "<b>Registered Address</b>"
    )

    # Build Factory address cell content (only used in 4-col variant)
    factory_html = _address_lines_html(factory_addr)
    factory_cell_html = (
        f"<b>Factory Address</b><br/>{factory_html}"
        if factory_html
        else "<b>Factory Address</b>"
    )

    # Build Other References cell content (PO / LC / BL / SO / Other)
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

    # Row 0: "Exporter" label (col 0) | PL Number (col 1) | CI Number (col 2)
    # The 4-col variant adds a blank col 3 to match the address row below.
    row0_exporter = Paragraph("<b>Exporter</b>", style_label)
    row0_pl       = Paragraph(f"<b>Packing List No.</b><br/>{pl_number}", style_text)
    row0_ci       = Paragraph(f"<b>Commercial Invoice No.</b><br/>{ci_number or '—'}", style_text)

    if factory_addr:
        # 4-column variant
        col_4 = PAGE_W / 4
        exp_data = [
            [row0_exporter, row0_pl, row0_ci, ""],   # col 3 blank; CI spans cols 2-3
            [
                Paragraph(office_cell_html, style_text),
                Paragraph(reg_cell_html, style_text),
                Paragraph(factory_cell_html, style_text),
                Paragraph(refs_cell_html, style_text),
            ],
        ]
        exp_tbl = Table(exp_data, colWidths=[col_4, col_4, col_4, col_4])
        exp_tbl.setStyle(TableStyle(_GRID_STYLE + [
            ("SPAN",       (2, 0), (3, 0)),   # CI number spans cols 2-3 in row 0
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ]))
    else:
        # 3-column variant
        exp_data = [
            [row0_exporter, row0_pl, row0_ci],
            [
                Paragraph(office_cell_html, style_text),
                Paragraph(reg_cell_html, style_text),
                Paragraph(refs_cell_html, style_text),
            ],
        ]
        exp_tbl = Table(exp_data, colWidths=[col_3, col_3, col_3])
        exp_tbl.setStyle(TableStyle(_GRID_STYLE + [
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ]))

    exp_tbl.hAlign = "LEFT"
    story.append(exp_tbl)

    # ------------------------------------------------------------------
    # Table 3 — Parties  (conditional: 3 cols with notify, 2 cols without)
    # ------------------------------------------------------------------

    cons = getattr(packing_list, "consignee", None)
    buyer = getattr(packing_list, "buyer", None)
    notify_party = getattr(packing_list, "notify_party", None)

    # Buyer cell: show buyer if set; otherwise mirror consignee
    buyer_org = buyer if buyer else cons
    buyer_cell_html = _party_html("Buyer", buyer_org)
    cons_cell_html  = _party_html("Consignee", cons)

    if notify_party:
        # 3-column variant
        notify_cell_html = _party_html("Notify Party", notify_party)
        party_data = [[
            Paragraph(buyer_cell_html, style_text),
            Paragraph(cons_cell_html, style_text),
            Paragraph(notify_cell_html, style_text),
        ]]
        party_tbl = Table(party_data, colWidths=[col_3, col_3, col_3])
    else:
        # 2-column variant
        col_2 = PAGE_W / 2
        party_data = [[
            Paragraph(buyer_cell_html, style_text),
            Paragraph(cons_cell_html, style_text),
        ]]
        party_tbl = Table(party_data, colWidths=[col_2, col_2])

    party_tbl.hAlign = "LEFT"
    party_tbl.setStyle(TableStyle(_GRID_STYLE))
    story.append(party_tbl)

    # ------------------------------------------------------------------
    # Table 4 — Shipping  (4 cols × 2 rows, single table for aligned borders)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Table 5 — Terms  (2 cols × 1 row)
    # ------------------------------------------------------------------

    payment_term_obj = getattr(packing_list, "payment_terms", None)
    payment_term_val = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""

    incoterm_obj = getattr(packing_list, "incoterms", None)
    incoterm_val = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""

    col_2 = PAGE_W / 2
    terms_data = [[
        Paragraph(f"<b>Payment Terms</b><br/>{payment_term_val}", style_text),
        Paragraph(f"<b>Incoterms</b><br/>{incoterm_val}", style_text),
    ]]
    terms_tbl = Table(terms_data, colWidths=[col_2, col_2])
    terms_tbl.hAlign = "LEFT"
    terms_tbl.setStyle(TableStyle(_GRID_STYLE))
    story.append(terms_tbl)

    story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # Container section — UNCHANGED
    # ------------------------------------------------------------------

    total_net   = Decimal("0.000")
    total_tare  = Decimal("0.000")
    total_gross = Decimal("0.000")

    for cont in packing_list.containers.all().order_by("id"):
        cont_ref = safe(getattr(cont, "container_ref", ""))
        marks    = safe(getattr(cont, "marks_numbers", ""))

        cont_header = Table(
            [[
                Paragraph(f"<b>Container:</b> {cont_ref}", style_text),
                Paragraph(f"<b>Marks &amp; Numbers:</b> {marks}", style_text),
            ]],
            colWidths=[col_2, col_2],
        )
        cont_header.hAlign = "LEFT"
        cont_header.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND",   (0, 0), (-1, -1), colors.whitesmoke),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))

        tare_val  = getattr(cont, "tare_weight", None)
        gross_val = getattr(cont, "gross_weight", None)

        # Net weight computed from items (net_weight × quantity per item)
        net_val = None
        try:
            computed_net = sum(
                item.net_weight * item.quantity
                for item in cont.items.all()
                if item.net_weight is not None and item.quantity is not None
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
                Paragraph("<b>Net Weight</b>", style_label),
                Paragraph(_fmt_decimal(net_val, 3) or "-", style_text),
                Paragraph("<b>Tare Weight</b>", style_label),
                Paragraph(_fmt_decimal(tare_val, 3) or "-", style_text),
                Paragraph("<b>Gross Weight</b>", style_label),
                Paragraph(_fmt_decimal(gross_val, 3) or "-", style_text),
            ]],
            colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 40 * mm],
        )
        weights_table.hAlign = "LEFT"
        weights_table.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("ALIGN",        (1, 0), (1, 0), "RIGHT"),
            ("ALIGN",        (3, 0), (3, 0), "RIGHT"),
            ("ALIGN",        (5, 0), (5, 0), "RIGHT"),
            ("BACKGROUND",   (0, 0), (-1, -1), colors.whitesmoke),
        ]))

        # Items table
        item_header = [
            Paragraph("<b>Sr.</b>", style_label),
            Paragraph("<b>HSN Code</b>", style_label),
            Paragraph("<b>Item Code</b>", style_label),
            Paragraph("<b>No &amp; Kind of Packages</b>", style_label),
            Paragraph("<b>Description of Goods</b>", style_label),
            Paragraph("<b>Qty</b>", style_label),
            Paragraph("<b>UOM</b>", style_label),
            Paragraph("<b>Batch Details</b>", style_label),
        ]
        item_rows = [item_header]
        sr = 0
        for it in cont.items.all().order_by("id"):
            sr += 1
            uom_obj      = getattr(it, "uom", None)
            uom_display  = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
            qty_display  = _fmt_decimal(getattr(it, "quantity", None))

            item_rows.append([
                Paragraph(str(sr), style_text),
                Paragraph(safe(getattr(it, "hsn_code", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "item_code", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "packages_kind", "")) or "-", style_text),
                Paragraph(safe(getattr(it, "description", "")) or "-", style_text),
                Paragraph(qty_display or "-", style_text),
                Paragraph(uom_display or "-", style_text),
                Paragraph(safe(getattr(it, "batch_details", "")) or "-", style_text),
            ])

        # Col widths: Sr(10)+HSN(20)+ItemCode(20)+Packages(28)+Desc(52)+Qty(16)+UOM(10)+Batch(34)=190mm
        items_table = Table(
            item_rows,
            colWidths=[10*mm, 20*mm, 20*mm, 28*mm, 52*mm, 16*mm, 10*mm, 34*mm],
            repeatRows=1,
        )
        items_table.hAlign = "LEFT"
        items_table.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("ALIGN",        (0, 0), (0, -1),  "CENTER"),
            ("ALIGN",        (5, 1), (5, -1),  "RIGHT"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.lightgrey),
        ]))

        story.append(KeepTogether([cont_header, weights_table, items_table]))
        story.append(Spacer(1, 6))

    # Grand totals row
    totals_tbl = Table(
        [[
            Paragraph("<b>Total Net Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_net, 3), style_text),
            Paragraph("<b>Total Tare Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_tare, 3), style_text),
            Paragraph("<b>Total Gross Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_gross, 3), style_text),
        ]],
        colWidths=[34*mm, 26*mm, 34*mm, 26*mm, 34*mm, 36*mm],
    )
    totals_tbl.hAlign = "LEFT"
    totals_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("ALIGN",        (1, 0), (1, 0), "RIGHT"),
        ("ALIGN",        (3, 0), (3, 0), "RIGHT"),
        ("ALIGN",        (5, 0), (5, 0), "RIGHT"),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 4))
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
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    def add_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 8 * mm,
            "This is a computer-generated document. Signature is not required.",
        )
        canvas.restoreState()

    styles = _make_pl_styles()
    story = build_pl_story(packing_list, styles)
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
