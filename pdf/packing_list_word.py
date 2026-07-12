"""
Combined Packing List + Commercial Invoice Word (.docx) generator — the Word
equivalent of pdf/packing_list.py::generate_pl_ci_pdf().

Produces a single in-memory .docx with two sections separated by a hard page
break:
  Section 1 — Commercial Invoice (or CIF-adjusted Client Invoice)
  Section 2 — Packing List / Weight Note

IMPORTANT: matching the real PDF generators, there is NO repeating per-page
header with the company name/title — each section prints its own one-time
title block (company name + document title) via add_title_block(), called
from within build_ci_word_section()/build_cif_ci_word_section() for section 1
and build_pl_word_section() for section 2. Only the footer + DRAFT watermark
repeat on every page (python-docx doesn't support restarting page numbering
mid-document the way the PDF's dual page-counters do, so continuous page
numbering across both sections is an accepted simplification here).

Constraint #9: Returns a BytesIO buffer — never writes to disk.
"""
import io

from docx import Document

from pdf.docx_base import add_page_footer, add_watermark, setup_page


def generate_pl_ci_docx(pl, client_invoice=False) -> io.BytesIO:
    """
    Generate a combined Commercial Invoice + Packing List Word document.
    Returns an in-memory BytesIO buffer — constraint #9: never writes to disk.

    Section 1 — Commercial Invoice (own one-time title block)
    Section 2 — Packing List (own one-time title block, starts on a new page
    after the CI via a hard page break)

    When client_invoice=True, CI line item rates are CIF-adjusted using the
    linked Proforma Invoice's freight and insurance_amount values (mirrors
    generate_pl_ci_pdf's client_invoice behaviour).
    """
    from apps.workflow.constants import APPROVED

    try:
        ci = pl.commercial_invoice
    except Exception:
        ci = None

    pi = getattr(pl, "proforma_invoice", None)

    document = Document()
    setup_page(document)
    section = document.sections[0]

    is_draft = getattr(pl, "status", None) != APPROVED

    add_page_footer(section, with_total=True)
    if is_draft:
        add_watermark(document, "DRAFT")

    # ---- Section 1: Commercial Invoice (or CIF Client Invoice) -------------
    # Mirrors pdf/packing_list.py: only ImportError is swallowed (module not
    # available yet); real bugs in the section builder must surface, not be
    # hidden behind a blank CI section.
    has_ci_content = False
    if ci is not None:
        try:
            if client_invoice:
                from pdf.cif_client_invoice_word_generator import build_cif_ci_word_section
                build_cif_ci_word_section(document, ci)
            else:
                from pdf.commercial_invoice_word_generator import build_ci_word_section
                build_ci_word_section(document, ci, client_invoice=client_invoice, pi=pi)
            has_ci_content = True
        except ImportError:
            has_ci_content = False

    # ---- Page break between CI and PL --------------------------------------
    if has_ci_content:
        document.add_page_break()

    # ---- Section 2: Packing List -------------------------------------------
    try:
        from pdf.packing_list_word_generator import build_pl_word_section
        build_pl_word_section(document, pl)
    except ImportError:
        from pdf.docx_base import add_title_block
        add_title_block(document, "", ["Packing List"])
        document.add_paragraph("Packing list content would appear here.")

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer
