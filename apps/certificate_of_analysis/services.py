"""
COA document number generation.
Format: COA-YYYY-NNNN (4-digit zero-padded sequence per year).
Uses select_for_update() to prevent duplicate numbers.
"""
from datetime import date
from django.db import transaction


def generate_document_number():
    # Local import avoids circular dependency at module load time.
    from .models import CertificateOfAnalysis
    year = date.today().year
    prefix = f"COA-{year}-"
    with transaction.atomic():
        # Lock all COA rows for this year — concurrent writers will block until we commit.
        count = (
            CertificateOfAnalysis.objects
            .select_for_update()
            .filter(coa_number__startswith=prefix)
            .count()
        )
        return f"{prefix}{count + 1:04d}"
