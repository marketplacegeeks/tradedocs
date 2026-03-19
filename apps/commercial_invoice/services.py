"""
CommercialInvoice service — document-level business logic.

Constraint #16: CI numbers are generated inside select_for_update() to prevent duplicates.
Constraint #17: Format is CI-YYYY-NNNN (4-digit, zero-padded sequence per year).
"""

from datetime import date

from django.db import transaction


def generate_document_number():
    """
    Generate the next CI number for the current year.
    Uses select_for_update() to lock all existing CI rows for this year,
    preventing duplicate numbers when two users save simultaneously.
    """
    from .models import CommercialInvoice  # local import avoids circular dependency at module load

    year = date.today().year
    prefix = f"CI-{year}-"

    with transaction.atomic():
        # Lock all CI rows for this year — any concurrent writer will block until we commit.
        count = (
            CommercialInvoice.objects
            .select_for_update()
            .filter(ci_number__startswith=prefix)
            .count()
        )
        return f"{prefix}{count + 1:04d}"
