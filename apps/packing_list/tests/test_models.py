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
        """A freshly created container with no items should have gross_weight == tare_weight."""
        container = ContainerFactory(tare_weight=Decimal("2200.000"))
        container.refresh_from_db()
        assert container.gross_weight == Decimal("2200.000")

    def test_gross_weight_recalculated_after_item_added(self):
        """
        Adding an item must trigger Container.save(), which adds item_gross_weight to tare.
        item_gross_weight = net_material_weight + (no_of_packages × weight_per_unit_packaging)
                          = (5 × 100) + (5 × 10) = 500 + 50 = 550
        container gross = 550 + 2000 = 2550
        """
        container = ContainerFactory(tare_weight=Decimal("2000.000"))
        ContainerItemFactory(
            container=container,
            no_of_packages=Decimal("5.000"),
            qty_per_package=Decimal("100.000"),
            weight_per_unit_packaging=Decimal("10.000"),
        )
        container.refresh_from_db()
        assert container.gross_weight == Decimal("2550.000")

    def test_gross_weight_sums_multiple_items(self):
        """
        item1: net_material = 3×50 = 150; gross = 150 + 3×5 = 165
        item2: net_material = 2×80 = 160; gross = 160 + 2×8 = 176
        container gross = 1500 + 165 + 176 = 1841
        """
        container = ContainerFactory(tare_weight=Decimal("1500.000"))
        ContainerItemFactory(
            container=container,
            no_of_packages=Decimal("3.000"),
            qty_per_package=Decimal("50.000"),
            weight_per_unit_packaging=Decimal("5.000"),
        )
        ContainerItemFactory(
            container=container,
            no_of_packages=Decimal("2.000"),
            qty_per_package=Decimal("80.000"),
            weight_per_unit_packaging=Decimal("8.000"),
        )
        container.refresh_from_db()
        assert container.gross_weight == Decimal("1841.000")


@pytest.mark.django_db
class TestContainerItemModel:
    def test_net_material_weight_computed(self):
        """net_material_weight = no_of_packages × qty_per_package"""
        item = ContainerItemFactory(
            no_of_packages=Decimal("10.000"),
            qty_per_package=Decimal("25.000"),
            weight_per_unit_packaging=Decimal("2.000"),
        )
        item.refresh_from_db()
        assert item.net_material_weight == Decimal("250.000")

    def test_item_gross_weight_computed(self):
        """item_gross_weight = net_material_weight + (no_of_packages × weight_per_unit_packaging)"""
        item = ContainerItemFactory(
            no_of_packages=Decimal("10.000"),
            qty_per_package=Decimal("25.000"),
            weight_per_unit_packaging=Decimal("2.000"),
        )
        item.refresh_from_db()
        # net_material = 10 × 25 = 250; pkg_weight = 10 × 2 = 20; gross = 270
        assert item.item_gross_weight == Decimal("270.000")

    def test_computed_fields_update_on_resave(self):
        item = ContainerItemFactory(
            no_of_packages=Decimal("5.000"),
            qty_per_package=Decimal("100.000"),
            weight_per_unit_packaging=Decimal("10.000"),
        )
        item.refresh_from_db()
        # net_material = 500; gross = 500 + 50 = 550
        assert item.net_material_weight == Decimal("500.000")
        assert item.item_gross_weight == Decimal("550.000")

        item.no_of_packages = Decimal("10.000")
        item.save()
        item.refresh_from_db()
        # net_material = 1000; gross = 1000 + 100 = 1100
        assert item.net_material_weight == Decimal("1000.000")
        assert item.item_gross_weight == Decimal("1100.000")

    def test_str_includes_item_code_and_container(self):
        item = ContainerItemFactory(item_code="ITEM-001")
        assert "ITEM-001" in str(item)

    def test_batch_details_is_optional(self):
        item = ContainerItemFactory(batch_details="")
        assert item.batch_details == ""

    def test_hsn_code_is_optional(self):
        item = ContainerItemFactory(hsn_code="")
        assert item.hsn_code == ""
