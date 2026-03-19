"""
Packing List PDF generator — pdf1/ reference layout, mapped to actual model fields.

Field mapping summary (pdf1/ attribute → actual model field):
  packing_list.invoice_number      → packing_list.pl_number
  packing_list.origin_country      → packing_list.country_of_origin
  packing_list.final_destination_country → packing_list.country_of_final_destination
  packing_list.pre_carriage        → packing_list.pre_carriage_by   (PreCarriageBy.name)
  packing_list.port_loading        → packing_list.port_of_loading   (Port.name)
  packing_list.port_discharge      → packing_list.port_of_discharge (Port.name)
  packing_list.incoterm            → packing_list.incoterms         (Incoterm.code)
  packing_list.payment_term        → packing_list.payment_terms     (PaymentTerm.name)
  packing_list.other_ref           → packing_list.other_references
  packing_list.other_ref_date      → packing_list.other_references_date
  notify_party (text field)        → packing_list.notify_party      (Organisation.name)
  cont.container_reference         → cont.container_ref
  cont.marks_and_numbers           → cont.marks_numbers
  it.packages_number_and_kind      → it.packages_kind
  it.description_of_goods         → it.description
  it.uom (string)                  → it.uom.abbreviation            (UOM FK)

Constraint #20: generate_packing_list_pdf_bytes() returns bytes in-memory — never writes to disk.
"""
from decimal import Decimal
from io import BytesIO
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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


def _org_phone(org) -> str:
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        if not addr:
            return ""
        if addr.phone_country_code and addr.phone_number:
            return f"{addr.phone_country_code} {addr.phone_number}"
        return addr.phone_number or ""
    except Exception:
        return ""


def _org_registered_address(org):
    """Return the REGISTERED OrganisationAddress instance, or None."""
    if not org:
        return None
    try:
        return org.addresses.filter(address_type="REGISTERED").first()
    except Exception:
        return None


def _make_pl_styles():
    """
    Build and return the paragraph styles used by the PL section.
    Names are prefixed 'PL' to avoid collisions when embedded in a combined story.
    """
    base = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "PLCompanyHeader", parent=base["Normal"],
        fontSize=16, leading=20, spaceAfter=6,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "PLTitle", parent=base["Normal"],
        fontSize=12, leading=15, spaceAfter=10,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "PLLabel", parent=base["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "PLText", parent=base["Normal"],
        fontSize=9, leading=11,
    )
    style_small = ParagraphStyle(
        "PLSmall", parent=base["Normal"],
        fontSize=8, leading=10,
    )
    return style_company_header, style_title, style_label, style_text, style_small


# ---------------------------------------------------------------------------
# Story builder — can be called by generate_pl_ci_pdf to embed PL in a
# combined document without creating a separate PDF.
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
    style_company_header, style_title, style_label, style_text, style_small = styles
    story = []

    # ---- Header entities ------------------------------------------------
    exp = getattr(packing_list, "exporter", None)
    cons = getattr(packing_list, "consignee", None)

    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("Packing List, Weight Note", style_title))
    story.append(Spacer(1, 6))

    # ---- Exporter details -----------------------------------------------
    exp_address = _org_address_str(exp)
    exp_email = _org_email(exp)
    iec_code = safe(getattr(exp, "iec_code", ""))

    exp_lines = [safe(getattr(exp, "name", ""))]
    if exp_address:
        exp_lines.append(exp_address)
    if exp_email:
        exp_lines.append(exp_email)
    exporter_details_html = "<b>Corporate Office</b><br/>" + "<br/>".join(ln for ln in exp_lines if ln)

    # ---- Registered address (second column of exporter block) -----------
    reg = _org_registered_address(exp)
    reg_html_parts = []
    if reg:
        reg_parts = []
        if getattr(reg, "line1", ""):
            reg_parts.append(reg.line1)
        if getattr(reg, "line2", ""):
            reg_parts.append(reg.line2)
        city_state = ", ".join(filter(None, [getattr(reg, "city", ""), getattr(reg, "state", "")]))
        if city_state:
            reg_parts.append(city_state)
        if getattr(reg, "country", None):
            reg_parts.append(reg.country.name)
        if reg_parts:
            reg_html_parts.append(", ".join(reg_parts))
        contact_bits = []
        if getattr(reg, "phone_country_code", "") and getattr(reg, "phone_number", ""):
            contact_bits.append(f"Phone: {reg.phone_country_code} {reg.phone_number}")
        elif getattr(reg, "phone_number", ""):
            contact_bits.append(f"Phone: {reg.phone_number}")
        if getattr(reg, "email", ""):
            contact_bits.append(f"Email: {reg.email}")
        if contact_bits:
            reg_html_parts.append(" • ".join(contact_bits))
    reg_html = "<b>Registered Office</b><br/>" + "<br/>".join(reg_html_parts)

    # ---- Order references -----------------------------------------------
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
        ref_lines.append(f"<b>PO No/Date:</b> {po_no}{(' / ' + po_date) if po_date else ''}")
    if lc_no:
        ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{(' / ' + lc_date) if lc_date else ''}")
    if bl_no:
        ref_lines.append(f"<b>B/L No/Date:</b> {bl_no}{(' / ' + bl_date) if bl_date else ''}")
    if so_no:
        ref_lines.append(f"<b>SO No/Date:</b> {so_no}{(' / ' + so_date) if so_date else ''}")
    if other_ref:
        ref_lines.append(f"<b>Other Ref/Date:</b> {other_ref}{(' / ' + other_ref_date) if other_ref_date else ''}")

    pl_number = safe(getattr(packing_list, "pl_number", ""))

    # ---- Consignee details ----------------------------------------------
    cons_address = _org_address_str(cons)
    cons_email = _org_email(cons)
    cons_phone = _org_phone(cons)
    cons_lines = [safe(getattr(cons, "name", ""))]
    if cons_address:
        cons_lines.append(cons_address)
    contact_bits = []
    if cons_phone:
        contact_bits.append(f"Phone: {cons_phone}")
    if cons_email:
        contact_bits.append(f"Email: {cons_email}")
    if contact_bits:
        cons_lines.append(" • ".join(contact_bits))
    cons_html = "<b>Consignee</b><br/>" + "<br/>".join(ln for ln in cons_lines if ln)

    # ---- Buyer (only if different from consignee) -----------------------
    buyer = getattr(packing_list, "buyer", None)
    buyer_html = ""
    if buyer:
        buyer_name = safe(getattr(buyer, "name", ""))
        cons_name_val = safe(getattr(cons, "name", ""))
        if buyer_name.strip().lower() != cons_name_val.strip().lower():
            buyer_address = _org_address_str(buyer)
            buyer_email = _org_email(buyer)
            buyer_phone = _org_phone(buyer)
            buyer_lines = [buyer_name]
            if buyer_address:
                buyer_lines.append(buyer_address)
            buyer_contact = []
            if buyer_phone:
                buyer_contact.append(f"Phone: {buyer_phone}")
            if buyer_email:
                buyer_contact.append(f"Email: {buyer_email}")
            if buyer_contact:
                buyer_lines.append(" • ".join(buyer_contact))
            buyer_html = "<b>Buyer</b><br/>" + "<br/>".join(ln for ln in buyer_lines if ln)

    # ---- Notify Party ---------------------------------------------------
    notify_party_org = getattr(packing_list, "notify_party", None)
    notify_text = safe(getattr(notify_party_org, "name", "")) if notify_party_org else ""
    notify_html = f"<b>Notify Party</b><br/>{notify_text}" if notify_text else "<b>Notify Party</b>"

    # ---- Countries ------------------------------------------------------
    origin_country_obj = getattr(packing_list, "country_of_origin", None)
    dest_country_obj = getattr(packing_list, "country_of_final_destination", None)
    origin_name = safe(getattr(origin_country_obj, "name", "")) if origin_country_obj else ""
    dest_name = safe(getattr(dest_country_obj, "name", "")) if dest_country_obj else ""

    # ---- SUMMARY TOP (Exporter / Registered / IEC / Refs) ---------------
    summary_top_data = [
        [
            Paragraph("<b>Exporter:</b>", style_label),   # (0,0) spans col 0-1
            "",
            Paragraph(f"<b>IEC Code:</b><br/>{iec_code}", style_text),
            Paragraph(f"<b>Invoice No:</b><br/>{pl_number}", style_text),
        ],
        [
            Paragraph(exporter_details_html, style_text),
            Paragraph(reg_html, style_text),
            Paragraph("<br/>".join(ref_lines), style_text),
            "",  # merged with col 2
        ],
    ]
    summary_top = Table(summary_top_data, colWidths=[50 * mm, 50 * mm, 40 * mm, 40 * mm])
    summary_top.hAlign = "LEFT"
    summary_top.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("SPAN",         (0, 0), (1, 0)),   # "Exporter:" across col 0-1
        ("SPAN",         (2, 1), (3, 1)),   # References across col 2-3
    ]))
    story.append(summary_top)
    story.append(Spacer(1, 0))

    # ---- Consignee + Buyer block -----------------------------------------
    buyer_display_html = buyer_html if buyer_html else (
        "<b>Buyer</b><br/>" + "<br/>".join(ln for ln in cons_lines if ln)
    )
    buyer_cons_tbl = Table(
        [[Paragraph(cons_html, style_text), Paragraph(buyer_display_html, style_text)]],
        colWidths=[90 * mm, 90 * mm],
    )
    buyer_cons_tbl.hAlign = "LEFT"
    buyer_cons_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(buyer_cons_tbl)
    story.append(Spacer(1, 0))

    # ---- Notify Party + Countries ----------------------------------------
    summary_bottom_data = [[
        Paragraph(notify_html, style_text),  # spans col 0-1
        "",
        Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_name}", style_text),
        Paragraph(f"<b>Country of Final Destination</b><br/>{dest_name}", style_text),
    ]]
    summary_bottom = Table(summary_bottom_data, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm])
    summary_bottom.hAlign = "LEFT"
    summary_bottom.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("SPAN",         (0, 0), (1, 0)),   # Notify Party across col 0-1
    ]))
    story.append(summary_bottom)
    story.append(Spacer(1, 0))

    # ---- Shipping info table (2 rows × 6 cols; last 3 cols merged) ------
    pre_carriage_obj = getattr(packing_list, "pre_carriage_by", None)
    pre_carriage_val = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""

    place_receipt_obj = getattr(packing_list, "place_of_receipt_by_pre_carrier", None)
    place_receipt_val = safe(getattr(place_receipt_obj, "name", "")) if place_receipt_obj else ""

    vessel_flight_val = safe(getattr(packing_list, "vessel_flight_no", ""))

    port_loading_obj = getattr(packing_list, "port_of_loading", None)
    port_loading_val = safe(getattr(port_loading_obj, "name", "")) if port_loading_obj else ""

    port_discharge_obj = getattr(packing_list, "port_of_discharge", None)
    port_discharge_val = safe(getattr(port_discharge_obj, "name", "")) if port_discharge_obj else ""

    final_dest_obj = getattr(packing_list, "final_destination", None)
    final_destination_val = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""

    incoterm_obj = getattr(packing_list, "incoterms", None)
    incoterm_str = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""
    payment_term_obj = getattr(packing_list, "payment_terms", None)
    payment_term_str = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""
    terms_merged_html = (
        "<b>Incoterms:</b> " + incoterm_str
        + ("<br/>" if incoterm_str or payment_term_str else "")
        + "<b>Payment Terms:</b> " + payment_term_str
    )

    third_data = [
        [
            Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_val}", style_text),
            Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}", style_text),
            Paragraph(f"<b>Vessel/Flight No.</b><br/>{vessel_flight_val}", style_text),
            Paragraph(terms_merged_html, style_text),   # spans (3,0)→(5,1)
            "",
            "",
        ],
        [
            Paragraph(f"<b>Port of Loading</b><br/>{port_loading_val}", style_text),
            Paragraph(f"<b>Port of Discharge</b><br/>{port_discharge_val}", style_text),
            Paragraph(f"<b>Final Destination</b><br/>{final_destination_val}", style_text),
            "", "", "",
        ],
    ]
    third_tbl = Table(third_data, colWidths=[30 * mm] * 6)
    third_tbl.hAlign = "LEFT"
    third_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("SPAN",         (3, 0), (5, 1)),   # Incoterms+Payment merged across last 3 cols × 2 rows
    ]))
    story.append(third_tbl)
    story.append(Spacer(1, 6))

    # ---- Containers & Items -------------------------------------------------
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
            colWidths=[90 * mm, 90 * mm],
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

        tare_val = getattr(cont, "tare_weight", None)
        gross_val = getattr(cont, "gross_weight", None)

        # Compute net weight for this container from its items
        net_val = None
        try:
            computed_net = sum(
                (item.net_weight * item.quantity)
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
            colWidths=[30 * mm] * 6,
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
            Paragraph("<b>HSN/Item</b>", style_label),
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
            hsn_part = safe(getattr(it, "hsn_code", ""))
            item_code_part = safe(getattr(it, "item_code", ""))
            hsn_item = " ".join(
                x for x in [hsn_part, f"({item_code_part})" if item_code_part else ""] if x
            ).strip()
            qty_display = _fmt_decimal(getattr(it, "quantity", None))
            uom_obj = getattr(it, "uom", None)
            uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
            packages_kind = safe(getattr(it, "packages_kind", ""))
            description = safe(getattr(it, "description", ""))
            batch_details = safe(getattr(it, "batch_details", ""))

            item_rows.append([
                Paragraph(str(sr), style_text),
                Paragraph(hsn_item or "-", style_text),
                Paragraph(packages_kind or "-", style_text),
                Paragraph(description or "-", style_text),
                Paragraph(qty_display or "-", style_text),
                Paragraph(uom_display or "-", style_text),
                Paragraph(batch_details or "-", style_text),
            ])

        items_table = Table(
            item_rows,
            colWidths=[12 * mm, 20 * mm, 32 * mm, 60 * mm, 18 * mm, 12 * mm, 26 * mm],
            repeatRows=1,
        )
        items_table.hAlign = "LEFT"
        items_table.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("ALIGN",        (0, 0), (0, -1),  "CENTER"),
            ("ALIGN",        (4, 1), (4, -1),  "RIGHT"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.lightgrey),
        ]))

        story.append(KeepTogether([cont_header, weights_table, items_table]))
        story.append(Spacer(1, 6))

    # ---- Grand totals row ---------------------------------------------------
    totals_tbl = Table(
        [[
            Paragraph("<b>Total Net Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_net, 3), style_text),
            Paragraph("<b>Total Tare Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_tare, 3), style_text),
            Paragraph("<b>Total Gross Weight</b>", style_label),
            Paragraph(_fmt_decimal(total_gross, 3), style_text),
        ]],
        colWidths=[34 * mm, 26 * mm, 34 * mm, 26 * mm, 34 * mm, 26 * mm],
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
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    def add_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            "This is a computer-generated document. Signature is not required.",
        )
        canvas.restoreState()

    styles = _make_pl_styles()
    story = build_pl_story(packing_list, styles)
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
