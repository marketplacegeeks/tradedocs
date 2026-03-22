"""
Shared utility functions for TradeDocs PDF generators.

format_decimal  — safe Decimal → formatted string
currency_to_words — Decimal amount → English words
strip_html       — strip Tiptap/rich-text HTML to plain text for canvas rendering
safe_str         — coerce None/empty to '—'
"""
import re
from decimal import Decimal


def safe_str(value, fallback='—'):
    """Return str(value) or fallback if value is None/empty."""
    s = str(value).strip() if value is not None else ''
    return s if s else fallback


def format_decimal(value, dp=2, prefix=''):
    """Format a Decimal (or None) with thousands separator."""
    if value is None:
        return f'{prefix}0.{"0" * dp}'
    fmt = f'{{:,.{dp}f}}'
    return f'{prefix}{fmt.format(value)}'


def strip_html(html_content):
    """
    Convert Tiptap/rich-text HTML to plain text suitable for a ReportLab Paragraph.
    Preserves paragraph breaks as double newlines, removes all tags.
    """
    if not html_content:
        return ''
    # Replace block-level closers with newlines before stripping tags
    text = re.sub(r'</p>|</li>|<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    entities = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&nbsp;': ' ',
                '&#39;': "'", '&quot;': '"'}
    for ent, char in entities.items():
        text = text.replace(ent, char)
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def html_to_rl_flowables(html_content, style, spacer_pt=3):
    """
    Convert Tiptap/rich-text HTML to a list of ReportLab Paragraph + Spacer flowables,
    preserving bold, italic, underline, bullet lists, ordered lists, and line breaks.

    Use this instead of strip_html() wherever T&C or other rich-text content is rendered.
    Returns a flat list ready to extend() into a story.
    """
    from html.parser import HTMLParser
    from reportlab.platypus import Paragraph, Spacer

    class _Parser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self._items = []       # completed text strings, each becomes one Paragraph
            self._buf = []         # current inline markup buffer
            self._list_types = []  # stack: 'ul' or 'ol'
            self._ol_counts = []   # parallel stack of counters for ordered lists
            self._in_li = False    # whether we're currently inside a <li>

        def handle_starttag(self, tag, attrs):
            t = tag.lower()
            if t in ('ul', 'ol'):
                self._flush()
                self._list_types.append(t)
                self._ol_counts.append(0)
            elif t == 'li':
                self._flush()
                self._in_li = True
                if self._list_types and self._list_types[-1] == 'ol':
                    self._ol_counts[-1] += 1
            elif t in ('strong', 'b'):
                self._buf.append('<b>')
            elif t in ('em', 'i'):
                self._buf.append('<i>')
            elif t == 'u':
                self._buf.append('<u>')
            elif t == 'br':
                self._buf.append('<br/>')
            elif t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                self._flush()
                self._buf.append('<b>')
            # <p> and <a> need no special start handling

        def handle_endtag(self, tag):
            t = tag.lower()
            if t == 'p':
                # Inside a <li> the <p> close does not emit a new paragraph —
                # that happens at </li> so indentation prefix can be prepended.
                if not self._in_li:
                    self._flush()
            elif t in ('ul', 'ol'):
                self._flush()
                if self._list_types:
                    self._list_types.pop()
                    self._ol_counts.pop()
            elif t == 'li':
                # Prepend the appropriate bullet / number prefix
                if self._list_types:
                    if self._list_types[-1] == 'ol':
                        prefix = f'{self._ol_counts[-1]}. '
                    else:
                        prefix = '\u2022  '  # bullet + two spaces for readability
                else:
                    prefix = '\u2022  '
                self._flush(prefix=prefix)
                self._in_li = False
            elif t in ('strong', 'b'):
                self._buf.append('</b>')
            elif t in ('em', 'i'):
                self._buf.append('</i>')
            elif t == 'u':
                self._buf.append('</u>')
            elif t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                self._buf.append('</b>')
                self._flush()

        def handle_data(self, data):
            # convert_charrefs=True means all HTML entities already decoded to Unicode.
            # Re-escape for ReportLab's XML parser; replace non-breaking space with plain space.
            data = data.replace('\xa0', ' ')
            data = data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            self._buf.append(data)

        def _flush(self, prefix=''):
            text = ''.join(self._buf).strip()
            self._buf = []
            if text:
                self._items.append(prefix + text)

        def result(self):
            self._flush()
            return self._items

    parser = _Parser()
    parser.feed(html_content or '')

    flowables = []
    for text in parser.result():
        flowables.append(Paragraph(text, style))
        flowables.append(Spacer(1, spacer_pt))
    return flowables


def currency_to_words(amount):
    """Convert a Decimal USD amount to English words (e.g. 'One Hundred Dollars Only')."""
    try:
        cents = int(Decimal(str(amount)) * 100)
    except (TypeError, ValueError, Exception):
        return 'Zero Dollars Only'

    dollars = cents // 100
    if dollars == 0:
        return 'Zero Dollars Only'

    def _ones(n):
        w = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
             'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
             'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        return w[n] if n < 20 else ''

    def _tens(n):
        w = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
             'Sixty', 'Seventy', 'Eighty', 'Ninety']
        return _ones(n) if n < 20 else (w[n // 10] + (' ' + _ones(n % 10) if n % 10 else '')).strip()

    def _hundreds(n):
        if n < 100:
            return _tens(n)
        h, r = divmod(n, 100)
        return (_ones(h) + ' Hundred' + (' ' + _tens(r) if r else '')).strip()

    parts = []
    for value, label in [
        (dollars // 1_000_000_000, 'Billion'),
        ((dollars % 1_000_000_000) // 1_000_000, 'Million'),
        ((dollars % 1_000_000) // 1_000, 'Thousand'),
        (dollars % 1_000, ''),
    ]:
        if value:
            chunk = _hundreds(value)
            parts.append(f'{chunk} {label}'.strip() if label else chunk)

    return ' '.join(parts) + ' Dollars Only'
