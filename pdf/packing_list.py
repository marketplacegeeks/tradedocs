"""
Combined Packing List + Commercial Invoice PDF generator (FR-14M.13).

Produces a single in-memory PDF with two sections:
  Section 1 — Packing List / Weight Note  (pages 1+)
  Section 2 — Commercial Invoice          (starts on a new page)

Both sections use the pdf1/ reference layout from their respective story
builders.  A PageBreak separates them inside a single SimpleDocTemplate so
only one pass of doc.build() is needed.

Constraint #20: Returns a BytesIO buffer — never writes to disk.
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, SimpleDocTemplate

from pdf.packing_list_generator import _make_pl_styles, build_pl_story
from pdf.commercial_invoice_generator import _make_ci_styles, build_ci_story


def generate_pl_ci_pdf(pl) -> io.BytesIO:
    """
    Generate a combined Packing List + Commercial Invoice PDF.
    Returns an in-memory BytesIO buffer — constraint #20: never writes to disk.

    Section 1 — Packing List (starts at page 1)
    Section 2 — Commercial Invoice (starts on a new page after the PL)
    """
    try:
        ci = pl.commercial_invoice
    except Exception:
        ci = None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
    )

    def add_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            "This is a computer-generated document. Signature is not required.",
        )
        canvas.restoreState()

    pl_styles = _make_pl_styles()
    story = build_pl_story(pl, pl_styles)

    if ci is not None:
        ci_styles = _make_ci_styles()
        story.append(PageBreak())
        story += build_ci_story(ci, ci_styles)

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer
