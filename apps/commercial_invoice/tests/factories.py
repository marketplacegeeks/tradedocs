import factory
from datetime import date

from apps.accounts.tests.factories import MakerFactory
from apps.master_data.tests.factories import BankFactory, UOMFactory
from apps.packing_list.tests.factories import PackingListFactory
from apps.commercial_invoice.models import CommercialInvoice, CommercialInvoiceLineItem
from apps.workflow.constants import DRAFT


class CommercialInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommercialInvoice

    ci_number = factory.Sequence(lambda n: f"CI-2026-{n + 1:04d}")
    ci_date = factory.LazyFunction(date.today)
    packing_list = factory.SubFactory(PackingListFactory)
    bank = factory.SubFactory(BankFactory)
    fob_rate = None
    freight = None
    insurance = None
    lc_details = ""
    status = DRAFT
    created_by = factory.SubFactory(MakerFactory)


class CommercialInvoiceLineItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommercialInvoiceLineItem

    ci = factory.SubFactory(CommercialInvoiceFactory)
    item_code = factory.Sequence(lambda n: f"ITEM-{n + 1:03d}")
    description = factory.Sequence(lambda n: f"Line item description {n + 1}")
    hsn_code = ""
    packages_kind = factory.Sequence(lambda n: f"{n + 1} Boxes")
    uom = factory.SubFactory(UOMFactory)
    total_quantity = factory.Faker(
        "pydecimal", left_digits=4, right_digits=3, positive=True
    )
    rate = factory.Faker(
        "pydecimal", left_digits=5, right_digits=2, positive=True
    )
    # amount is computed on save — do not set here
