"""
Model-level tests for ProformaInvoice, ProformaInvoiceLineItem, ProformaInvoiceCharge.
"""

import pytest
from decimal import Decimal

from apps.proforma_invoice.models import ProformaInvoice, ProformaInvoiceLineItem
from apps.proforma_invoice.services import generate_document_number
from apps.workflow.constants import DRAFT

from .factories import (
    ProformaInvoiceChargeFactory,
    ProformaInvoiceFactory,
    ProformaInvoiceLineItemFactory,
)


@pytest.mark.django_db
class TestProformaInvoiceModel:

    def test_default_status_is_draft(self):
        pi = ProformaInvoiceFactory()
        assert pi.status == DRAFT

    def test_pi_number_is_unique(self):
        pi1 = ProformaInvoiceFactory()
        with pytest.raises(Exception):
            # Creating a second PI with the same pi_number should fail at DB level
            ProformaInvoiceFactory(pi_number=pi1.pi_number)

    def test_str_returns_pi_number(self):
        pi = ProformaInvoiceFactory(pi_number="PI-2026-0001")
        assert str(pi) == "PI-2026-0001"


@pytest.mark.django_db
class TestProformaInvoiceLineItemModel:

    def test_amount_usd_is_computed_on_save(self):
        item = ProformaInvoiceLineItemFactory(
            quantity=Decimal("10.000"),
            rate_usd=Decimal("50.00"),
        )
        assert item.amount_usd == Decimal("500.00")

    def test_amount_updates_when_saved_again(self):
        item = ProformaInvoiceLineItemFactory(
            quantity=Decimal("2.000"),
            rate_usd=Decimal("100.00"),
        )
        item.quantity = Decimal("3.000")
        item.save()
        item.refresh_from_db()
        assert item.amount_usd == Decimal("300.00")

    def test_hsn_regex_valid(self):
        # 2, 4, 6, 8 digits are valid
        item = ProformaInvoiceLineItemFactory(hsn_code="090111")
        assert item.hsn_code == "090111"

    def test_str(self):
        pi = ProformaInvoiceFactory(pi_number="PI-2026-0001")
        item = ProformaInvoiceLineItemFactory(pi=pi, description="Soybean Oil")
        assert "PI-2026-0001" in str(item)


@pytest.mark.django_db
class TestGenerateDocumentNumber:

    def test_first_number_for_year(self, monkeypatch):
        """First PI of the year should be PI-YYYY-0001."""
        # Ensure no PIs exist for 2026
        assert ProformaInvoice.objects.filter(pi_number__startswith="PI-2026-").count() == 0
        number = generate_document_number()
        assert number.startswith("PI-")
        parts = number.split("-")
        assert len(parts) == 3
        assert int(parts[2]) == 1

    def test_sequential_numbers(self):
        """Second PI number should be one greater than the first."""
        num1 = generate_document_number()
        ProformaInvoiceFactory(pi_number=num1)
        num2 = generate_document_number()
        seq1 = int(num1.split("-")[2])
        seq2 = int(num2.split("-")[2])
        assert seq2 == seq1 + 1

    def test_zero_padded_four_digits(self):
        number = generate_document_number()
        seq_part = number.split("-")[2]
        assert len(seq_part) == 4
        assert seq_part.isdigit()
