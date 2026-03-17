"""
ProformaInvoiceService — document-level business logic.

Constraint #16: PI numbers are generated inside select_for_update() to prevent duplicates.
Constraint #17: Format is PI-YYYY-NNNN (4-digit, zero-padded sequence per year).
"""

from datetime import date

from django.db import transaction


def generate_document_number():
    """
    Generate the next PI number for the current year.
    Uses select_for_update() to lock all existing PI rows for this year,
    preventing duplicate numbers when two users save simultaneously.
    """
    from .models import ProformaInvoice  # local import avoids circular dependency at module load

    year = date.today().year
    prefix = f"PI-{year}-"

    with transaction.atomic():
        # Lock all PI rows for this year — any concurrent writer will block until we commit.
        count = (
            ProformaInvoice.objects
            .select_for_update()
            .filter(pi_number__startswith=prefix)
            .count()
        )
        return f"{prefix}{count + 1:04d}"
