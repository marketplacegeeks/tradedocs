"""
Combined Packing List + Commercial Invoice PDF generator (FR-14M.13).

Produces a single in-memory PDF with two sections:
  Section 1 — Packing List / Weight Note
  Section 2 — Commercial Invoice  (starts on a new page)

Both sections share the same story.  A zero-height _SetSection flowable written
just before the PageBreak flips the section_state dict so the onPage callback
can draw the correct header and footer for each section.

Constraint #20: Returns a BytesIO buffer — never writes to disk.
"""
import io
from collections import defaultdict
from decimal import Decimal

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    PageBreak,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf.base import (
    COLOR_BLUE_ACCENT,
    COLOR_BORDER,
    COLOR_LIGHT_BG,
    COLOR_NAVY,
    COLOR_TEXT_DARK,
    COLOR_TEXT_MUTED,
    COLOR_WHITE,
    CONTENT_W,
    DOC_TOP_MARGIN,
    FONT_BODY,
    FONT_HEADING,
    FONT_LABEL,
    MARGIN_BOTTOM,
    MARGIN_H,
    PAGE_H,
    PAGE_W,
    SIZE_SECTION,
    SIZE_TABLE,
    SIZE_TABLE_HDR,
    _BODY,
    _BOLD,
    _HDR_WHITE,
    _LABEL,
    _RIGHT,
    _RIGHT_BOLD,
    _p,
    build_info_grid,
    build_party_grid,
    draw_footer,
    draw_page_header,
    draw_watermark,
    section_label,
)
from pdf.utils import currency_to_words, format_decimal, safe_str


# ---- Internal helpers --------------------------------------------------------

def _fmt(value, dp=2):
    return format_decimal(value, dp=dp)


def _date(d):
    if d is None:
        return '—'
    try:
        return d.strftime('%-d %b %Y')
    except ValueError:
        return d.strftime('%d %b %Y')


def _name(obj):
    return obj.name if obj else '—'


def _address_lines(addr):
    """Format an OrganisationAddress instance into a list of plain strings."""
    if not addr:
        return []
    lines = []
    if addr.line1:
        lines.append(addr.line1)
    if addr.line2:
        lines.append(addr.line2)
    city_state = ', '.join(filter(None, [addr.city, addr.state]))
    if city_state:
        pin = f' – {addr.pin}' if addr.pin else ''
        lines.append(f'{city_state}{pin}')
    if addr.country:
        lines.append(addr.country.name)
    return lines


def _org_primary_address_lines(org):
    """Primary (first) address of an Organisation as a list of strings."""
    if not org:
        return []
    addr = org.addresses.first()
    return _address_lines(addr) if addr else []


def _org_addresses_by_type(org):
    """Return {address_type: OrganisationAddress} for every address on org."""
    if not org:
        return {}
    return {a.address_type: a for a in org.addresses.all()}


# ---- Section-switch flowable -------------------------------------------------

class _SetSection(Flowable):
    """
    Zero-height flowable that updates section_state when drawn.
    Place this BEFORE a PageBreak so the onPage callback for the new page
    already sees the updated section name.
    """
    def __init__(self, state, section):
        super().__init__()
        self._state = state
        self._section = section
        self.width = self.height = 0

    def draw(self):
        self._state['current'] = self._section


# ---- Page callback -----------------------------------------------------------

def _make_page_callback(pl, ci, is_draft, section_state):
    exporter = pl.exporter
    addr_lines = _org_primary_address_lines(exporter)
    iec = getattr(exporter, 'iec_code', None) if exporter else None
    pl_number = pl.pl_number
    ci_number = ci.ci_number if ci else '—'
    pl_date_str = _date(pl.pl_date)
    ci_date_str = _date(ci.ci_date) if ci else '—'
    exporter_name = exporter.name if exporter else ''

    def on_page(canvas, doc):
        current = section_state['current']
        if current == 'pl':
            draw_page_header(
                canvas,
                exporter_name=exporter_name,
                exporter_addr_lines=addr_lines,
                doc_title_lines=['PACKING LIST', 'WEIGHT NOTE'],
                doc_number=pl_number,
                doc_date=pl_date_str,
                iec_code=iec,
            )
            draw_footer(canvas, pl_number)
        else:
            draw_page_header(
                canvas,
                exporter_name=exporter_name,
                exporter_addr_lines=addr_lines,
                doc_title_lines=['COMMERCIAL INVOICE'],
                doc_number=ci_number,
                doc_date=ci_date_str,
                iec_code=iec,
            )
            draw_footer(canvas, ci_number)
        if is_draft:
            draw_watermark(canvas)

    return on_page


# ---- Shared section builders -------------------------------------------------

def _build_exporter_block(pl):
    """
    3-column block: Corporate/Office address | Registered Office | Factory.
    All three columns span equal widths across CONTENT_W.
    """
    exporter = pl.exporter
    if not exporter:
        return _p('—')

    addrs = _org_addresses_by_type(exporter)
    col_w = CONTENT_W / 3

    def _make_col(label, addr):
        rows = [[_p(label.upper(), _LABEL)]]
        if addr:
            rows.append([_p(exporter.name, _BOLD)])
            for line in _address_lines(addr):
                rows.append([_p(line, _BODY)])
        else:
            rows.append([_p('—', _BODY)])

        inner = Table(rows, colWidths=[col_w - 14])
        inner.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        outer = Table([[inner]], colWidths=[col_w])
        outer.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING',   (0, 0), (-1, -1), 7),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return outer

    col_a = _make_col('Corporate Address', addrs.get('OFFICE') or addrs.get('REGISTERED'))
    col_b = _make_col('Registered Office',  addrs.get('REGISTERED'))
    col_c = _make_col('Factory Address',    addrs.get('FACTORY'))

    tbl = Table([[col_a, col_b, col_c]], colWidths=[col_w, col_w, col_w])
    tbl.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


def _build_references_block(pl):
    """Order reference fields. Only rows with a value are printed."""
    pairs = [
        ('PO No. & Date',      pl.po_number,         pl.po_date),
        ('LC No. & Date',      pl.lc_number,         pl.lc_date),
        ('BL No. & Date',      pl.bl_number,         pl.bl_date),
        ('SO No. & Date',      pl.so_number,         pl.so_date),
        ('Other Reference(s)', pl.other_references,  pl.other_references_date),
    ]
    populated = [
        (label, f'{num} / {_date(dt)}' if dt else num)
        for label, num, dt in pairs
        if num
    ]
    if not populated:
        return None

    LABEL_W = CONTENT_W * 0.28
    VALUE_W = CONTENT_W - LABEL_W
    rows = [[_p(f'{lbl}:', _BOLD), _p(val, _BODY)] for lbl, val in populated]

    tbl = Table(rows, colWidths=[LABEL_W, VALUE_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


def _build_parties(pl):
    """Consignee + Buyer (if set) party boxes."""
    parties = [
        ('Advising Bank / Consignee',
         pl.consignee.name if pl.consignee else '—',
         _org_primary_address_lines(pl.consignee)),
    ]
    if pl.buyer:
        parties.append((
            'Buyer (if other than Consignee)',
            pl.buyer.name,
            _org_primary_address_lines(pl.buyer),
        ))
    return build_party_grid(parties)


def _build_notify_countries(pl):
    """Notify Party + Country of Origin + Country of Final Destination."""
    parties = [
        ('Consignee / Notify Party',
         pl.notify_party.name if pl.notify_party else '—',
         _org_primary_address_lines(pl.notify_party) if pl.notify_party else []),
        ('Country of Origin of Goods',
         _name(pl.country_of_origin), []),
        ('Country of Final Destination',
         _name(pl.country_of_final_destination), []),
    ]
    return build_party_grid(parties)


def _build_shipping_grid(pl):
    """Grid of shipping & logistics fields."""
    cells = [
        ('Pre-Carriage By',                  _name(pl.pre_carriage_by)),
        ('Place of Receipt by Pre-Carrier',  safe_str(pl.place_of_receipt_by_pre_carrier)),
        ('Vessel / Flight No',               safe_str(pl.vessel_flight_no)),
        ('Port of Loading',                  safe_str(pl.port_of_loading)),
        ('Port of Discharge',                safe_str(pl.port_of_discharge)),
        ('Final Destination',                safe_str(pl.final_destination)),
    ]
    return build_info_grid(cells, cols=3)


def _build_terms_grid(pl):
    """Incoterms, Payment Terms, Additional Description."""
    incoterms_str = '—'
    if pl.incoterms:
        code = pl.incoterms.code or ''
        desc = pl.incoterms.description or ''
        incoterms_str = f'{code} – {desc}' if desc else code

    cells = [
        ('Incoterms',             incoterms_str),
        ('Payment Terms',         _name(pl.payment_terms)),
        ('Additional Description', safe_str(pl.additional_description)),
    ]
    return build_info_grid(cells, cols=3)


# ---- PL-specific section builders -------------------------------------------

_SUBTOTAL_BG = HexColor('#E8EEF5')


def _build_pl_items_table(containers):
    """
    Packing details table grouped by container.
    After each container's items a subtotal row shows Item Gross sum, Tare, Container Gross.
    Returns (table, total_net_weight, total_gross_weight).
    """
    headers = [
        'Marks & Nos.\nContainer Nos.',
        'HSN', 'Item Code', 'No. & Kind\nof Pkgs.', 'Description',
        'Qty', 'UOM',
        'Net Wt\n/Unit', 'Total\nNet Wt',
        'Inner\nPkg Wt', 'Item\nGross Wt', 'Batch',
    ]
    # Column widths — total must equal CONTENT_W (≈ 538 pt for A4 at 18mm margins)
    COL_W = [52, 30, 38, 42, 0, 28, 20, 30, 30, 28, 32, 42]
    COL_W[4] = int(CONTENT_W - sum(COL_W))   # remainder goes to Description

    header_row = [_p(h, _HDR_WHITE) for h in headers]
    all_rows = [header_row]
    subtotal_indices = []

    total_net = Decimal('0.000')
    total_gross = Decimal('0.000')

    for container in containers:
        # Build marks string shown in every row for this container.
        marks = container.container_ref
        if container.marks_numbers:
            marks = f'{container.marks_numbers}\n({container.container_ref})'

        items = list(container.items.all())
        sum_item_gross = Decimal('0.000')

        for item in items:
            total_item_net = item.net_weight * item.quantity
            total_net += total_item_net
            sum_item_gross += item.item_gross_weight
            uom_abbr = item.uom.abbreviation if item.uom else ''
            all_rows.append([
                _p(marks),
                _p(safe_str(item.hsn_code, fallback='')),
                _p(item.item_code),
                _p(safe_str(item.packages_kind, fallback='')),
                _p(item.description),
                _p(_fmt(item.quantity, dp=3), _RIGHT),
                _p(uom_abbr),
                _p(_fmt(item.net_weight, dp=3), _RIGHT),
                _p(_fmt(total_item_net, dp=3), _RIGHT),
                _p(_fmt(item.inner_packing_weight, dp=3), _RIGHT),
                _p(_fmt(item.item_gross_weight, dp=3), _RIGHT),
                _p(safe_str(item.batch_details, fallback='')),
            ])

        # Container subtotal row
        container_gross = container.gross_weight   # stored: SUM(item_gross) + tare
        total_gross += container_gross
        sub_idx = len(all_rows)
        subtotal_indices.append(sub_idx)
        all_rows.append([
            _p(f'Sum item gross: {_fmt(sum_item_gross, dp=3)}', _BOLD),
            _p(''), _p(''), _p(''), _p(''),
            _p(''), _p(''), _p(''),
            _p(f'Tare: {_fmt(container.tare_weight, dp=3)}', _BOLD),
            _p(''),
            _p(f'Container gross: {_fmt(container_gross, dp=3)}', _BOLD),
            _p(''),
        ])

    # Build table style
    cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0), COLOR_NAVY),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('FONTNAME',      (0, 0), (-1, -1), FONT_BODY),
        ('FONTSIZE',      (0, 0), (-1, -1), SIZE_TABLE - 1),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    # Right-align numeric columns
    for col in [5, 7, 8, 9, 10]:
        cmds.append(('ALIGN', (col, 0), (col, -1), 'RIGHT'))

    # Alternate-shading for data rows (excluding header at 0 and subtotal rows)
    subtotal_set = set(subtotal_indices)
    data_rows = [i for i in range(1, len(all_rows)) if i not in subtotal_set]
    for i in range(1, len(data_rows), 2):
        cmds.append(('BACKGROUND', (0, data_rows[i]), (-1, data_rows[i]), COLOR_LIGHT_BG))

    # Subtotal row styling
    for idx in subtotal_indices:
        cmds.extend([
            ('BACKGROUND', (0, idx), (-1, idx), _SUBTOTAL_BG),
            ('LINEABOVE',  (0, idx), (-1, idx), 0.75, COLOR_NAVY),
            ('FONTNAME',   (0, idx), (-1, idx), FONT_LABEL),
        ])

    tbl = Table(all_rows, colWidths=COL_W, repeatRows=1)
    tbl.setStyle(TableStyle(cmds))
    return tbl, total_net, total_gross


def _build_weight_summary(containers, total_net, total_gross):
    """
    Bottom weight block: container reference list (left) + per-container tare table (right).
    """
    LEFT_W  = CONTENT_W * 0.45
    RIGHT_W = CONTENT_W - LEFT_W

    # Left side: container refs + shipment totals
    left_data = [
        [_p('Container / Tank No.', _BOLD), _p(''), _p('')],
    ]
    for c in containers:
        left_data.append([_p(c.container_ref, _BODY), _p(''), _p('')])

    left_data.append([
        _p('Total Net Weight:', _BOLD),
        _p(_fmt(total_net, dp=3), _RIGHT),
        _p('MT'),
    ])
    left_data.append([
        _p('Total Gross Weight:', _BOLD),
        _p(_fmt(total_gross, dp=3), _RIGHT),
        _p('MT'),
    ])

    ca, cb, cc = LEFT_W * 0.52, LEFT_W * 0.30, LEFT_W * 0.18
    left_tbl = Table(left_data, colWidths=[ca, cb, cc])
    left_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), COLOR_NAVY),
        ('FONTNAME',      (0, 0), (-1, 0), FONT_LABEL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), COLOR_WHITE),
        ('SPAN',          (0, 0), (2, 0)),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
    ]))

    # Right side: per-container tare table
    total_tare = sum((c.tare_weight for c in containers), Decimal('0.000'))
    right_data = [[_p('Container No.', _BOLD), _p('Tare Wt', _BOLD)]]
    for c in containers:
        right_data.append([_p(c.container_ref, _BODY), _p(_fmt(c.tare_weight, dp=3), _RIGHT)])
    right_data.append([_p('Total TARE Wt', _BOLD), _p(_fmt(total_tare, dp=3), _RIGHT_BOLD)])

    right_tbl = Table(right_data, colWidths=[RIGHT_W * 0.58, RIGHT_W * 0.42])
    right_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), COLOR_NAVY),
        ('FONTNAME',      (0, 0), (-1, 0), FONT_LABEL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), COLOR_WHITE),
        ('BACKGROUND',    (0, -1), (-1, -1), COLOR_LIGHT_BG),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
    ]))

    outer = Table([[left_tbl, right_tbl]], colWidths=[LEFT_W, RIGHT_W])
    outer.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return outer


def _build_signature_block():
    """Right-aligned 'Authorised Signatory' block."""
    SIG_W = CONTENT_W * 0.40
    sig_inner = Table([
        [_p('For', _BODY)],
        [Spacer(1, 10 * mm)],
        [_p('_' * 30, _BOLD)],
        [_p('Authorised Signatory', _LABEL)],
    ], colWidths=[SIG_W])
    sig_inner.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    outer = Table([[_p(''), sig_inner]], colWidths=[CONTENT_W - SIG_W, SIG_W])
    outer.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return outer


# ---- CI-specific section builders -------------------------------------------

def _build_ci_items_table(pl, containers, ci):
    """
    Items table aggregated by Item Code + UOM across all containers.
    Rate and Amount columns are shown here (not on the PL section).
    Returns (table, total_amount, total_net_weight).
    """
    if not ci:
        return _p('No Commercial Invoice linked.'), Decimal('0.00'), Decimal('0.000')

    line_items = list(ci.line_items.select_related('uom').order_by('id').all())
    if not line_items:
        return _p('No line items found.'), Decimal('0.00'), Decimal('0.000')

    # Build a lookup: (item_code, uom_id) → {net_weight_per_unit, marks_list, packages_kind_parts}
    item_info = defaultdict(lambda: {
        'net_weight': Decimal('0.000'),
        'marks': [],
    })
    for container in containers:
        marks = container.marks_numbers or container.container_ref
        ref = container.container_ref
        marks_label = f'{marks} ({ref})' if marks != ref else ref
        for item in container.items.all():
            key = (item.item_code, item.uom_id)
            if item_info[key]['net_weight'] == Decimal('0.000'):
                item_info[key]['net_weight'] = item.net_weight
            if marks_label not in item_info[key]['marks']:
                item_info[key]['marks'].append(marks_label)

    # Dynamic rate column header based on unique UOMs
    uoms = {li.uom.abbreviation for li in line_items if li.uom}
    rate_header = f'Rate (USD per {next(iter(uoms))})' if len(uoms) == 1 else 'Rate (USD)'

    headers = [
        'Marks & Nos.\nContainer Nos.',
        'HSN', 'No. & Kind\nof Pkgs.', 'Description', 'Item Code',
        'Qty', 'UOM',
        'Net Wt\n/Unit', 'Total\nNet Wt',
        rate_header, 'Amount\n(USD)',
    ]
    COL_W = [52, 30, 42, 0, 38, 28, 20, 30, 30, 45, 45]
    COL_W[3] = int(CONTENT_W - sum(COL_W))   # remainder to Description

    header_row = [_p(h, _HDR_WHITE) for h in headers]
    all_rows = [header_row]

    total_amount = Decimal('0.00')
    total_net_weight = Decimal('0.000')

    for li in line_items:
        key = (li.item_code, li.uom_id)
        info = item_info.get(key, {})
        marks_str = '\n'.join(info.get('marks', []))
        net_per_unit = info.get('net_weight', Decimal('0.000'))
        total_net = net_per_unit * li.total_quantity
        total_net_weight += total_net
        total_amount += li.amount_usd or Decimal('0.00')
        uom_abbr = li.uom.abbreviation if li.uom else ''

        all_rows.append([
            _p(marks_str),
            _p(safe_str(li.hsn_code, fallback='')),
            _p(safe_str(li.packages_kind, fallback='')),
            _p(li.description),
            _p(li.item_code),
            _p(_fmt(li.total_quantity, dp=3), _RIGHT),
            _p(uom_abbr),
            _p(_fmt(net_per_unit, dp=3), _RIGHT),
            _p(_fmt(total_net, dp=3), _RIGHT),
            _p(_fmt(li.rate_usd), _RIGHT),
            _p(_fmt(li.amount_usd), _RIGHT),
        ])

    cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0), COLOR_NAVY),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('FONTNAME',      (0, 0), (-1, -1), FONT_BODY),
        ('FONTSIZE',      (0, 0), (-1, -1), SIZE_TABLE - 1),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for col in [5, 7, 8, 9, 10]:
        cmds.append(('ALIGN', (col, 0), (col, -1), 'RIGHT'))
    for i in range(2, len(all_rows), 2):
        cmds.append(('BACKGROUND', (0, i), (-1, i), COLOR_LIGHT_BG))

    tbl = Table(all_rows, colWidths=COL_W, repeatRows=1)
    tbl.setStyle(TableStyle(cmds))
    return tbl, total_amount, total_net_weight


def _build_ci_bottom(ci, total_amount, total_net_weight, total_gross_weight):
    """
    Two-column block: weight totals + L/C details (left) | Break-up in USD (right).
    """
    fob_rate  = ci.fob_rate  or Decimal('0.00')
    freight   = ci.freight   or Decimal('0.00')
    insurance = ci.insurance or Decimal('0.00')

    LEFT_W  = CONTENT_W * 0.50
    RIGHT_W = CONTENT_W - LEFT_W

    left_rows = [
        [_p('Total Net Weight:', _BOLD),
         _p(f'{_fmt(total_net_weight, dp=3)} MT', _RIGHT)],
        [_p('Total Gross Weight:', _BOLD),
         _p(f'{_fmt(total_gross_weight, dp=3)} MT', _RIGHT)],
    ]
    if ci.lc_details:
        left_rows.append([_p('L/C Details:', _BOLD), _p(ci.lc_details, _BODY)])

    left_tbl = Table(left_rows, colWidths=[LEFT_W * 0.45, LEFT_W * 0.55])
    left_tbl.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
    ]))

    right_rows = [
        [_p('BREAK-UP IN USD (APPROX.)',
            ParagraphStyle('buhdr', fontName=FONT_LABEL, fontSize=SIZE_TABLE_HDR,
                           leading=10, textColor=COLOR_WHITE)),
         _p('')],
        [_p('FOB Rate', _LABEL),     _p(_fmt(fob_rate), _RIGHT)],
        [_p('Freight', _LABEL),      _p(_fmt(freight), _RIGHT)],
        [_p('Insurance', _LABEL),    _p(_fmt(insurance), _RIGHT)],
    ]
    right_tbl = Table(right_rows, colWidths=[RIGHT_W * 0.55, RIGHT_W * 0.45])
    right_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), COLOR_NAVY),
        ('SPAN',          (0, 0), (1, 0)),
        ('BACKGROUND',    (0, 1), (-1, -1), COLOR_LIGHT_BG),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN',         (1, 1), (1, -1), 'RIGHT'),
    ]))

    outer = Table([[left_tbl, right_tbl]], colWidths=[LEFT_W, RIGHT_W])
    outer.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return outer


def _build_grand_total_row(total_amount):
    """Full-width navy banner with grand total."""
    tbl = Table([[
        _p('Amount Chargeable in Currency: USD', ParagraphStyle(
            'gt_lbl', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
            leading=11, textColor=COLOR_WHITE)),
        _p(f'Total: {_fmt(total_amount)}', ParagraphStyle(
            'gt_val', fontName=FONT_HEADING, fontSize=SIZE_TABLE,
            leading=11, textColor=COLOR_WHITE)),
    ]], colWidths=[CONTENT_W * 0.65, CONTENT_W * 0.35])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOR_NAVY),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN',         (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl


def _build_amount_words_box(amount):
    """Italic amount-in-words box with blue left accent."""
    text = f'<b>Amount in Words:</b> {currency_to_words(amount)} US-Dollar(s) Only.'
    p = _p(text, ParagraphStyle(
        'amt_words_plci', fontName=FONT_BODY, fontSize=SIZE_TABLE,
        leading=12, textColor=COLOR_NAVY,
    ))
    tbl = Table([[p]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('LINEBEFORE',    (0, 0), (0, -1),  3, COLOR_BLUE_ACCENT),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _build_bank_block(ci):
    """Bank details block for the CI section. Returns None if no bank linked."""
    if not ci or not ci.bank_id:
        return None
    bank = ci.bank
    ACCENT = 4
    LABEL_W = CONTENT_W * 0.28
    VALUE_W = CONTENT_W - ACCENT - LABEL_W

    pairs = [
        ('Beneficiary Name', bank.beneficiary_name),
        ('Bank Name',        bank.bank_name),
        ('Branch',           bank.branch_name or '—'),
        ('Branch Address',   bank.branch_address or '—'),
        ('Account No.',      bank.account_number),
        ('IFSC / Routing',   bank.routing_number or '—'),
        ('SWIFT Code',       bank.swift_code or '—'),
    ]
    if bank.iban:
        pairs.append(('IBAN', bank.iban))
    if bank.intermediary_bank_name:
        ccy = bank.intermediary_currency.code if bank.intermediary_currency_id else ''
        pairs.extend([
            (f'Intermediary Bank ({ccy})', bank.intermediary_bank_name),
            ('  SWIFT',  bank.intermediary_swift_code or '—'),
        ])

    hdr_style = ParagraphStyle(
        'bnk_hdr', fontName=FONT_LABEL, fontSize=SIZE_TABLE_HDR,
        leading=10, textColor=COLOR_WHITE,
    )
    all_rows = [['', _p('BENEFICIARY BANK DETAILS', hdr_style), '']]
    for lbl, val in pairs:
        all_rows.append(['', _p(lbl, _LABEL), _p(str(val or '—'), _BODY)])

    tbl = Table(all_rows, colWidths=[ACCENT, LABEL_W, VALUE_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), COLOR_BLUE_ACCENT),
        ('BACKGROUND',    (1, 0), (2, 0),  COLOR_NAVY),
        ('BACKGROUND',    (1, 1), (2, -1), COLOR_LIGHT_BG),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (0, -1), 0),
        ('RIGHTPADDING',  (0, 0), (0, -1), 0),
        ('TOPPADDING',    (0, 0), (0, -1), 0),
        ('BOTTOMPADDING', (0, 0), (0, -1), 0),
        ('LEFTPADDING',   (1, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (1, 0), (-1, -1), 8),
        ('TOPPADDING',    (1, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (1, 0), (-1, -1), 3),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


# ---- Main generator ----------------------------------------------------------

def generate_pl_ci_pdf(pl) -> io.BytesIO:
    """
    Generate a combined Packing List + Commercial Invoice PDF.
    Returns an in-memory BytesIO buffer — constraint #20: never writes to disk.

    The PDF has two sections:
      Section 1 — Packing List / Weight Note
      Section 2 — Commercial Invoice  (starts on a new page)
    """
    from apps.workflow.constants import APPROVED

    # Prefetch all related data once to avoid N+1 queries during story building.
    containers = list(
        pl.containers
        .prefetch_related('items__uom')
        .select_related('packing_list')
        .order_by('id')
        .all()
    )

    try:
        ci = pl.commercial_invoice
        # Ensure bank and line items are loaded.
        _ = ci.bank_id
        _ = list(ci.line_items.select_related('uom').all())
    except Exception:
        ci = None

    is_draft = pl.status != APPROVED
    section_state = {'current': 'pl'}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=DOC_TOP_MARGIN,
        bottomMargin=MARGIN_BOTTOM,
    )

    on_page = _make_page_callback(pl, ci, is_draft, section_state)
    story = []

    # =========================================================================
    # SECTION 1 — PACKING LIST / WEIGHT NOTE
    # =========================================================================
    story.append(_SetSection(section_state, 'pl'))

    story.append(section_label('Document Numbers'))
    story.append(Spacer(1, 2 * mm))
    story.append(build_info_grid([
        ('Packing List No.', pl.pl_number),
        ('PL Date',          _date(pl.pl_date)),
        ('Commercial Invoice No.', ci.ci_number if ci else '—'),
        ('CI Date',          _date(ci.ci_date) if ci else '—'),
    ], cols=4))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Exporter'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_exporter_block(pl))
    story.append(Spacer(1, 3 * mm))

    ref_block = _build_references_block(pl)
    if ref_block:
        story.append(section_label('Order References'))
        story.append(Spacer(1, 2 * mm))
        story.append(ref_block)
        story.append(Spacer(1, 3 * mm))

    story.append(section_label('Parties'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_parties(pl))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_notify_countries(pl))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Shipping & Logistics'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_shipping_grid(pl))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_terms_grid(pl))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Packing Details'))
    story.append(Spacer(1, 2 * mm))
    pl_items_tbl, total_net, total_gross = _build_pl_items_table(containers)
    story.append(pl_items_tbl)
    story.append(Spacer(1, 3 * mm))

    story.append(_build_weight_summary(containers, total_net, total_gross))
    story.append(Spacer(1, 5 * mm))
    story.append(_build_signature_block())

    # =========================================================================
    # SECTION 2 — COMMERCIAL INVOICE
    # Switch section BEFORE the page break so the CI page header fires correctly.
    # =========================================================================
    story.append(_SetSection(section_state, 'ci'))
    story.append(PageBreak())

    story.append(section_label('Document Numbers'))
    story.append(Spacer(1, 2 * mm))
    story.append(build_info_grid([
        ('Packing List No.', pl.pl_number),
        ('PL Date',          _date(pl.pl_date)),
        ('Commercial Invoice No.', ci.ci_number if ci else '—'),
        ('CI Date',          _date(ci.ci_date) if ci else '—'),
    ], cols=4))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Exporter'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_exporter_block(pl))
    story.append(Spacer(1, 3 * mm))

    if ref_block:
        story.append(section_label('Order References'))
        story.append(Spacer(1, 2 * mm))
        story.append(_build_references_block(pl))
        story.append(Spacer(1, 3 * mm))

    story.append(section_label('Parties'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_parties(pl))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_notify_countries(pl))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Shipping & Logistics'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_shipping_grid(pl))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_terms_grid(pl))
    story.append(Spacer(1, 3 * mm))

    story.append(section_label('Commercial Invoice Items'))
    story.append(Spacer(1, 2 * mm))
    ci_tbl, total_amount, ci_total_net = _build_ci_items_table(pl, containers, ci)
    story.append(ci_tbl)
    story.append(Spacer(1, 3 * mm))

    if ci:
        story.append(_build_ci_bottom(ci, total_amount, ci_total_net, total_gross))
        story.append(Spacer(1, 3 * mm))

    story.append(_build_grand_total_row(total_amount))
    story.append(Spacer(1, 3 * mm))
    story.append(_build_amount_words_box(total_amount))
    story.append(Spacer(1, 3 * mm))

    # Declaration
    decl_style = ParagraphStyle(
        'decl', fontName=FONT_BODY, fontSize=SIZE_TABLE - 0.5,
        leading=11, textColor=COLOR_TEXT_MUTED,
    )
    story.append(_p(
        'We declare that this invoice shows the actual price of the goods described '
        'and that all particulars are true and correct.',
        decl_style,
    ))
    story.append(Spacer(1, 3 * mm))

    bank_block = _build_bank_block(ci)
    if bank_block:
        story.append(bank_block)
        story.append(Spacer(1, 3 * mm))

    story.append(_build_signature_block())

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
