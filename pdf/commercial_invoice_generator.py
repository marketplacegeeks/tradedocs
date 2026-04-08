"""
Commercial Invoice PDF generator — pdf1/ reference layout, mapped to actual model fields.

Field mapping summary (pdf1/ attribute → actual model field):
  invoice.exporter           → invoice.packing_list.exporter   (via PL)
  invoice.consignee          → invoice.packing_list.consignee  (via PL)
  invoice.invoice_number     → invoice.ci_number
  invoice.date               → invoice.ci_date
  invoice.incoterm.code      → invoice.packing_list.incoterms.code
  invoice.payment_term.name  → invoice.packing_list.payment_terms.name
  invoice.port_loading       → invoice.packing_list.port_of_loading
  invoice.port_discharge     → invoice.packing_list.port_of_discharge
  invoice.pre_carriage       → invoice.packing_list.pre_carriage_by
  it.hs_code                 → it.hsn_code
  it.quantity                → it.total_quantity
  it.unit_price_usd          → it.rate_usd
  it.unit (string)           → it.uom.abbreviation  (UOM FK)
  pitem.packages_number_and_kind → pitem.packages_kind
  invoice.total_amount_usd   → computed: sum(li.amount_usd for li in ci.line_items.all())
  containers (is_active)     → no is_active on Container; use .all().order_by("id")

Constraint #20: generate_commercial_invoice_pdf_bytes() returns bytes in-memory — never
writes to disk.
"""
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_INCOTERM_VISIBLE_FIELDS: dict = {
    "EXW": set(),
    "FCA": set(),
    "FOB": set(),
    "CFR": {"freight"},
    "CIF": {"freight", "insurance"},
    "CPT": {"freight"},
    "CIP": {"freight", "insurance"},
    "DAP": {"freight", "insurance"},
    "DPU": {"freight", "insurance"},
    "DDP": {"freight", "insurance"},
}
_ALL_CI_FIELDS = {"freight", "insurance"}


def safe(v: Any, default: str = "") -> str:
    return default if v is None else str(v)


def _fmt_money(v: Any) -> str:
    """Format number as money - show decimals only if non-zero (max 2 decimal places)."""
    try:
        num = float(v)
        # Check if it's a whole number
        if num == int(num):
            return f"{int(num):,}"
        # Has decimals - show up to 2 places, strip trailing zeros
        formatted = f"{num:,.2f}"
        # Remove trailing zeros after decimal point
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted
    except Exception:
        return safe(v)


def _fmt_qty(v: Any) -> str:
    """Format quantity - show decimals only if non-zero (max 3 decimal places)."""
    try:
        num = float(v)
        # Check if it's a whole number
        if num == int(num):
            return f"{int(num):,}"
        # Has decimals - show up to 3 places, strip trailing zeros
        formatted = f"{num:,.3f}"
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted
    except Exception:
        return safe(v)


def _amount_to_words(n: Any, currency: str = "USD") -> str:
    try:
        from num2words import num2words
        n = int(float(n or 0))
        words = num2words(n).title()
        return f"{words} {currency} Only"
    except Exception:
        return ""


def _org_address_str(org) -> str:
    if not org:
        return ""
    try:
        addr = (
            org.addresses.filter(address_type="OFFICE").first()
            or org.addresses.filter(address_type="REGISTERED").first()
        )
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
        addr = (
            org.addresses.filter(address_type="OFFICE").first()
            or org.addresses.filter(address_type="REGISTERED").first()
        )
        return addr.email if addr else ""
    except Exception:
        return ""


def _org_registered_address(org):
    if not org:
        return None
    try:
        return org.addresses.filter(address_type="REGISTERED").first()
    except Exception:
        return None


def _party_cell_html(label: str, org) -> str:
    if not org:
        return f"<b>{label}</b>" if label else ""
    parts = []
    name = safe(getattr(org, "name", ""))
    if name:
        parts.append(name)
    try:
        addr = org.addresses.first()
    except Exception:
        addr = None
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
    body = "<br/>".join(p for p in parts if p)
    if label:
        return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"
    return body


def _make_ci_styles():
    base = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "CICompanyHeader", parent=base["Normal"],
        fontSize=18, leading=22, spaceAfter=4,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "CITitle", parent=base["Normal"],
        fontSize=13, leading=16, spaceAfter=14,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "CILabel", parent=base["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "CIText", parent=base["Normal"],
        fontSize=9, leading=12,
    )
    style_small = ParagraphStyle(
        "CISmall", parent=base["Normal"],
        fontSize=8, leading=11,
    )
    style_table_header = ParagraphStyle(
        "CITableHeader", parent=base["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    return style_company_header, style_title, style_label, style_text, style_small, style_table_header


def build_ci_story(ci, styles) -> list:
    style_company_header, style_title, style_label, style_text, style_small, style_table_header = styles
    story = []

    pl = getattr(ci, "packing_list", None)
    exp = getattr(pl, "exporter", None) if pl else None
    cons = getattr(pl, "consignee", None) if pl else None
    buyer = getattr(pl, "buyer", None) if pl else None
    notify_party_org = getattr(pl, "notify_party", None) if pl else None

    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("COMMERCIAL INVOICE", style_title))

    line_table = Table([[""]], colWidths=[180 * mm])
    line_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 10))

    col_4 = 180 * mm / 4
    col_3 = 180 * mm / 3
    col_2 = 90 * mm

    _GRID = [
        ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    corp_addr = (
        (exp.addresses.filter(address_type="OFFICE").first()
         or exp.addresses.filter(address_type="REGISTERED").first())
        if exp else None
    )
    reg_addr = (exp.addresses.filter(address_type="REGISTERED").first() if exp else None)
    factory_addr = (exp.addresses.filter(address_type="FACTORY").first() if exp else None)

    def _exp_cell(label: str, addr) -> str:
        parts = []
        if exp:
            parts.append(safe(getattr(exp, "name", "")))
        if addr:
            if getattr(addr, "line1", ""):
                parts.append(addr.line1)
            if getattr(addr, "line2", ""):
                parts.append(addr.line2)
            city_parts = [v for v in (getattr(addr, "city", ""), getattr(addr, "pin", ""),
                                      getattr(addr, "state", "")) if v]
            if getattr(addr, "country", None):
                city_parts.append(addr.country.name)
            if city_parts:
                parts.append(", ".join(city_parts))
            phone_cc = getattr(addr, "phone_country_code", "")
            phone_no = getattr(addr, "phone_number", "")
            if phone_cc and phone_no:
                parts.append(f"Ph: {phone_cc} {phone_no}")
            elif phone_no:
                parts.append(f"Ph: {phone_no}")
            if getattr(addr, "email", ""):
                parts.append(addr.email)
            iec = getattr(addr, "iec_code", "")
            if iec:
                parts.append(f"IEC: {iec}")
            tax_type = getattr(addr, "tax_type", "")
            tax_code_v = getattr(addr, "tax_code", "")
            if tax_type and tax_code_v:
                parts.append(f"{tax_type}: {tax_code_v}")
        body = "<br/>".join(parts)
        return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"

    ref_lines = []
    if pl:
        po_no = safe(getattr(pl, "po_number", ""))
        po_date = safe(getattr(pl, "po_date", "")) if getattr(pl, "po_date", None) else ""
        lc_no = safe(getattr(pl, "lc_number", ""))
        lc_date = safe(getattr(pl, "lc_date", "")) if getattr(pl, "lc_date", None) else ""
        bl_no = safe(getattr(pl, "bl_number", ""))
        bl_date = safe(getattr(pl, "bl_date", "")) if getattr(pl, "bl_date", None) else ""
        so_no = safe(getattr(pl, "so_number", ""))
        so_date = safe(getattr(pl, "so_date", "")) if getattr(pl, "so_date", None) else ""
        other_ref = safe(getattr(pl, "other_references", ""))
        other_ref_date = (
            safe(getattr(pl, "other_references_date", ""))
            if getattr(pl, "other_references_date", None) else ""
        )
        if po_no:
            ref_lines.append(f"<b>PO No/Date:</b> {po_no}{(' / ' + po_date) if po_date else ''}")
        if lc_no:
            ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{(' / ' + lc_date) if lc_date else ''}")
        if bl_no:
            ref_lines.append(f"<b>BL No/Date:</b> {bl_no}{(' / ' + bl_date) if bl_date else ''}")
        if so_no:
            ref_lines.append(f"<b>SO No/Date:</b> {so_no}{(' / ' + so_date) if so_date else ''}")
        if other_ref:
            ref_lines.append(
                f"<b>Other Ref/Date:</b> {other_ref}"
                f"{(' / ' + other_ref_date) if other_ref_date else ''}"
            )
    refs_cell_html = (
        "<b>Other References</b><br/>" + "<br/>".join(ref_lines)
        if ref_lines else "<b>Other References</b>"
    )

    pi_obj = getattr(pl, "proforma_invoice", None) if pl else None
    pi_number = safe(getattr(pi_obj, "pi_number", "")) if pi_obj else ""
    ci_number = safe(getattr(ci, "ci_number", ""))

    header_tbl = Table(
        [[
            Paragraph("<b>Exporter</b>", style_label),
            "",
            Paragraph(f"<b>Proforma Invoice No.</b><br/>{pi_number}", style_text),
            Paragraph(f"<b>Commercial Invoice No.</b><br/>{ci_number}", style_text),
        ]],
        colWidths=[col_4, col_4, col_4, col_4],
    )
    header_tbl.hAlign = "LEFT"
    header_tbl.setStyle(TableStyle(_GRID + [
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
    ]))
    story.append(header_tbl)

    office_cell = _exp_cell("Corporate Office", corp_addr)
    reg_cell = _exp_cell("Registered Address", reg_addr)
    factory_cell = _exp_cell("Factory Address", factory_addr)

    if factory_addr:
        exp_tbl = Table(
            [[Paragraph(office_cell, style_text), Paragraph(reg_cell, style_text),
              Paragraph(factory_cell, style_text)]],
            colWidths=[col_3, col_3, col_3],
        )
    else:
        exp_tbl = Table(
            [[Paragraph(office_cell, style_text), Paragraph(reg_cell, style_text)]],
            colWidths=[col_2, col_2],
        )
    exp_tbl.hAlign = "LEFT"
    exp_tbl.setStyle(TableStyle(_GRID))
    story.append(exp_tbl)

    buyer_cell = _party_cell_html("Buyer", buyer if buyer else cons)
    cons_cell = _party_cell_html("Consignee", cons)

    if notify_party_org:
        notify_cell = _party_cell_html("Notify Party", notify_party_org)
        party_tbl = Table(
            [[Paragraph(buyer_cell, style_text), Paragraph(cons_cell, style_text),
              Paragraph(notify_cell, style_text)]],
            colWidths=[col_3, col_3, col_3],
        )
    else:
        party_tbl = Table(
            [[Paragraph(buyer_cell, style_text), Paragraph(cons_cell, style_text)]],
            colWidths=[col_2, col_2],
        )
    party_tbl.hAlign = "LEFT"
    party_tbl.setStyle(TableStyle(_GRID))
    story.append(party_tbl)

    pre_carriage_obj = getattr(pl, "pre_carriage_by", None) if pl else None
    pre_carriage_val = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""
    place_receipt_obj = getattr(pl, "place_of_receipt_by_pre_carrier", None) if pl else None
    place_receipt_val = safe(getattr(place_receipt_obj, "name", "")) if place_receipt_obj else ""
    port_loading_obj = getattr(pl, "port_of_loading", None) if pl else None
    port_loading_val = safe(getattr(port_loading_obj, "name", "")) if port_loading_obj else ""
    port_discharge_obj = getattr(pl, "port_of_discharge", None) if pl else None
    port_discharge_val = safe(getattr(port_discharge_obj, "name", "")) if port_discharge_obj else ""
    final_dest_obj = getattr(pl, "final_destination", None) if pl else None
    final_dest_val = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""
    dest_country_obj = getattr(pl, "country_of_final_destination", None) if pl else None
    dest_country_val = safe(getattr(dest_country_obj, "name", "")) if dest_country_obj else ""
    origin_country_obj = getattr(pl, "country_of_origin", None) if pl else None
    origin_country_val = safe(getattr(origin_country_obj, "name", "")) if origin_country_obj else ""
    vessel_flight_val = safe(getattr(pl, "vessel_flight_no", "")) if pl else ""

    shipping_tbl = Table(
        [
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
                Paragraph(f"<b>Vessel / Flight No.</b><br/>{vessel_flight_val}", style_text),
            ],
        ],
        colWidths=[col_4, col_4, col_4, col_4],
    )
    shipping_tbl.hAlign = "LEFT"
    shipping_tbl.setStyle(TableStyle(_GRID))
    story.append(shipping_tbl)

    incoterm_obj = getattr(pl, "incoterms", None) if pl else None
    incoterm_str = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""
    payment_term_obj = getattr(pl, "payment_terms", None) if pl else None
    payment_term_str = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""
    terms_tbl = Table(
        [[
            Paragraph(f"<b>Payment Terms</b><br/>{payment_term_str}", style_text),
            Paragraph(f"<b>Incoterms</b><br/>{incoterm_str}", style_text),
            Paragraph(refs_cell_html, style_text),
        ]],
        colWidths=[col_3, col_3, col_3],
    )
    terms_tbl.hAlign = "LEFT"
    terms_tbl.setStyle(TableStyle(_GRID))
    story.append(terms_tbl)
    story.append(Spacer(1, 12))

    packages_map: dict = {}
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                for pitem in cont.items.all().order_by("id"):
                    key = safe(getattr(pitem, "item_code", ""))
                    val = safe(getattr(pitem, "packages_kind", ""))
                    if not key:
                        continue
                    if key not in packages_map:
                        packages_map[key] = set()
                    if val:
                        packages_map[key].add(val)
        except Exception:
            pass

    li_header = [
        Paragraph("<b>Sr.</b>", style_table_header),
        Paragraph("<b>HSN Code</b>", style_table_header),
        Paragraph("<b>No &amp; Kind of Packages</b>", style_table_header),
        Paragraph("<b>Item Code</b>", style_table_header),
        Paragraph("<b>Description of Goods</b>", style_table_header),
        Paragraph("<b>Qty</b>", style_table_header),
        Paragraph("<b>Rate (USD)</b>", style_table_header),
        Paragraph("<b>Amount (USD)</b>", style_table_header),
    ]
    li_rows = [li_header]
    total_amount_usd = Decimal("0.00")

    idx = 0
    for it in ci.line_items.all().order_by("id"):
        idx += 1
        pkg_text = ""
        try:
            pkset = packages_map.get(safe(getattr(it, "item_code", "")), None)
            if pkset:
                pkg_text = " ; ".join(sorted(pkset))
        except Exception:
            pass

        uom_obj = getattr(it, "uom", None)
        uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
        qty_val = getattr(it, "total_quantity", None)
        rate_val = getattr(it, "rate_usd", None)
        amount_val = getattr(it, "amount_usd", None)

        if amount_val is not None:
            try:
                total_amount_usd += Decimal(str(amount_val))
            except Exception:
                pass

        li_rows.append([
            Paragraph(str(idx), style_text),
            Paragraph(safe(it.hsn_code), style_text),
            Paragraph(pkg_text, style_text),
            Paragraph(safe(it.item_code), style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{_fmt_qty(qty_val)} {uom_display}".strip(), style_text),
            Paragraph(_fmt_money(rate_val), style_text),
            Paragraph(_fmt_money(amount_val), style_text),
        ])

    # Sr(10) + HSN(22) + Packages(24) + ItemCode(20) + Desc(46) + Qty(18) + Rate(20) + Amt(20) = 180mm
    li_table = Table(
        li_rows,
        colWidths=[10 * mm, 22 * mm, 24 * mm, 20 * mm, 46 * mm, 18 * mm, 20 * mm, 20 * mm],
    )
    li_table.hAlign = "LEFT"
    li_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("ALIGN",        (6, 1), (7, -1), "RIGHT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (0, 0), 6),
        ("BOTTOMPADDING",(0, 0), (0, 0), 6),
        ("TOPPADDING",   (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 4),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 12))

    total_net_val = Decimal("0.000")
    total_gross_val = Decimal("0.000")
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                for item in cont.items.all():
                    # Use net_material_weight from container items
                    net_mat_wt = getattr(item, "net_material_weight", None)
                    if net_mat_wt is not None:
                        try:
                            total_net_val += Decimal(str(net_mat_wt))
                        except Exception:
                            pass
                # Sum container gross weights
                gw = getattr(cont, "gross_weight", None)
                if gw is not None:
                    try:
                        total_gross_val += Decimal(str(gw))
                    except Exception:
                        pass
        except Exception:
            pass

    lc_details_val = safe(getattr(ci, "lc_details", ""))
    visible_fields = _INCOTERM_VISIBLE_FIELDS.get(incoterm_str, _ALL_CI_FIELDS)

    freight_amount = Decimal("0.00")
    insurance_amount = Decimal("0.00")
    # Only include freight/insurance if the field was actually filled in (not None)
    show_freight = False
    show_insurance = False
    if "freight" in visible_fields and getattr(ci, "freight", None) is not None:
        try:
            freight_amount = Decimal(str(ci.freight))
            show_freight = True
        except Exception:
            pass
    if "insurance" in visible_fields and getattr(ci, "insurance", None) is not None:
        try:
            insurance_amount = Decimal(str(ci.insurance))
            show_insurance = True
        except Exception:
            pass
    invoice_total = total_amount_usd + freight_amount + insurance_amount

    # Build left cell: net/gross weight stacked, then optional L/C Details below
    left_inner_rows = [
        [Paragraph(f"<b>Total Net Weight:</b> {_fmt_qty(total_net_val)} KGS", style_text)],
        [Paragraph(f"<b>Total Gross Weight:</b> {_fmt_qty(total_gross_val)} KGS", style_text)],
    ]
    if lc_details_val:
        left_inner_rows.append(
            [Paragraph(f"<b>L/C Details:</b> {lc_details_val}", style_text)]
        )
    left_inner = Table(left_inner_rows, colWidths=[78 * mm])
    left_inner.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    left_cell_content = left_inner

    # Build breakdown as a nested table: label col (left) | amount col (right-aligned)
    breakdown_header = f"COST BREAKDOWN ({incoterm_str})" if incoterm_str else "COST BREAKDOWN"
    style_amt = ParagraphStyle("CIAmt", parent=style_text, alignment=TA_RIGHT)

    breakdown_rows = [
        # Header spans both sub-columns
        [Paragraph(f"<b>{breakdown_header}</b>", style_text), Paragraph("", style_text)],
        [Paragraph("FOB Value (Line Items):", style_text),
         Paragraph(f"USD {_fmt_money(total_amount_usd)}", style_amt)],
    ]
    if show_freight:
        breakdown_rows.append([
            Paragraph("Freight:", style_text),
            Paragraph(f"USD {_fmt_money(freight_amount)}", style_amt),
        ])
    if show_insurance:
        breakdown_rows.append([
            Paragraph("Insurance Amount:", style_text),
            Paragraph(f"USD {_fmt_money(insurance_amount)}", style_amt),
        ])

    # Inner widths must fit inside the 90mm outer cell (12mm used by outer padding)
    breakdown_inner = Table(breakdown_rows, colWidths=[46 * mm, 32 * mm])
    breakdown_inner.setStyle(TableStyle([
        ("SPAN",          (0, 0), (1, 0)),   # header spans both sub-columns
        ("LINEBELOW",     (0, 0), (1, 0), 0.5, colors.black),  # line under header
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    totals_charges_tbl = Table(
        [[left_cell_content, breakdown_inner]],
        colWidths=[90 * mm, 90 * mm],
    )
    totals_charges_tbl.hAlign = "LEFT"
    totals_charges_tbl.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(totals_charges_tbl)

    invoice_total_tbl = Table(
        [[
            Paragraph("<b>Invoice Total (Amount Payable)</b>", style_label),
            Paragraph(f"<b>${_fmt_money(invoice_total)}</b>", style_label),
        ]],
        colWidths=[140 * mm, 40 * mm],
    )
    invoice_total_tbl.hAlign = "LEFT"
    invoice_total_tbl.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#E8E8E8")),
    ]))
    story.append(invoice_total_tbl)
    story.append(Spacer(1, 6))

    amount_in_words_str = _amount_to_words(invoice_total, currency="USD")
    if amount_in_words_str:
        style_text_center = ParagraphStyle(
            "CITextCenter", parent=style_text, alignment=TA_CENTER,
        )
        words_table = Table(
            [[Paragraph(f"<b>Amount in Words:</b> {amount_in_words_str}", style_text_center)]],
            colWidths=[180 * mm],
        )
        words_table.setStyle(TableStyle([
            ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        words_table.hAlign = "LEFT"
        story.append(words_table)

    story.append(Spacer(1, 12))

    decl_table = Table(
        [[Paragraph(
            "<b>Declaration:</b> We declare that this invoice shows actual price of the goods "
            "described and that all particulars are true and correct.",
            style_text,
        )]],
        colWidths=[180 * mm],
    )
    decl_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    decl_table.hAlign = "LEFT"
    story.append(decl_table)
    story.append(Spacer(1, 12))

    bank = getattr(ci, "bank", None)
    if bank:
        bank_lines = []
        bank_lines.append(f"<b>BENEFICIARY NAME:</b> {safe(getattr(bank, 'beneficiary_name', ''))}")
        bank_lines.append(f"<b>BANK NAME:</b> {safe(getattr(bank, 'bank_name', ''))}")
        bank_lines.append(f"<b>BRANCH NAME:</b> {safe(getattr(bank, 'branch_name', ''))}")
        bank_lines.append(f"<b>BRANCH ADDRESS:</b> {safe(getattr(bank, 'branch_address', ''))}")
        bank_lines.append(f"<b>A/C NO.:</b> {safe(getattr(bank, 'account_number', ''))}")
        if getattr(bank, "routing_number", None):
            bank_lines.append(f"<b>IFSC CODE:</b> {safe(bank.routing_number)}")
        if getattr(bank, "swift_code", None):
            bank_lines.append(f"<b>SWIFT CODE:</b> {safe(bank.swift_code)}")
        if getattr(bank, "iban", None):
            bank_lines.append(f"<b>IBAN:</b> {safe(bank.iban)}")
        if safe(getattr(bank, "intermediary_bank_name", "")):
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
            # Explicit 4-sided line commands so each page-split fragment keeps all borders.
            ("LINEABOVE",    (0, 0),  (-1, 0),  1.2, colors.black),
            ("LINEBELOW",    (0, -1), (-1, -1), 1.2, colors.black),
            ("LINEBEFORE",   (0, 0),  (0, -1),  1.2, colors.black),
            ("LINEAFTER",    (-1, 0), (-1, -1), 1.2, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ]))
        bank_box.hAlign = "LEFT"
        story.append(bank_box)
        story.append(Spacer(1, 10))

    return story


def generate_commercial_invoice_pdf_bytes(ci) -> bytes:
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

    styles = _make_ci_styles()
    story = build_ci_story(ci, styles)
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
