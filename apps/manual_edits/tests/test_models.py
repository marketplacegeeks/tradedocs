import pytest
from django.db import IntegrityError

from apps.manual_edits.models import DocumentEditTracking
from apps.accounts.tests.factories import MakerFactory

pytestmark = pytest.mark.django_db


def test_creates_tracking_row_with_defaults():
    tracking = DocumentEditTracking.objects.create(
        document_type="proforma_invoice",
        document_id=1,
        document_number="PI-2026-0001",
    )
    assert tracking.first_generated_at is None
    assert tracking.edited_word_file.name in (None, "")
    assert tracking.edited_pdf_file.name in (None, "")
    assert tracking.edit_comment == ""
    assert tracking.edited_by is None
    assert tracking.edited_at is None


def test_document_type_and_id_must_be_unique_together():
    DocumentEditTracking.objects.create(
        document_type="proforma_invoice",
        document_id=1,
        document_number="PI-2026-0001",
    )
    with pytest.raises(IntegrityError):
        DocumentEditTracking.objects.create(
            document_type="proforma_invoice",
            document_id=1,
            document_number="PI-2026-0001",
        )


def test_same_document_id_allowed_across_different_document_types():
    DocumentEditTracking.objects.create(
        document_type="proforma_invoice",
        document_id=1,
        document_number="PI-2026-0001",
    )
    # No collision — document_id=1 for a different document_type is a different document.
    other = DocumentEditTracking.objects.create(
        document_type="packing_list",
        document_id=1,
        document_number="PL-2026-0001",
    )
    assert other.pk is not None


def test_edited_by_is_protected_on_user_delete():
    maker = MakerFactory()
    DocumentEditTracking.objects.create(
        document_type="proforma_invoice",
        document_id=1,
        document_number="PI-2026-0001",
        edited_by=maker,
    )
    from django.db.models import ProtectedError
    with pytest.raises(ProtectedError):
        maker.delete()
