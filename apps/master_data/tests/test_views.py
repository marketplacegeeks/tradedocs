import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.tests.factories import MakerFactory, CheckerFactory, CompanyAdminFactory
from .factories import CountryFactory, PortFactory, IncotermFactory, UOMFactory, PaymentTermFactory, PreCarriageByFactory, LocationFactory


@pytest.fixture
def api_client():
    return APIClient()


def auth_client(user):
    """Return an APIClient already authenticated as the given user."""
    client = APIClient()
    response = client.post(reverse("auth-login"), {"email": user.email, "password": "testpass123"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


# ---------------------------------------------------------------------------
# Country endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCountryEndpoints:
    def test_maker_can_list_countries(self):
        CountryFactory.create_batch(3)
        client = auth_client(MakerFactory())
        response = client.get(reverse("country-list"))
        assert response.status_code == 200
        assert len(response.data) >= 3

    def test_maker_cannot_create_country(self):
        client = auth_client(MakerFactory())
        response = client.post(reverse("country-list"), {"name": "India", "iso2": "IN", "iso3": "IND"})
        assert response.status_code == 403

    def test_checker_can_create_country(self):
        client = auth_client(CheckerFactory())
        response = client.post(reverse("country-list"), {"name": "India", "iso2": "IN", "iso3": "IND"})
        assert response.status_code == 201

    def test_company_admin_can_create_country(self):
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("country-list"), {"name": "UAE", "iso2": "AE", "iso3": "ARE"})
        assert response.status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(reverse("country-list"))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Port endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPortEndpoints:
    def test_maker_can_list_ports(self):
        PortFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("port-list"))
        assert response.status_code == 200

    def test_maker_cannot_create_port(self):
        country = CountryFactory()
        client = auth_client(MakerFactory())
        response = client.post(reverse("port-list"), {"name": "Mumbai", "code": "INBOM", "country": country.id})
        assert response.status_code == 403

    def test_checker_can_create_port(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(reverse("port-list"), {"name": "Mumbai", "code": "INBOM", "country": country.id})
        assert response.status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(reverse("port-list"))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Location endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLocationEndpoints:
    def test_maker_can_list_locations(self):
        LocationFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("location-list"))
        assert response.status_code == 200

    def test_maker_cannot_create_location(self):
        country = CountryFactory()
        client = auth_client(MakerFactory())
        response = client.post(reverse("location-list"), {"name": "ICD Tughlakabad", "country": country.id})
        assert response.status_code == 403

    def test_checker_can_create_location(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(reverse("location-list"), {"name": "ICD Tughlakabad", "country": country.id})
        assert response.status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(reverse("location-list"))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Incoterm endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIncotermEndpoints:
    def test_maker_can_list(self):
        IncotermFactory.create_batch(2)
        client = auth_client(MakerFactory())
        assert client.get(reverse("incoterm-list")).status_code == 200

    def test_maker_cannot_create(self):
        client = auth_client(MakerFactory())
        assert client.post(reverse("incoterm-list"), {"code": "FOB", "full_name": "Free On Board"}).status_code == 403

    def test_checker_can_create(self):
        client = auth_client(CheckerFactory())
        assert client.post(reverse("incoterm-list"), {"code": "FOB", "full_name": "Free On Board"}).status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        assert api_client.get(reverse("incoterm-list")).status_code == 401


# ---------------------------------------------------------------------------
# UOM endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUOMEndpoints:
    def test_maker_can_list(self):
        UOMFactory.create_batch(2)
        client = auth_client(MakerFactory())
        assert client.get(reverse("uom-list")).status_code == 200

    def test_maker_cannot_create(self):
        client = auth_client(MakerFactory())
        assert client.post(reverse("uom-list"), {"name": "Metric Tonnes", "abbreviation": "MT"}).status_code == 403

    def test_checker_can_create(self):
        client = auth_client(CheckerFactory())
        assert client.post(reverse("uom-list"), {"name": "Metric Tonnes", "abbreviation": "MT"}).status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        assert api_client.get(reverse("uom-list")).status_code == 401


# ---------------------------------------------------------------------------
# PaymentTerm endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPaymentTermEndpoints:
    def test_maker_can_list(self):
        PaymentTermFactory.create_batch(2)
        client = auth_client(MakerFactory())
        assert client.get(reverse("paymentterm-list")).status_code == 200

    def test_maker_cannot_create(self):
        client = auth_client(MakerFactory())
        assert client.post(reverse("paymentterm-list"), {"name": "Advance Payment"}).status_code == 403

    def test_checker_can_create(self):
        client = auth_client(CheckerFactory())
        assert client.post(reverse("paymentterm-list"), {"name": "Advance Payment"}).status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        assert api_client.get(reverse("paymentterm-list")).status_code == 401


# ---------------------------------------------------------------------------
# PreCarriageBy endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPreCarriageByEndpoints:
    def test_maker_can_list(self):
        PreCarriageByFactory.create_batch(2)
        client = auth_client(MakerFactory())
        assert client.get(reverse("precarriageby-list")).status_code == 200

    def test_maker_cannot_create(self):
        client = auth_client(MakerFactory())
        assert client.post(reverse("precarriageby-list"), {"name": "Truck"}).status_code == 403

    def test_checker_can_create(self):
        client = auth_client(CheckerFactory())
        assert client.post(reverse("precarriageby-list"), {"name": "Truck"}).status_code == 201

    def test_unauthenticated_cannot_list(self, api_client):
        assert api_client.get(reverse("precarriageby-list")).status_code == 401
