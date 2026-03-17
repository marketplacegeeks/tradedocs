"""
Shared design-system constants and drawing utilities for all TradeDocs PDF generators.

Import colours, fonts, and helpers from here — never hardcode them in individual
generators.  All canvas-drawing helpers receive a ReportLab Canvas instance.
"""
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

# ---- Colour palette ----------------------------------------------------------
COLOR_NAVY        = HexColor('#0A3D62')   # table headers, section rules
COLOR_BLUE_ACCENT = HexColor('#1E88E5')   # left accent bar, banking box border
COLOR_LIGHT_BG    = HexColor('#F4F7FB')   # alternating rows, info boxes
COLOR_BORDER      = HexColor('#D0DCE8')   # all borders and dividers
COLOR_TEXT_DARK   = HexColor('#1A1A2E')   # body text
COLOR_TEXT_MUTED  = HexColor('#5A7A9F')   # labels, section headers
COLOR_DRAFT_RED   = HexColor('#CC0000')   # watermark (alpha 0.07)
COLOR_WHITE       = white

# ---- Fonts (ReportLab built-ins — no external files required) ----------------
FONT_HEADING = 'Times-Bold'       # company name, document title
FONT_LABEL   = 'Helvetica-Bold'   # section labels, table headers
FONT_BODY    = 'Helvetica'        # body text, data cells
FONT_ITALIC  = 'Helvetica-Oblique'
FONT_MONO    = 'Courier'          # batch numbers, reference codes

# ---- Type sizes (pt) ---------------------------------------------------------
SIZE_COMPANY   = 14
SIZE_DOC_TITLE = 12
SIZE_SECTION   =  7
SIZE_BODY      =  9
SIZE_SMALL     =  7.5
SIZE_TABLE     =  8.5
SIZE_TABLE_HDR =  7

# ---- Page geometry -----------------------------------------------------------
PAGE_W, PAGE_H = A4
MARGIN_H       = 18 * mm    # left / right margin
MARGIN_TOP     = 15 * mm    # gap between paper edge and header top
MARGIN_BOTTOM  = 20 * mm    # gap between paper edge and footer bottom
CONTENT_W      = PAGE_W - 2 * MARGIN_H
HEADER_H       = 24 * mm    # height of the canvas-drawn page header

# Platypus SimpleDocTemplate topMargin must clear the physical margin + header.
DOC_TOP_MARGIN = MARGIN_TOP + HEADER_H


# ---- Paragraph style helpers -------------------------------------------------

_BODY = ParagraphStyle(
    'td_body', fontName=FONT_BODY, fontSize=SIZE_TABLE,
    leading=11, textColor=COLOR_TEXT_DARK,
)
_BOLD = ParagraphStyle(
    'td_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
    leading=11, textColor=COLOR_TEXT_DARK,
)
_LABEL = ParagraphStyle(
    'td_label', fontName=FONT_BODY, fontSize=SIZE_SECTION,
    leading=9, textColor=COLOR_TEXT_MUTED,
)
_RIGHT = ParagraphStyle(
    'td_right', fontName=FONT_BODY, fontSize=SIZE_TABLE,
    leading=11, alignment=TA_RIGHT, textColor=COLOR_TEXT_DARK,
)
_RIGHT_BOLD = ParagraphStyle(
    'td_right_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
    leading=11, alignment=TA_RIGHT, textColor=COLOR_TEXT_DARK,
)
_ITALIC = ParagraphStyle(
    'td_italic', fontName=FONT_ITALIC, fontSize=SIZE_TABLE,
    leading=11, textColor=COLOR_NAVY,
)
_SECTION_STYLE = ParagraphStyle(
    'td_section', fontName=FONT_LABEL, fontSize=SIZE_SECTION,
    leading=9, textColor=COLOR_TEXT_MUTED, spaceBefore=8, spaceAfter=2,
)
_HDR_WHITE = ParagraphStyle(
    'td_hdr_white', fontName=FONT_LABEL, fontSize=SIZE_TABLE_HDR,
    leading=10, textColor=COLOR_WHITE,
)
_NAVY_WHITE = ParagraphStyle(
    'td_navy_white', fontName=FONT_LABEL, fontSize=SIZE_SECTION,
    leading=9, textColor=COLOR_WHITE,
)


def _p(text, style=None):
    """Create a Paragraph; coerce None/empty to a safe empty string."""
    return Paragraph(str(text or ''), style or _BODY)


def section_label(text):
    """Return a Paragraph styled as a section label (ALL CAPS, muted blue-grey)."""
    return _p(text.upper(), _SECTION_STYLE)


# ---- Canvas drawing helpers --------------------------------------------------

def draw_watermark(canvas):
    """Faint diagonal 'DRAFT' watermark. Call for all non-APPROVED documents."""
    canvas.saveState()
    canvas.setFont(FONT_HEADING, 80)
    canvas.setFillColor(COLOR_DRAFT_RED, alpha=0.07)
    canvas.translate(PAGE_W / 2, PAGE_H / 2)
    canvas.rotate(35)
    canvas.drawCentredString(0, 0, 'DRAFT')
    canvas.restoreState()


def draw_footer(canvas, doc_number):
    """Hairline rule + document reference (left) + page number (right)."""
    canvas.saveState()
    y_rule = MARGIN_BOTTOM - 5 * mm
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_H, y_rule + 5, PAGE_W - MARGIN_H, y_rule + 5)
    canvas.setFont(FONT_BODY, 6.5)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawString(
        MARGIN_H, y_rule,
        f'{doc_number} · This is a computer-generated document.',
    )
    canvas.drawRightString(
        PAGE_W - MARGIN_H, y_rule,
        f'Page {canvas.getPageNumber()}',
    )
    canvas.restoreState()


def draw_page_header(canvas, exporter_name, exporter_addr_lines,
                     doc_title_lines, doc_number, doc_date, iec_code=None):
    """
    Canvas-drawn page header: left = company info, right = document title + ref.
    Called from page callbacks so it appears on every page.
    """
    canvas.saveState()

    y_top    = PAGE_H - MARGIN_TOP          # top of header area
    y_bottom = y_top - HEADER_H             # bottom of header area (where hairline sits)
    x_left   = MARGIN_H
    x_right  = PAGE_W - MARGIN_H
    mid_x    = x_left + CONTENT_W * 0.55   # left block ends here

    # --- Blue left accent bar (4 pt wide) ------------------------------------
    canvas.setFillColor(COLOR_BLUE_ACCENT)
    canvas.rect(x_left, y_bottom, 4, HEADER_H, fill=1, stroke=0)

    text_x = x_left + 8   # text starts just after the accent bar

    # --- Company name ---------------------------------------------------------
    canvas.setFont(FONT_HEADING, SIZE_COMPANY)
    canvas.setFillColor(COLOR_TEXT_DARK)
    y_cursor = y_top - SIZE_COMPANY - 1
    canvas.drawString(text_x, y_cursor, exporter_name or '')

    if iec_code:
        y_cursor -= 10
        canvas.setFont(FONT_BODY, SIZE_SMALL)
        canvas.setFillColor(COLOR_TEXT_MUTED)
        canvas.drawString(text_x, y_cursor, f'IEC: {iec_code}')

    # --- Address lines --------------------------------------------------------
    canvas.setFont(FONT_BODY, SIZE_SMALL)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    for line in (exporter_addr_lines or []):
        y_cursor -= 10
        canvas.drawString(text_x, y_cursor, line)

    # --- Right side: document title ------------------------------------------
    canvas.setFont(FONT_HEADING, SIZE_DOC_TITLE)
    canvas.setFillColor(COLOR_NAVY)
    y_right = y_top - SIZE_DOC_TITLE - 1
    for title_line in (doc_title_lines or []):
        canvas.drawRightString(x_right, y_right, title_line.upper())
        y_right -= SIZE_DOC_TITLE + 3

    # --- Doc number + date ---------------------------------------------------
    canvas.setFont(FONT_BODY, SIZE_SMALL)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    y_right -= 4
    canvas.drawRightString(x_right, y_right, f'No: {doc_number}')
    if doc_date:
        y_right -= 10
        canvas.drawRightString(x_right, y_right, f'Date: {doc_date}')

    # --- Bottom hairline rule ------------------------------------------------
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(x_left, y_bottom, x_right, y_bottom)

    canvas.restoreState()


# ---- Platypus table builders -------------------------------------------------

def build_items_table(headers, rows, col_widths, right_cols=None):
    """
    Styled line-items table.
    headers   : list[str]
    rows      : list[list[Paragraph | str]]  — each inner list is one data row
    col_widths: list[float]  (pt)
    right_cols: list[int]    — 0-based column indices to right-align
    """
    right_cols = set(right_cols or [])
    header_row = [_p(h, _HDR_WHITE) for h in headers]
    all_rows = [header_row] + rows

    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('FONTNAME', (0, 0), (-1, -1), FONT_BODY),
        ('FONTSIZE', (0, 0), (-1, -1), SIZE_TABLE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    # Alternating row shading (data rows only — skip header at index 0)
    for i in range(2, len(all_rows), 2):
        cmds.append(('BACKGROUND', (0, i), (-1, i), COLOR_LIGHT_BG))

    for c in right_cols:
        cmds.append(('ALIGN', (c, 0), (c, -1), 'RIGHT'))

    tbl = Table(all_rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(cmds))
    return tbl


def build_info_grid(cells, cols=4):
    """
    Grid of labelled info boxes (shipping details, reference numbers, etc.).
    cells: list of (label, value) tuples.  Padded to fill complete rows.
    """
    cell_w = CONTENT_W / cols
    pad_count = (-len(cells)) % cols
    cells = list(cells) + [('', '')] * pad_count

    def _cell(label, value):
        content = Table(
            [[_p(label.upper(), _LABEL)], [_p(value or '—', _BOLD)]],
            colWidths=[cell_w - 14],
        )
        content.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        outer = Table([[content]], colWidths=[cell_w])
        outer.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING',   (0, 0), (-1, -1), 7),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return outer

    rows = []
    for i in range(0, len(cells), cols):
        rows.append([_cell(lbl, val) for lbl, val in cells[i:i + cols]])

    grid = Table(rows, colWidths=[cell_w] * cols)
    grid.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return grid


def build_party_grid(parties, gap=6):
    """
    Row of party boxes (Consignee, Buyer, Notify Party, etc.).
    parties: list of (label, name, [detail_line, ...]) tuples.
    All boxes share equal width across CONTENT_W.
    """
    n = len(parties)
    box_w = (CONTENT_W - gap * (n - 1)) / n

    def _box(label, name, detail_lines):
        content_rows = [[_p(label.upper(), _LABEL)], [_p(name or '—', _BOLD)]]
        for line in (detail_lines or []):
            if line:
                content_rows.append([_p(line, _BODY)])
        inner = Table(content_rows, colWidths=[box_w - 18])
        inner.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        outer = Table([[inner]], colWidths=[box_w])
        outer.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING',   (0, 0), (-1, -1), 9),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return outer

    boxes = [_box(lbl, name, lines) for lbl, name, lines in parties]
    # Spacers between boxes using a single-row table with equal-width columns
    col_widths = []
    for i, _ in enumerate(boxes):
        col_widths.append(box_w)
        if i < n - 1:
            col_widths.append(gap)

    row = []
    for i, box in enumerate(boxes):
        row.append(box)
        if i < n - 1:
            row.append('')   # gap cell

    tbl = Table([row], colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


def build_banking_box(bank):
    """
    Returns a Table styled as the banking details box.
    Left edge has a 4pt blue accent strip. Background is light grey.
    Returns None if bank is None.
    """
    if not bank:
        return None

    pairs = [
        ('Beneficiary Name', bank.beneficiary_name),
        ('Bank Name',        bank.bank_name),
        ('Branch',           bank.branch_name),
        ('Branch Address',   bank.branch_address or '—'),
        ('Account No.',      bank.account_number),
        ('IFSC / Routing',   bank.routing_number or '—'),
        ('SWIFT Code',       bank.swift_code or '—'),
    ]
    if bank.iban:
        pairs.append(('IBAN', bank.iban))
    if bank.intermediary_bank_name:
        ccy = bank.intermediary_currency.code if bank.intermediary_currency else ''
        pairs.extend([
            (f'Intermediary Institution ({ccy})', ''),
            ('  A/C No.',   bank.intermediary_account_number or '—'),
            ('  Bank',      bank.intermediary_bank_name),
            ('  SWIFT',     bank.intermediary_swift_code or '—'),
        ])

    ACCENT = 4
    LABEL_W = CONTENT_W * 0.32
    VALUE_W = CONTENT_W - ACCENT - LABEL_W

    title_row = ['', _p('BENEFICIARY BANK INFORMATION', _NAVY_WHITE), '']
    data_rows = [['', _p(lbl, _LABEL), _p(str(val or '—'), _BODY)] for lbl, val in pairs]
    all_rows = [title_row] + data_rows

    tbl = Table(all_rows, colWidths=[ACCENT, LABEL_W, VALUE_W])
    tbl.setStyle(TableStyle([
        # Blue accent strip
        ('BACKGROUND',    (0, 0), (0, -1), COLOR_BLUE_ACCENT),
        # Title row navy background
        ('BACKGROUND',    (1, 0), (2, 0),  COLOR_NAVY),
        # Data rows light background
        ('BACKGROUND',    (1, 1), (2, -1), COLOR_LIGHT_BG),
        # Outer border only
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0,   COLOR_BORDER),
        # Accent strip: no padding
        ('LEFTPADDING',   (0, 0), (0, -1), 0),
        ('RIGHTPADDING',  (0, 0), (0, -1), 0),
        ('TOPPADDING',    (0, 0), (0, -1), 0),
        ('BOTTOMPADDING', (0, 0), (0, -1), 0),
        # Content padding
        ('LEFTPADDING',   (1, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (1, 0), (-1, -1), 8),
        ('TOPPADDING',    (1, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (1, 0), (-1, -1), 3),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl
