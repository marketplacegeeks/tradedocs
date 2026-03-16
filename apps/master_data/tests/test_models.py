import pytest
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from .factories import CountryFactory, PortFactory, LocationFactory, IncotermFactory, UOMFactory


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


@pytest.mark.django_db
class TestIncotermModel:
    def test_str(self):
        incoterm = IncotermFactory(code="FOB", full_name="Free On Board")
        assert str(incoterm) == "FOB – Free On Board"

    def test_code_must_be_unique(self):
        IncotermFactory(code="FOB")
        with pytest.raises(IntegrityError):
            IncotermFactory(code="FOB")


@pytest.mark.django_db
class TestUOMModel:
    def test_str(self):
        uom = UOMFactory(name="Metric Tonnes", abbreviation="MT")
        assert str(uom) == "MT"

    def test_abbreviation_must_be_unique(self):
        UOMFactory(abbreviation="MT")
        with pytest.raises(IntegrityError):
            UOMFactory(abbreviation="MT")
