"""
Model tests for apps.commercial_invoice (FR-14M).
Covers: computed amount, field defaults, __str__, constraint behaviour.
"""
from decimal import Decimal

import pytest

from apps.commercial_invoice.models import CommercialInvoice, CommercialInvoiceLineItem
from apps.workflow.constants import DRAFT

from .factories import CommercialInvoiceFactory, CommercialInvoiceLineItemFactory


@pytest.mark.django_db
class TestCommercialInvoiceModel:
    def test_str_returns_ci_number(self):
        ci = CommercialInvoiceFactory(ci_number="CI-2026-0001")
        assert str(ci) == "CI-2026-0001"

    def test_default_status_is_draft(self):
        ci = CommercialInvoiceFactory()
        assert ci.status == DRAFT

    def test_ordering_is_newest_first(self):
        ci1 = CommercialInvoiceFactory()
        ci2 = CommercialInvoiceFactory()
        cis = list(CommercialInvoice.objects.all())
        assert cis[0].pk == ci2.pk
        assert cis[1].pk == ci1.pk

    def test_ci_number_is_unique(self):
        CommercialInvoiceFactory(ci_number="CI-2026-0001")
        with pytest.raises(Exception):
            CommercialInvoiceFactory(ci_number="CI-2026-0001")

    def test_financial_fields_are_optional(self):
        ci = CommercialInvoiceFactory(fob_rate=None, freight=None, insurance=None)
        assert ci.fob_rate is None
        assert ci.freight is None
        assert ci.insurance is None

    def test_lc_details_defaults_to_empty_string(self):
        ci = CommercialInvoiceFactory(lc_details="")
        assert ci.lc_details == ""

    def test_bank_is_optional(self):
        ci = CommercialInvoiceFactory(bank=None)
        assert ci.bank is None

    def test_one_to_one_with_packing_list(self):
        """Each PackingList can only have one CommercialInvoice."""
        ci = CommercialInvoiceFactory()
        with pytest.raises(Exception):
            CommercialInvoiceFactory(packing_list=ci.packing_list)


@pytest.mark.django_db
class TestCommercialInvoiceLineItemModel:
    def test_amount_computed_on_save(self):
        item = CommercialInvoiceLineItemFactory(
            total_quantity=Decimal("100.000"),
            rate=Decimal("5.50"),
        )
        item.refresh_from_db()
        assert item.amount == Decimal("550.00")

    def test_amount_updates_on_resave(self):
        item = CommercialInvoiceLineItemFactory(
            total_quantity=Decimal("10.000"),
            rate=Decimal("20.00"),
        )
        item.refresh_from_db()
        assert item.amount == Decimal("200.00")

        item.rate = Decimal("25.00")
        item.save()
        item.refresh_from_db()
        assert item.amount == Decimal("250.00")

    def test_str_includes_ci_number_and_item_code(self):
        item = CommercialInvoiceLineItemFactory(item_code="PROD-X")
        assert "PROD-X" in str(item)
        assert item.ci.ci_number in str(item)

    def test_hsn_code_is_optional(self):
        item = CommercialInvoiceLineItemFactory(hsn_code="")
        assert item.hsn_code == ""

    def test_packages_kind_is_optional(self):
        item = CommercialInvoiceLineItemFactory(packages_kind="")
        assert item.packages_kind == ""
