import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from .factories import (
    BankFactory, CountryFactory, CurrencyFactory, IncotermFactory, LocationFactory,
    OrganisationAddressFactory, OrganisationFactory, OrganisationTagFactory,
    OrganisationTaxCodeFactory, PaymentTermFactory, PortFactory, PreCarriageByFactory,
    TCTemplateFactory, UOMFactory,
)


@pytest.mark.django_db
class TestCountryModel:
    def test_str(self):
        country = CountryFactory(name="India", iso2="IN", iso3="IND")
        assert str(country) == "India (IN)"

    def test_iso2_must_be_unique(self):
        CountryFactory(iso2="IN", iso3="IND")
        with pytest.raises(IntegrityError):
            CountryFactory(iso2="IN", iso3="INE")  # duplicate iso2

    def test_iso3_must_be_unique(self):
        CountryFactory(iso2="IN", iso3="IND")
        with pytest.raises(IntegrityError):
            CountryFactory(iso2="IO", iso3="IND")  # duplicate iso3

    def test_is_active_defaults_to_true(self):
        country = CountryFactory()
        assert country.is_active is True


@pytest.mark.django_db
class TestPortModel:
    def test_str(self):
        port = PortFactory(name="Mumbai", code="INBOM")
        assert str(port) == "Mumbai (INBOM)"

    def test_code_must_be_unique(self):
        country = CountryFactory()
        PortFactory(code="INBOM", country=country)
        with pytest.raises(IntegrityError):
            PortFactory(code="INBOM", country=country)

    def test_deleting_country_with_port_raises_protected_error(self):
        """Constraint #7: on_delete=PROTECT prevents orphaning ports."""
        port = PortFactory()
        with pytest.raises(ProtectedError):
            port.country.delete()

    def test_is_active_defaults_to_true(self):
        port = PortFactory()
        assert port.is_active is True


@pytest.mark.django_db
class TestLocationModel:
    def test_str(self):
        country = CountryFactory(name="India", iso2="IN", iso3="IND")
        location = LocationFactory(name="Mumbai ICD", country=country)
        assert str(location) == "Mumbai ICD, India"

    def test_deleting_country_with_location_raises_protected_error(self):
        """Constraint #7: on_delete=PROTECT prevents orphaning locations."""
        location = LocationFactory()
        with pytest.raises(ProtectedError):
            location.country.delete()

    def test_is_active_defaults_to_true(self):
        location = LocationFactory()
        assert location.is_active is True


@pytest.mark.django_db
class TestIncotermModel:
    def test_str(self):
        incoterm = IncotermFactory(code="FOB", full_name="Free On Board")
        assert str(incoterm) == "FOB – Free On Board"

    def test_code_must_be_unique(self):
        IncotermFactory(code="FOB")
        with pytest.raises(IntegrityError):
            IncotermFactory(code="FOB")

    def test_is_active_defaults_to_true(self):
        incoterm = IncotermFactory()
        assert incoterm.is_active is True


@pytest.mark.django_db
class TestUOMModel:
    def test_str(self):
        uom = UOMFactory(name="Metric Tonnes", abbreviation="MT")
        assert str(uom) == "MT"

    def test_abbreviation_must_be_unique(self):
        UOMFactory(abbreviation="MT")
        with pytest.raises(IntegrityError):
            UOMFactory(abbreviation="MT")

    def test_is_active_defaults_to_true(self):
        uom = UOMFactory()
        assert uom.is_active is True


# ---------------------------------------------------------------------------
# PaymentTerm model tests (FR-06)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPaymentTermModel:
    def test_str(self):
        term = PaymentTermFactory(name="Advance Payment")
        assert str(term) == "Advance Payment"

    def test_is_active_defaults_to_true(self):
        term = PaymentTermFactory()
        assert term.is_active is True


# ---------------------------------------------------------------------------
# PreCarriageBy model tests (FR-06)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPreCarriageByModel:
    def test_str(self):
        carrier = PreCarriageByFactory(name="Truck")
        assert str(carrier) == "Truck"

    def test_is_active_defaults_to_true(self):
        carrier = PreCarriageByFactory()
        assert carrier.is_active is True


# ---------------------------------------------------------------------------
# Organisation model tests (FR-04)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOrganisationModel:
    # Test 1: __str__ returns the organisation name.
    def test_str(self):
        org = OrganisationFactory(name="Sunrise Exports Pvt Ltd")
        assert str(org) == "Sunrise Exports Pvt Ltd"

    # Test 2: Two organisations cannot share the same name — the database enforces uniqueness.
    def test_name_must_be_unique(self):
        OrganisationFactory(name="Sunrise Exports")
        with pytest.raises(IntegrityError):
            OrganisationFactory(name="Sunrise Exports")

    # Test 3: Multiple organisations can have no IEC code — blank/null does not conflict.
    def test_multiple_orgs_can_have_null_iec_code(self):
        OrganisationFactory(iec_code=None)
        OrganisationFactory(iec_code=None)  # should not raise

    # Test 4: Two organisations cannot share the same non-blank IEC code.
    def test_iec_code_must_be_unique_when_set(self):
        OrganisationFactory(iec_code="AABCD1234E")
        with pytest.raises(IntegrityError):
            OrganisationFactory(iec_code="AABCD1234E")

    # Test 5: Deleting a Country that is used by an OrganisationAddress is blocked.
    # This protects data integrity — you cannot orphan an address by removing its country.
    def test_deleting_country_used_by_address_raises_protected_error(self):
        address = OrganisationAddressFactory()
        with pytest.raises(ProtectedError):
            address.country.delete()

    # Test 6: Deleting an Organisation removes all its child records automatically (CASCADE).
    def test_deleting_org_cascades_to_addresses_tags_tax_codes(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        OrganisationTagFactory(organisation=org)
        OrganisationTaxCodeFactory(organisation=org)
        org_id = org.id
        org.delete()
        from apps.master_data.models import OrganisationAddress, OrganisationTag, OrganisationTaxCode
        assert OrganisationAddress.objects.filter(organisation_id=org_id).count() == 0
        assert OrganisationTag.objects.filter(organisation_id=org_id).count() == 0
        assert OrganisationTaxCode.objects.filter(organisation_id=org_id).count() == 0


@pytest.mark.django_db
class TestOrganisationTaxCodeModel:
    # Test 7a: A valid GSTIN passes validation without raising an error.
    def test_valid_gstin_passes_validation(self):
        tax_code = OrganisationTaxCodeFactory.build(tax_type="GSTIN", tax_code="22AAAAA0000A1Z5")
        tax_code.clean()  # should not raise

    # Test 7b: A GSTIN with the wrong format raises a ValidationError.
    def test_invalid_gstin_raises_validation_error(self):
        tax_code = OrganisationTaxCodeFactory.build(tax_type="GSTIN", tax_code="BADGSTIN")
        with pytest.raises(ValidationError):
            tax_code.clean()

    # Test 8a: A valid PAN passes validation without raising an error.
    # PAN format: 3 letters + entity-type letter (P/C/H/F/A/T/B/L/J/G/E) + letter + 4 digits + letter
    def test_valid_pan_passes_validation(self):
        tax_code = OrganisationTaxCodeFactory.build(tax_type="PAN", tax_code="ABCPD1234E")
        tax_code.clean()  # should not raise

    # Test 8b: A PAN with the wrong format raises a ValidationError.
    def test_invalid_pan_raises_validation_error(self):
        tax_code = OrganisationTaxCodeFactory.build(tax_type="PAN", tax_code="BADPAN")
        with pytest.raises(ValidationError):
            tax_code.clean()


# ---------------------------------------------------------------------------
# Currency and Bank model tests (FR-05)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCurrencyModel:
    def test_str(self):
        currency = CurrencyFactory(code="USD", name="US Dollar")
        assert str(currency) == "USD – US Dollar"

    def test_code_must_be_unique(self):
        CurrencyFactory(code="USD")
        with pytest.raises(IntegrityError):
            CurrencyFactory(code="USD")


@pytest.mark.django_db
class TestBankModel:
    def test_str(self):
        bank = BankFactory(bank_name="HDFC Bank", nickname="USD Operating Account")
        assert str(bank) == "HDFC Bank – USD Operating Account"

    def test_deleting_country_with_bank_raises_protected_error(self):
        """Constraint #7: on_delete=PROTECT prevents orphaning a bank's country."""
        bank = BankFactory()
        with pytest.raises(ProtectedError):
            bank.bank_country.delete()

    def test_deleting_currency_with_bank_raises_protected_error(self):
        """Constraint #7: on_delete=PROTECT prevents deleting a currency in use."""
        bank = BankFactory()
        with pytest.raises(ProtectedError):
            bank.currency.delete()

    def test_valid_swift_8_chars_passes_validation(self):
        bank = BankFactory.build(swift_code="HDFCINBB")
        # Exclude FK fields: build() doesn't save related objects, so they have no PK.
        # We only want to test the SWIFT validator here.
        bank.full_clean(exclude=["bank_country", "currency"])

    def test_valid_swift_11_chars_passes_validation(self):
        bank = BankFactory.build(swift_code="HDFCINBBXXX")
        bank.full_clean(exclude=["bank_country", "currency"])

    def test_invalid_swift_raises_validation_error(self):
        bank = BankFactory.build(swift_code="BADC0DE")  # 7 chars — invalid
        with pytest.raises(ValidationError):
            bank.full_clean(exclude=["bank_country", "currency"])

    def test_swift_lowercase_raises_validation_error(self):
        bank = BankFactory.build(swift_code="hdfcinbb")  # lowercase — invalid
        with pytest.raises(ValidationError):
            bank.full_clean(exclude=["bank_country", "currency"])

    def test_empty_swift_is_allowed(self):
        bank = BankFactory.build(swift_code="")
        bank.full_clean(exclude=["bank_country", "currency"])  # optional — should not raise

    def test_valid_iban_passes_validation(self):
        bank = BankFactory.build(iban="GB29NWBK60161331926819")
        bank.full_clean(exclude=["bank_country", "currency"])

    def test_invalid_iban_raises_validation_error(self):
        bank = BankFactory.build(iban="12BADIBAN")  # starts with digits, not letters
        with pytest.raises(ValidationError):
            bank.full_clean(exclude=["bank_country", "currency"])

    def test_empty_iban_is_allowed(self):
        bank = BankFactory.build(iban="")
        bank.full_clean(exclude=["bank_country", "currency"])  # optional — should not raise


# ---------------------------------------------------------------------------
# T&C Template model tests (FR-07)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTCTemplateModel:
    def test_str(self):
        template = TCTemplateFactory(name="My Terms")
        assert str(template) == "My Terms"

    def test_name_must_be_unique(self):
        TCTemplateFactory(name="Standard T&C")
        with pytest.raises(Exception):  # IntegrityError from DB unique constraint
            TCTemplateFactory(name="Standard T&C")

    def test_is_active_defaults_to_true(self):
        template = TCTemplateFactory()
        assert template.is_active is True

    def test_can_associate_multiple_organisations(self):
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()
        template = TCTemplateFactory(organisations=[org1, org2])
        assert template.organisations.count() == 2

    def test_soft_delete_sets_is_active_false(self):
        template = TCTemplateFactory()
        template.is_active = False
        template.save()
        template.refresh_from_db()
        assert template.is_active is False
