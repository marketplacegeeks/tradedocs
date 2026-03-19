import factory
from datetime import date

from apps.accounts.tests.factories import MakerFactory
from apps.master_data.tests.factories import (
    IncotermFactory,
    LocationFactory,
    OrganisationFactory,
    PaymentTermFactory,
    PortFactory,
    UOMFactory,
)
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.packing_list.models import Container, ContainerItem, PackingList
from apps.workflow.constants import DRAFT


class PackingListFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PackingList

    pl_number = factory.Sequence(lambda n: f"PL-2026-{n + 1:04d}")
    pl_date = factory.LazyFunction(date.today)
    proforma_invoice = factory.SubFactory(ProformaInvoiceFactory)
    exporter = factory.SubFactory(OrganisationFactory)
    consignee = factory.SubFactory(OrganisationFactory)
    buyer = None
    notify_party = None
    status = DRAFT
    created_by = factory.SubFactory(MakerFactory)


class ContainerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Container

    packing_list = factory.SubFactory(PackingListFactory)
    container_ref = factory.Sequence(lambda n: f"CONT{n + 1:03d}")
    marks_numbers = factory.Sequence(lambda n: f"MARK-{n + 1}")
    seal_number = factory.Sequence(lambda n: f"SEAL-{n + 1:04d}")
    # tare_weight must be set explicitly; gross_weight is computed on save.
    tare_weight = factory.Faker(
        "pydecimal", left_digits=4, right_digits=3, positive=True
    )


class ContainerItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContainerItem

    container = factory.SubFactory(ContainerFactory)
    item_code = factory.Sequence(lambda n: f"ITEM-{n + 1:03d}")
    packages_kind = factory.Sequence(lambda n: f"{n + 1} Boxes")
    description = factory.Sequence(lambda n: f"Commodity description {n + 1}")
    batch_details = ""
    uom = factory.SubFactory(UOMFactory)
    quantity = factory.Faker(
        "pydecimal", left_digits=4, right_digits=3, positive=True
    )
    net_weight = factory.Faker(
        "pydecimal", left_digits=4, right_digits=3, positive=True
    )
    inner_packing_weight = factory.Faker(
        "pydecimal", left_digits=2, right_digits=3, positive=True
    )
    # item_gross_weight is computed on save — do not set here
