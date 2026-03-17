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
