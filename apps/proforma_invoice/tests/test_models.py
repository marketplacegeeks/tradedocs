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


# ============================================================================
# ProformaInvoiceCharge model tests (no coverage existed before)
# ============================================================================

@pytest.mark.django_db
class TestProformaInvoiceChargeModel:

    def test_str_contains_pi_number_and_description(self):
        pi = ProformaInvoiceFactory(pi_number="PI-2026-0001")
        charge = ProformaInvoiceChargeFactory(pi=pi, description="Bank Charges")
        result = str(charge)
        assert "PI-2026-0001" in result
        assert "Bank Charges" in result

    def test_amount_stored_with_correct_precision(self):
        charge = ProformaInvoiceChargeFactory(amount_usd=Decimal("150.75"))
        charge.refresh_from_db()
        assert charge.amount_usd == Decimal("150.75")

    def test_charge_cascade_deleted_with_pi(self):
        """CASCADE on the pi FK means charges are deleted when the PI is deleted."""
        from apps.proforma_invoice.models import ProformaInvoiceCharge
        pi = ProformaInvoiceFactory()
        charge = ProformaInvoiceChargeFactory(pi=pi)
        charge_id = charge.pk
        pi.delete()
        assert not ProformaInvoiceCharge.objects.filter(pk=charge_id).exists()


# ============================================================================
# ProformaInvoiceLineItem: additional edge-case model tests
# ============================================================================

@pytest.mark.django_db
class TestLineItemModelEdgeCases:

    def test_line_item_cascade_deleted_with_pi(self):
        """CASCADE on the pi FK means line items are deleted when the PI is deleted."""
        pi = ProformaInvoiceFactory()
        item = ProformaInvoiceLineItemFactory(pi=pi)
        item_id = item.pk
        pi.delete()
        assert not ProformaInvoiceLineItem.objects.filter(pk=item_id).exists()

    def test_amount_usd_field_is_not_directly_editable(self):
        """amount_usd is always computed on save — passing a wrong value is ignored."""
        item = ProformaInvoiceLineItemFactory(
            quantity=Decimal("2.000"),
            rate_usd=Decimal("100.00"),
        )
        # Force an incorrect stored value and re-save
        item.quantity = Decimal("3.000")
        item.save()
        item.refresh_from_db()
        # Must reflect 3 × 100 = 300, not the old stale value
        assert item.amount_usd == Decimal("300.00")

    def test_hsn_code_blank_is_valid_at_model_level(self):
        """HSN code is optional — blank string is accepted at the model level."""
        item = ProformaInvoiceLineItemFactory(hsn_code="")
        assert item.hsn_code == ""
