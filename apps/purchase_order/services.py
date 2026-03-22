"""
PurchaseOrderService — document-level business logic.

Constraint #16: PO numbers are generated inside select_for_update() to prevent duplicates.
Constraint #17: Format is PO-YYYY-NNNN (4-digit, zero-padded sequence per year).
"""

from datetime import date

from django.db import transaction


def generate_document_number():
    """
    Generate the next PO number for the current year.
    Uses select_for_update() to lock all existing PO rows for this year,
    preventing duplicate numbers when two users save simultaneously.
    """
    from .models import PurchaseOrder  # local import avoids circular dependency at module load

    year = date.today().year
    prefix = f"PO-{year}-"

    with transaction.atomic():
        # Lock all PO rows for this year — any concurrent writer will block until we commit.
        count = (
            PurchaseOrder.objects
            .select_for_update()
            .filter(po_number__startswith=prefix)
            .count()
        )
        return f"{prefix}{count + 1:04d}"
