"""
ProformaInvoiceService — document-level business logic.

Constraint #16: PI numbers are generated inside select_for_update() to prevent duplicates.
Constraint #17: Format is PI-YYYY-NNNN (4-digit, zero-padded sequence per year).
"""

from datetime import date

from django.db import transaction


def generate_document_number():
    """
    Generate the next PI number for the current year using a row-level lock.

    IMPORTANT: This function must be called from within an outer
    transaction.atomic() block that also performs the INSERT. The
    SELECT FOR UPDATE lock is only held until the surrounding transaction
    commits — if this runs in its own atomic() (which becomes a savepoint
    when nested), the lock releases before the INSERT and two concurrent
    requests can generate the same number.

    Constraint #16: PI numbers use select_for_update() to prevent duplicates.
    Constraint #17: Format is PI-YYYY-NNNN (4-digit, zero-padded per year).

    Implementation note: select_for_update() is combined with values_list()
    (not count()) because Django silently drops the FOR UPDATE clause when
    using aggregate functions like COUNT(*). values_list() fetches the actual
    locked rows; len() on that result gives the correct count.
    """
    from .models import ProformaInvoice  # local import avoids circular dependency at module load

    year = date.today().year
    prefix = f"PI-{year}-"

    # Fetch AND lock all PI rows for this year.
    # values_list() preserves the FOR UPDATE clause (unlike .count() which
    # wraps in SELECT COUNT(*) and silently drops FOR UPDATE).
    # The second concurrent writer blocks here until the first commits.
    # This function must be called inside transaction.atomic() in the caller.
    existing = list(
        ProformaInvoice.objects
        .select_for_update()
        .filter(pi_number__startswith=prefix)
        .values_list("pi_number", flat=True)
    )
    return f"{prefix}{len(existing) + 1:04d}"
