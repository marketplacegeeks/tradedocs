"""
Unit tests for PurchaseOrder and PurchaseOrderLineItem models (FR-PO-12).
"""

from decimal import Decimal

import pytest

from apps.purchase_order.models import TransactionType
from .factories import PurchaseOrderFactory, PurchaseOrderLineItemFactory


@pytest.mark.django_db
class TestPurchaseOrderModel:
    def test_po_number_is_set(self):
        """po_number is set when the PO is created via factory."""
        po = PurchaseOrderFactory()
        assert po.po_number.startswith("PO-")

    def test_str_returns_po_number(self):
        po = PurchaseOrderFactory()
        assert str(po) == po.po_number


@pytest.mark.django_db
class TestPurchaseOrderLineItemSave:
    def test_zero_rated_computes_correctly(self):
        """ZERO_RATED: taxable_amount = qty × price; total_tax = 0; total = taxable_amount."""
        po = PurchaseOrderFactory(transaction_type=TransactionType.ZERO_RATED)
        item = PurchaseOrderLineItemFactory(
            purchase_order=po,
            quantity=Decimal("5.000000"),
            unit_price=Decimal("200.00"),
        )
        assert item.taxable_amount == Decimal("1000.00")
        assert item.total_tax == Decimal("0")
        assert item.total == Decimal("1000.00")
        assert item.igst_amount is None
        assert item.cgst_amount is None
        assert item.sgst_amount is None

    def test_igst_computes_correctly(self):
        """IGST: igst_amount = taxable × rate / 100; total = taxable + igst_amount."""
        po = PurchaseOrderFactory(transaction_type=TransactionType.IGST)
        item = PurchaseOrderLineItemFactory(
            purchase_order=po,
            quantity=Decimal("10.000000"),
            unit_price=Decimal("100.00"),
            igst_percent=Decimal("18.00"),
        )
        assert item.taxable_amount == Decimal("1000.00")
        assert item.igst_amount == Decimal("180.00")
        assert item.total_tax == Decimal("180.00")
        assert item.total == Decimal("1180.00")
        # CGST/SGST must be cleared
        assert item.cgst_percent is None
        assert item.sgst_percent is None

    def test_cgst_sgst_computes_correctly(self):
        """CGST_SGST: cgst_amount + sgst_amount; total_tax = sum of both."""
        po = PurchaseOrderFactory(transaction_type=TransactionType.CGST_SGST)
        item = PurchaseOrderLineItemFactory(
            purchase_order=po,
            quantity=Decimal("10.000000"),
            unit_price=Decimal("100.00"),
            cgst_percent=Decimal("9.00"),
            sgst_percent=Decimal("9.00"),
        )
        assert item.taxable_amount == Decimal("1000.00")
        assert item.cgst_amount == Decimal("90.00")
        assert item.sgst_amount == Decimal("90.00")
        assert item.total_tax == Decimal("180.00")
        assert item.total == Decimal("1180.00")
        # IGST must be cleared
        assert item.igst_percent is None
        assert item.igst_amount is None
