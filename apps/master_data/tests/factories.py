import factory
from apps.master_data.models import (
    Bank, Country, Currency, Incoterm, Location, Organisation, OrganisationAddress,
    OrganisationTag, OrganisationTaxCode, Port, PaymentTerm, PreCarriageBy, UOM,
)


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country

    name = factory.Sequence(lambda n: f"Country {n}")
    # Use letter-pairs so codes are always exactly 2 or 3 chars and never collide.
    # n=0 → "AA", n=1 → "AB", ..., n=25 → "AZ", n=26 → "BA", etc.
    iso2 = factory.Sequence(lambda n: chr(65 + (n // 26) % 26) + chr(65 + n % 26))
    iso3 = factory.Sequence(lambda n: chr(65 + (n // 676) % 26) + chr(65 + (n // 26) % 26) + chr(65 + n % 26))


class PortFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Port

    name = factory.Sequence(lambda n: f"Port {n}")
    code = factory.Sequence(lambda n: f"PC{n:03d}"[:10])
    country = factory.SubFactory(CountryFactory)


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Location {n}")
    country = factory.SubFactory(CountryFactory)


class IncotermFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Incoterm

    code = factory.Sequence(lambda n: f"IC{n}")
    full_name = factory.Sequence(lambda n: f"Incoterm Full Name {n}")
    description = ""


class UOMFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UOM

    name = factory.Sequence(lambda n: f"Unit {n}")
    abbreviation = factory.Sequence(lambda n: f"U{n}")


class PaymentTermFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentTerm

    name = factory.Sequence(lambda n: f"Payment Term {n}")
    description = ""


class PreCarriageByFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PreCarriageBy

    name = factory.Sequence(lambda n: f"Carrier {n}")


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = factory.Sequence(lambda n: f"Organisation {n}")
    iec_code = None
    is_active = True


class OrganisationAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationAddress

    organisation = factory.SubFactory(OrganisationFactory)
    address_type = OrganisationAddress.AddressType.REGISTERED
    line1 = factory.Sequence(lambda n: f"{n} Test Street")
    city = "Mumbai"
    country = factory.SubFactory(CountryFactory)
    email = factory.Sequence(lambda n: f"contact{n}@example.com")
    contact_name = factory.Sequence(lambda n: f"Contact Person {n}")
    phone_country_code = ""
    phone_number = ""


class OrganisationTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationTag

    organisation = factory.SubFactory(OrganisationFactory)
    tag = OrganisationTag.Tag.EXPORTER


class OrganisationTaxCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationTaxCode

    organisation = factory.SubFactory(OrganisationFactory)
    tax_type = "GSTIN"
    tax_code = "22AAAAA0000A1Z5"


# ---------------------------------------------------------------------------
# Currency and Bank factories (FR-05)
# ---------------------------------------------------------------------------

class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency

    # Unique 3-letter codes: USD, USe, USf, ... (n=0 → "USD", sequential after)
    code = factory.Sequence(lambda n: f"C{n:02d}")
    name = factory.Sequence(lambda n: f"Currency {n}")


class BankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bank

    nickname = factory.Sequence(lambda n: f"Bank Account {n}")
    beneficiary_name = factory.Sequence(lambda n: f"Beneficiary {n}")
    bank_name = factory.Sequence(lambda n: f"Bank {n}")
    bank_country = factory.SubFactory(CountryFactory)
    branch_name = factory.Sequence(lambda n: f"Branch {n}")
    branch_address = ""
    account_number = factory.Sequence(lambda n: f"ACC{n:06d}")
    account_type = Bank.AccountType.CURRENT
    currency = factory.SubFactory(CurrencyFactory)
    swift_code = ""
    iban = ""
    routing_number = ""
