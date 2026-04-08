"""
Model tests for apps.packing_list (FR-14M).
Covers: computed fields, field defaults, __str__, constraint behaviour.
"""
from decimal import Decimal

import pytest

from apps.packing_list.models import Container, ContainerItem, PackingList
from apps.workflow.constants import DRAFT

from .factories import ContainerFactory, ContainerItemFactory, PackingListFactory


@pytest.mark.django_db
class TestPackingListModel:
    def test_str_returns_pl_number(self):
        pl = PackingListFactory(pl_number="PL-2026-0001")
        assert str(pl) == "PL-2026-0001"

    def test_default_status_is_draft(self):
        pl = PackingListFactory()
        assert pl.status == DRAFT

    def test_ordering_is_newest_first(self):
        pl1 = PackingListFactory()
        pl2 = PackingListFactory()
        pls = list(PackingList.objects.all())
        # Most recently created should appear first.
        assert pls[0].pk == pl2.pk
        assert pls[1].pk == pl1.pk

    def test_pl_number_is_unique(self):
        PackingListFactory(pl_number="PL-2026-0001")
        with pytest.raises(Exception):
            PackingListFactory(pl_number="PL-2026-0001")

    def test_buyer_and_notify_party_are_optional(self):
        pl = PackingListFactory(buyer=None, notify_party=None)
        assert pl.buyer is None
        assert pl.notify_party is None


@pytest.mark.django_db
class TestContainerModel:
    def test_str_includes_pl_number_and_container_ref(self):
        container = ContainerFactory(container_ref="CONT001")
        assert container.packing_list.pl_number in str(container)
        assert "CONT001" in str(container)

    def test_gross_weight_equals_tare_when_no_items(self):
        """
        A freshly created container with no items should have gross_weight == tare_weight.
        """
        container = ContainerFactory(tare_weight=Decimal("2200.000"))
        container.refresh_from_db()
        assert container.gross_weight == Decimal("2200.000")

    def test_gross_weight_recalculated_after_item_added(self):
        """
        Adding an item must trigger Container.save(), which adds item_gross_weight to tare.
        """
        container = ContainerFactory(tare_weight=Decimal("2000.000"))
        ContainerItemFactory(
            container=container,
            net_weight=Decimal("100.000"),
            inner_packing_weight=Decimal("10.000"),
            quantity=Decimal("2.000"),
        )
        container.refresh_from_db()
        # item_gross_weight = (100.000 + 10.000) * 2 = 220.000
        # container gross = 220.000 + 2000.000 = 2220.000
        assert container.gross_weight == Decimal("2220.000")

    def test_gross_weight_sums_multiple_items(self):
        container = ContainerFactory(tare_weight=Decimal("1500.000"))
        ContainerItemFactory(
            container=container,
            net_weight=Decimal("50.000"),
            inner_packing_weight=Decimal("5.000"),
            quantity=Decimal("2.000"),
        )
        ContainerItemFactory(
            container=container,
            net_weight=Decimal("80.000"),
            inner_packing_weight=Decimal("8.000"),
            quantity=Decimal("3.000"),
        )
        container.refresh_from_db()
        # item1 gross: (50+5)*2 = 110.000; item2 gross: (80+8)*3 = 264.000
        # container gross = 1500 + 110 + 264 = 1874.000
        assert container.gross_weight == Decimal("1874.000")


@pytest.mark.django_db
class TestContainerItemModel:
    def test_item_gross_weight_is_net_plus_inner_packing(self):
        item = ContainerItemFactory(
            net_weight=Decimal("200.000"),
            inner_packing_weight=Decimal("20.500"),
            quantity=Decimal("2.000"),
        )
        item.refresh_from_db()
        # item_gross_weight = (200.000 + 20.500) * 2 = 441.000
        assert item.item_gross_weight == Decimal("441.000")

    def test_item_gross_weight_updates_on_resave(self):
        item = ContainerItemFactory(
            net_weight=Decimal("100.000"),
            inner_packing_weight=Decimal("10.000"),
            quantity=Decimal("2.000"),
        )
        item.refresh_from_db()
        # (100 + 10) * 2 = 220.000
        assert item.item_gross_weight == Decimal("220.000")

        item.net_weight = Decimal("150.000")
        item.save()
        item.refresh_from_db()
        # (150 + 10) * 2 = 320.000
        assert item.item_gross_weight == Decimal("320.000")

    def test_str_includes_item_code_and_container(self):
        item = ContainerItemFactory(item_code="ITEM-001")
        assert "ITEM-001" in str(item)

    def test_batch_details_is_optional(self):
        item = ContainerItemFactory(batch_details="")
        assert item.batch_details == ""

    def test_hsn_code_is_optional(self):
        item = ContainerItemFactory(hsn_code="")
        assert item.hsn_code == ""
