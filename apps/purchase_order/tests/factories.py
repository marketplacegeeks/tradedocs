import factory
from decimal import Decimal

from apps.accounts.tests.factories import MakerFactory, CheckerFactory
from apps.master_data.models import OrganisationAddress, OrganisationTag
from apps.master_data.tests.factories import (
    CurrencyFactory,
    OrganisationFactory,
    OrganisationAddressFactory,
    UOMFactory,
)
from apps.purchase_order.models import PurchaseOrder, PurchaseOrderLineItem, TransactionType


class VendorOrganisationFactory(OrganisationFactory):
    """An organisation tagged as VENDOR with at least one DELIVERY address."""

    @factory.post_generation
    def ensure_vendor_tag(self, create, extracted, **kwargs):
        if not create:
            return
        OrganisationTag.objects.get_or_create(organisation=self, tag=OrganisationTag.Tag.VENDOR)


class DeliveryAddressFactory(OrganisationAddressFactory):
    """An OrganisationAddress with address_type=DELIVERY."""
    address_type = OrganisationAddress.AddressType.DELIVERY


class PurchaseOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseOrder

    po_number = factory.Sequence(lambda n: f"PO-2026-{n + 1:04d}")
    po_date = factory.Faker("date_object")
    vendor = factory.SubFactory(VendorOrganisationFactory)
    internal_contact = factory.SubFactory(MakerFactory)
    delivery_address = factory.LazyAttribute(
        lambda obj: DeliveryAddressFactory(organisation=obj.vendor)
    )
    currency = factory.SubFactory(CurrencyFactory)
    transaction_type = TransactionType.ZERO_RATED
    status = "DRAFT"
    created_by = factory.SubFactory(MakerFactory)


class PurchaseOrderLineItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseOrderLineItem

    purchase_order = factory.SubFactory(PurchaseOrderFactory)
    description = factory.Sequence(lambda n: f"Product {n}")
    item_code = factory.Sequence(lambda n: f"ITEM{n:04d}")
    uom = factory.SubFactory(UOMFactory)
    quantity = Decimal("10.000000")
    unit_price = Decimal("100.00")
    sort_order = factory.Sequence(lambda n: n)
