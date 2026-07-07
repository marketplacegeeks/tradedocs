"""
Tests for PDF helper: deriving a packing list's single weight-label unit.

Weight figures on the PL / CI / client-invoice PDFs are expressed in the
Material Unit the maker selected (not always KGS). These tests cover the helper
that decides which unit label to print.
"""
import pytest

from apps.master_data.tests.factories import UOMFactory
from pdf.utils import weight_unit_for_packing_list
from .factories import ContainerFactory, ContainerItemFactory, PackingListFactory


@pytest.mark.django_db
class TestWeightUnitForPackingList:

    def test_returns_the_shared_unit(self):
        """When every item uses MT, the weight label unit is MT."""
        pl = PackingListFactory()
        container = ContainerFactory(packing_list=pl)
        mt = UOMFactory(abbreviation="MT", name="Metric Tonne")
        ContainerItemFactory(container=container, uom=mt)
        ContainerItemFactory(container=container, uom=mt)
        assert weight_unit_for_packing_list(pl) == "MT"

    def test_falls_back_to_kgs_when_no_items(self):
        """A packing list with no items falls back to KGS."""
        pl = PackingListFactory()
        assert weight_unit_for_packing_list(pl) == "KGS"

    def test_falls_back_to_kgs_for_legacy_mixed_units(self):
        """
        Legacy data may pre-date the single-unit rule. If items disagree, fall
        back to KGS rather than mislabelling the total with one wrong unit.
        """
        pl = PackingListFactory()
        container = ContainerFactory(packing_list=pl)
        # Built via the factory (ORM) to bypass the API's single-unit validation.
        ContainerItemFactory(container=container, uom=UOMFactory(abbreviation="MT"))
        ContainerItemFactory(container=container, uom=UOMFactory(abbreviation="KG"))
        assert weight_unit_for_packing_list(pl) == "KGS"
