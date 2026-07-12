"""
Packing List Word (.docx) section generator — transliterates
pdf/packing_list_generator.py::build_pl_story() cell-by-cell, span-by-span,
background-by-background using pdf/docx_base.py's build_grid_table() (the
direct analog of ReportLab's Table + TableStyle).

Formatting helpers (date/qty/decimal formatting, address building) are reused
from pdf/packing_list_generator.py so the Word output always matches the
PDF's numbers — never duplicate that logic here.

Constraint #9: this module never writes to disk; it only appends content to
an in-memory python-docx Document that the caller saves to a BytesIO buffer.
"""
import html
from decimal import Decimal

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Emu, Mm

from pdf.packing_list_generator import (
    _fmt_decimal,
    _fmt_qty,
    _format_address_html,
    _org_address_by_type,
    _party_html,
    fmt_date,
    safe,
)
from pdf.utils import weight_unit_for_packing_list
from pdf.docx_base import (
    CONTENT_W,
    add_title_block,
    build_grid_table as _build_grid_table,
    build_items_table,
)


def _unescape_html_entities(spec):
    """See pdf/commercial_invoice_word_generator.py's identical helper for why
    this is needed: add_html_runs only understands <b>/</b>/<br/>, not entities
    such as the "&amp;" used in "Marks &amp; Numbers" below."""
    if spec is None:
        return None
    if isinstance(spec, str):
        return html.unescape(spec)
    if isinstance(spec, dict) and "html" in spec:
        spec = dict(spec)
        spec["html"] = html.unescape(spec["html"])
    return spec


def build_grid_table(document, rows, col_widths, spans=None):
    """Thin wrapper around docx_base.build_grid_table that unescapes HTML
    entities in every cell before rendering (see _unescape_html_entities)."""
    clean_rows = [[_unescape_html_entities(cell) for cell in row] for row in rows]
    return _build_grid_table(document, clean_rows, col_widths, spans=spans)


def build_pl_word_section(document, packing_list):
    """
    Append the Packing List / Weight Note section content to `document`,
    transliterating build_pl_story()'s Table()/TableStyle() calls line-by-line.

    Args:
        document: python-docx Document being built.
        packing_list: PackingList model instance.
    """
    weight_unit = weight_unit_for_packing_list(packing_list)

    exp = getattr(packing_list, "exporter", None)
    exporter_name = safe(getattr(exp, "name", ""))

    # ---- Title block (ONE-TIME, not a repeating header) --------------------
    # Mirrors: story.append(Paragraph(exporter_name, style_company_header));
    #          story.append(Paragraph("Packing List / Weight Note", style_title))
    add_title_block(document, exporter_name, ["Packing List / Weight Note"])

    col_4 = Emu(int(CONTENT_W / 4))
    col_3 = Emu(int(CONTENT_W / 3))
    col_2 = Emu(int(CONTENT_W / 2))

    pi_obj = getattr(packing_list, "proforma_invoice", None)
    pi_number = safe(getattr(pi_obj, "pi_number", "")) if pi_obj else ""
    pi_number_with_date = pi_number
    if pi_obj:
        pi_date = getattr(pi_obj, "pi_date", None)
        if pi_date:
            pi_number_with_date = f"{pi_number} {fmt_date(pi_date)}"

    pl_number = safe(getattr(packing_list, "pl_number", ""))

    ci_number = ""
    ci_obj = None
    try:
        ci_obj = packing_list.commercial_invoice
        if ci_obj:
            ci_number = safe(getattr(ci_obj, "ci_number", ""))
    except Exception:
        pass

    office_addr = _org_address_by_type(exp, "OFFICE") or _org_address_by_type(exp, "REGISTERED")
    reg_addr = _org_address_by_type(exp, "REGISTERED")
    factory_addr = _org_address_by_type(exp, "FACTORY")

    def _exp_cell(label: str, addr) -> str:
        body = _format_address_html(exp, addr)
        return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"

    office_cell_html = _exp_cell("Corporate Office", office_addr)
    reg_cell_html = _exp_cell("Registered Office Address", reg_addr)
    factory_cell_html = _exp_cell("Factory Address", factory_addr)

    ref_lines = []
    po_no = safe(getattr(packing_list, "po_number", ""))
    po_date = fmt_date(getattr(packing_list, "po_date", None))
    lc_no = safe(getattr(packing_list, "lc_number", ""))
    lc_date = fmt_date(getattr(packing_list, "lc_date", None))
    bl_no = safe(getattr(packing_list, "bl_number", ""))
    bl_date = fmt_date(getattr(packing_list, "bl_date", None))
    so_no = safe(getattr(packing_list, "so_number", ""))
    so_date = fmt_date(getattr(packing_list, "so_date", None))
    other_ref = safe(getattr(packing_list, "other_references", ""))
    other_ref_date = fmt_date(getattr(packing_list, "other_references_date", None))

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

    from apps.workflow.constants import APPROVED
    pl_status = getattr(packing_list, "status", None)
    if pl_status == APPROVED:
        pl_date_display = ""
        try:
            from apps.workflow.models import AuditLog
            approval_log = AuditLog.objects.filter(
                document_type="packing_list",
                document_id=packing_list.id,
                action="APPROVE",
            ).order_by("-created_at").first()
            if approval_log:
                pl_date_display = fmt_date(approval_log.created_at.date())
        except Exception:
            pass
    else:
        from datetime import date
        pl_date_display = fmt_date(date.today())
    pl_number_with_date = f"{pl_number} {pl_date_display}" if pl_date_display else pl_number

    ci_number_with_date = "—"
    if ci_number and ci_obj is not None:
        try:
            ci_status = getattr(ci_obj, "status", None)
            if ci_status == APPROVED:
                ci_date_display = ""
                try:
                    from apps.workflow.models import AuditLog
                    approval_log = AuditLog.objects.filter(
                        document_type="commercial_invoice",
                        document_id=ci_obj.id,
                        action="APPROVE",
                    ).order_by("-created_at").first()
                    if approval_log:
                        ci_date_display = fmt_date(approval_log.created_at.date())
                except Exception:
                    pass
            else:
                from datetime import date
                ci_date_display = fmt_date(date.today())
            ci_number_with_date = f"{ci_number} {ci_date_display}" if ci_date_display else ci_number
        except Exception:
            ci_number_with_date = ci_number

    # ---- header_tbl: Exporter (navy, spans 2 cols) | PL No. | CI No. --------
    build_grid_table(
        document,
        [[
            {"html": "<b>Exporter</b>", "bg": "navy", "align": WD_ALIGN_PARAGRAPH.CENTER},
            None,
            {"html": f"<b>Packing List No.</b><br/>{pl_number_with_date}",
             "bg": "navy", "align": WD_ALIGN_PARAGRAPH.CENTER},
            {"html": f"<b>Commercial Invoice No.</b><br/>{ci_number_with_date}",
             "bg": "navy", "align": WD_ALIGN_PARAGRAPH.CENTER},
        ]],
        col_widths=[col_4, col_4, col_4, col_4],
        spans=[(0, 0, 0, 1)],
    )

    # ---- exp_tbl: Corporate Office | Registered Office | (Factory) ----------
    if factory_addr:
        build_grid_table(
            document,
            [[{"html": office_cell_html}, {"html": reg_cell_html}, {"html": factory_cell_html}]],
            col_widths=[col_3, col_3, col_3],
        )
    else:
        build_grid_table(
            document,
            [[{"html": office_cell_html}, {"html": reg_cell_html}]],
            col_widths=[col_2, col_2],
        )

    # ---- party_tbl: Buyer | Consignee | (Notify Party) ----------------------
    cons = getattr(packing_list, "consignee", None)
    buyer = getattr(packing_list, "buyer", None)
    notify_party = getattr(packing_list, "notify_party", None)

    buyer_org = buyer if buyer else cons
    buyer_cell_html = _party_html("Buyer", buyer_org)
    cons_cell_html = _party_html("Consignee", cons)

    if notify_party:
        notify_cell_html = _party_html("Notify Party", notify_party)
        build_grid_table(
            document,
            [[{"html": buyer_cell_html}, {"html": cons_cell_html}, {"html": notify_cell_html}]],
            col_widths=[col_3, col_3, col_3],
        )
    else:
        build_grid_table(
            document,
            [[{"html": buyer_cell_html}, {"html": cons_cell_html}]],
            col_widths=[col_2, col_2],
        )

    # ---- shipping_tbl: 4 cols x 2 rows --------------------------------------
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

    build_grid_table(
        document,
        [
            [
                {"html": f"<b>Pre-carriage by</b><br/>{pre_carriage_val}"},
                {"html": f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}"},
                {"html": f"<b>Port of Loading</b><br/>{port_loading_val}"},
                {"html": f"<b>Port of Discharge</b><br/>{port_discharge_val}"},
            ],
            [
                {"html": f"<b>Final Destination</b><br/>{final_dest_val}"},
                {"html": f"<b>Country of Final Destination</b><br/>{dest_country_val}"},
                {"html": f"<b>Country of Origin of Goods</b><br/>{origin_country_val}"},
                {"html": f"<b>Vessel / Flight No.</b><br/>{vessel_val}"},
            ],
        ],
        col_widths=[col_4, col_4, col_4, col_4],
    )

    # ---- terms_tbl: Payment Terms | Incoterms | Other References -----------
    payment_term_obj = getattr(packing_list, "payment_terms", None)
    payment_term_val = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""
    incoterm_obj = getattr(packing_list, "incoterms", None)
    incoterm_val = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""

    build_grid_table(
        document,
        [[
            {"html": f"<b>Payment Terms</b><br/>{payment_term_val}"},
            {"html": f"<b>Incoterms</b><br/>{incoterm_val}"},
            {"html": refs_cell_html},
        ]],
        col_widths=[col_3, col_3, col_3],
    )
    document.add_paragraph()

    # ---- Container sections ------------------------------------------------
    total_net = Decimal("0.000")
    total_gross = Decimal("0.000")

    for cont in packing_list.containers.all().order_by("id"):
        cont_ref = safe(getattr(cont, "container_ref", ""))
        marks = safe(getattr(cont, "marks_numbers", ""))

        # ---- cont_header: navy bar, Container | Marks & Numbers -------------
        build_grid_table(
            document,
            [[
                {"html": f"<b>Container:</b> {cont_ref}", "bg": "navy",
                 "align": WD_ALIGN_PARAGRAPH.CENTER},
                {"html": f"<b>Marks &amp; Numbers:</b> {marks}", "bg": "navy",
                 "align": WD_ALIGN_PARAGRAPH.CENTER},
            ]],
            col_widths=[col_2, col_2],
        )

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
            if gross_val is not None:
                total_gross += Decimal(str(gross_val))
        except Exception:
            pass

        # ---- weights_table: Net Weight | value | Gross Weight | value --------
        net_display = f"{_fmt_decimal(net_val, 1)} {weight_unit}" if net_val is not None else "-"
        gross_display = f"{_fmt_decimal(gross_val, 1)} {weight_unit}" if gross_val is not None else "-"
        build_grid_table(
            document,
            [[
                {"html": "<b>Net Weight</b>"},
                {"html": net_display, "align": WD_ALIGN_PARAGRAPH.RIGHT},
                {"html": "<b>Gross Weight</b>"},
                {"html": gross_display, "align": WD_ALIGN_PARAGRAPH.RIGHT},
            ]],
            col_widths=[col_4, col_4, col_4, col_4],
        )

        # ---- items_table: 9-column two-row-per-item layout (Sr spans rows) --
        headers = ["Sr", "HSN Code", "Item Code", "Description", "Batch No.",
                   "Qty", "Pkg Type", "Unit", f"Net Wt/Item ({weight_unit})",
                   f"Tare Wt/Item ({weight_unit})", f"Net Wt ({weight_unit})", f"Gross Wt ({weight_unit})"]
        rows = []
        sr = 0
        for it in cont.items.all().order_by("id"):
            sr += 1
            uom_obj = getattr(it, "uom", None)
            uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
            pkg_obj = getattr(it, "type_of_package", None)
            pkg_display = safe(getattr(pkg_obj, "name", "")) if pkg_obj else ""

            rows.append([
                str(sr),
                safe(getattr(it, "hsn_code", "")) or "-",
                safe(getattr(it, "item_code", "")) or "-",
                safe(getattr(it, "description", "")) or "-",
                safe(getattr(it, "batch_details", "")) or "-",
                _fmt_qty(getattr(it, "no_of_packages", None)) or "-",
                pkg_display or "-",
                uom_display or "-",
                _fmt_decimal(getattr(it, "qty_per_package", None), 1) or "-",
                _fmt_decimal(getattr(it, "weight_per_unit_packaging", None), 1) or "-",
                _fmt_decimal(getattr(it, "net_material_weight", None), 1) or "-",
                _fmt_decimal(getattr(it, "item_gross_weight", None), 1) or "-",
            ])

        col_widths = [Mm(6), Mm(14), Mm(14), Mm(28), Mm(14), Mm(10), Mm(14),
                      Mm(10), Mm(18), Mm(18), Mm(16), Mm(18)]
        build_items_table(document, headers, rows, col_widths, right_cols=[5, 8, 9, 10, 11])
        document.add_paragraph()

    # ---- totals_tbl: navy bar, Total Net Weight | Total Gross Weight --------
    build_grid_table(
        document,
        [[
            {"html": "<b>Total Net Weight</b>", "bg": "navy"},
            {"html": f"{_fmt_decimal(total_net, 1)} {weight_unit}", "bg": "navy",
             "align": WD_ALIGN_PARAGRAPH.RIGHT},
            {"html": "<b>Total Gross Weight</b>", "bg": "navy"},
            {"html": f"{_fmt_decimal(total_gross, 1)} {weight_unit}", "bg": "navy",
             "align": WD_ALIGN_PARAGRAPH.RIGHT},
        ]],
        col_widths=[col_4, col_4, col_4, col_4],
    )
