import factory
from datetime import date

from apps.accounts.tests.factories import MakerFactory
from apps.master_data.tests.factories import (
    BankFactory, IncotermFactory, LocationFactory, OrganisationFactory,
    PaymentTermFactory, PortFactory, UOMFactory,
)
from apps.proforma_invoice.models import (
    ProformaInvoice, ProformaInvoiceCharge, ProformaInvoiceLineItem,
)
from apps.workflow.constants import DRAFT


class ProformaInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoice

    pi_number = factory.Sequence(lambda n: f"PI-2026-{n + 1:04d}")
    pi_date = factory.LazyFunction(date.today)
    exporter = factory.SubFactory(OrganisationFactory)
    consignee = factory.SubFactory(OrganisationFactory)
    buyer = None
    payment_terms = factory.SubFactory(PaymentTermFactory)
    incoterms = factory.SubFactory(IncotermFactory)
    status = DRAFT
    created_by = factory.SubFactory(MakerFactory)


class ProformaInvoiceLineItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoiceLineItem

    pi = factory.SubFactory(ProformaInvoiceFactory)
    description = factory.Sequence(lambda n: f"Item description {n}")
    quantity = factory.Faker("pydecimal", left_digits=4, right_digits=3, positive=True)
    uom = factory.SubFactory(UOMFactory)
    rate_usd = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    # amount_usd is computed on save — do not set here


class ProformaInvoiceChargeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoiceCharge

    pi = factory.SubFactory(ProformaInvoiceFactory)
    description = factory.Sequence(lambda n: f"Charge {n}")
    amount_usd = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
