import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import MakerFactory, CheckerFactory, CompanyAdminFactory
from .factories import (
    BankFactory, CountryFactory, CurrencyFactory, IncotermFactory, LocationFactory,
    OrganisationAddressFactory, OrganisationFactory, OrganisationTagFactory,
    PortFactory, PaymentTermFactory, PreCarriageByFactory, TCTemplateFactory, UOMFactory,
)


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

    def test_checker_can_patch_country(self):
        country = CountryFactory(name="India", iso2="IN", iso3="IND")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("country-detail", args=[country.id]), {"name": "India Updated"})
        assert response.status_code == 200
        assert response.data["name"] == "India Updated"

    def test_maker_cannot_patch_country(self):
        country = CountryFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("country-detail", args=[country.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_country(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("country-detail", args=[country.id]))
        assert response.status_code == 204
        country.refresh_from_db()
        assert country.is_active is False

    def test_soft_deleted_country_hidden_from_default_list(self):
        active = CountryFactory()
        inactive = CountryFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("country-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_countries(self):
        CountryFactory(is_active=True)
        inactive = CountryFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("country-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


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

    def test_company_admin_can_create_port(self):
        country = CountryFactory()
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("port-list"), {"name": "Chennai", "code": "INMAA", "country": country.id})
        assert response.status_code == 201

    def test_checker_can_patch_port(self):
        port = PortFactory(name="Mumbai")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("port-detail", args=[port.id]), {"name": "Mumbai Updated"})
        assert response.status_code == 200
        assert response.data["name"] == "Mumbai Updated"

    def test_maker_cannot_patch_port(self):
        port = PortFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("port-detail", args=[port.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_port(self):
        port = PortFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("port-detail", args=[port.id]))
        assert response.status_code == 204
        port.refresh_from_db()
        assert port.is_active is False

    def test_soft_deleted_port_hidden_from_default_list(self):
        active = PortFactory()
        inactive = PortFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("port-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_ports(self):
        PortFactory(is_active=True)
        inactive = PortFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("port-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids

    def test_missing_country_returns_400_for_port(self):
        client = auth_client(CheckerFactory())
        response = client.post(reverse("port-list"), {"name": "Test Port", "code": "TPRT"})
        assert response.status_code == 400
        assert "country" in response.data

    def test_response_includes_country_name_for_port(self):
        country = CountryFactory(name="India")
        client = auth_client(CheckerFactory())
        response = client.post(reverse("port-list"), {"name": "Mumbai", "code": "INBOM", "country": country.id})
        assert response.status_code == 201
        assert response.data["country_name"] == "India"


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

    def test_company_admin_can_create_location(self):
        country = CountryFactory()
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("location-list"), {"name": "ICD Patparganj", "country": country.id})
        assert response.status_code == 201

    def test_checker_can_patch_location(self):
        location = LocationFactory(name="Old Name")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("location-detail", args=[location.id]), {"name": "New Name"})
        assert response.status_code == 200
        assert response.data["name"] == "New Name"

    def test_maker_cannot_patch_location(self):
        location = LocationFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("location-detail", args=[location.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_location(self):
        location = LocationFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("location-detail", args=[location.id]))
        assert response.status_code == 204
        location.refresh_from_db()
        assert location.is_active is False

    def test_soft_deleted_location_hidden_from_default_list(self):
        active = LocationFactory()
        inactive = LocationFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("location-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_locations(self):
        LocationFactory(is_active=True)
        inactive = LocationFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("location-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids

    def test_missing_country_returns_400_for_location(self):
        client = auth_client(CheckerFactory())
        response = client.post(reverse("location-list"), {"name": "Test Location"})
        assert response.status_code == 400
        assert "country" in response.data

    def test_response_includes_country_name_for_location(self):
        country = CountryFactory(name="India")
        client = auth_client(CheckerFactory())
        response = client.post(reverse("location-list"), {"name": "ICD Tughlakabad", "country": country.id})
        assert response.status_code == 201
        assert response.data["country_name"] == "India"


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

    def test_company_admin_can_create_incoterm(self):
        client = auth_client(CompanyAdminFactory())
        assert client.post(reverse("incoterm-list"), {"code": "CIF", "full_name": "Cost Insurance Freight"}).status_code == 201

    def test_checker_can_patch_incoterm(self):
        incoterm = IncotermFactory()
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("incoterm-detail", args=[incoterm.id]), {"description": "Updated description"})
        assert response.status_code == 200

    def test_maker_cannot_patch_incoterm(self):
        incoterm = IncotermFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("incoterm-detail", args=[incoterm.id]), {"description": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_incoterm(self):
        incoterm = IncotermFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("incoterm-detail", args=[incoterm.id]))
        assert response.status_code == 204
        incoterm.refresh_from_db()
        assert incoterm.is_active is False

    def test_soft_deleted_incoterm_hidden_from_default_list(self):
        active = IncotermFactory()
        inactive = IncotermFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("incoterm-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_incoterms(self):
        IncotermFactory(is_active=True)
        inactive = IncotermFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("incoterm-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


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

    def test_company_admin_can_create_uom(self):
        client = auth_client(CompanyAdminFactory())
        assert client.post(reverse("uom-list"), {"name": "Kilograms", "abbreviation": "KG"}).status_code == 201

    def test_checker_can_patch_uom(self):
        uom = UOMFactory(name="Metric Tonnes", abbreviation="MT")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("uom-detail", args=[uom.id]), {"name": "Metric Tons"})
        assert response.status_code == 200
        assert response.data["name"] == "Metric Tons"

    def test_maker_cannot_patch_uom(self):
        uom = UOMFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("uom-detail", args=[uom.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_uom(self):
        uom = UOMFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("uom-detail", args=[uom.id]))
        assert response.status_code == 204
        uom.refresh_from_db()
        assert uom.is_active is False

    def test_soft_deleted_uom_hidden_from_default_list(self):
        active = UOMFactory()
        inactive = UOMFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("uom-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_uoms(self):
        UOMFactory(is_active=True)
        inactive = UOMFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("uom-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


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

    def test_company_admin_can_create_paymentterm(self):
        client = auth_client(CompanyAdminFactory())
        assert client.post(reverse("paymentterm-list"), {"name": "LC at Sight"}).status_code == 201

    def test_checker_can_patch_paymentterm(self):
        term = PaymentTermFactory(name="Advance Payment")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("paymentterm-detail", args=[term.id]), {"description": "Full upfront payment"})
        assert response.status_code == 200

    def test_maker_cannot_patch_paymentterm(self):
        term = PaymentTermFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("paymentterm-detail", args=[term.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_paymentterm(self):
        term = PaymentTermFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("paymentterm-detail", args=[term.id]))
        assert response.status_code == 204
        term.refresh_from_db()
        assert term.is_active is False

    def test_soft_deleted_paymentterm_hidden_from_default_list(self):
        active = PaymentTermFactory()
        inactive = PaymentTermFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("paymentterm-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_paymentterms(self):
        PaymentTermFactory(is_active=True)
        inactive = PaymentTermFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("paymentterm-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


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

    def test_company_admin_can_create_precarriageby(self):
        client = auth_client(CompanyAdminFactory())
        assert client.post(reverse("precarriageby-list"), {"name": "Rail"}).status_code == 201

    def test_checker_can_patch_precarriageby(self):
        carrier = PreCarriageByFactory(name="Truck")
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("precarriageby-detail", args=[carrier.id]), {"name": "Road Truck"})
        assert response.status_code == 200
        assert response.data["name"] == "Road Truck"

    def test_maker_cannot_patch_precarriageby(self):
        carrier = PreCarriageByFactory()
        client = auth_client(MakerFactory())
        response = client.patch(reverse("precarriageby-detail", args=[carrier.id]), {"name": "Changed"})
        assert response.status_code == 403

    def test_checker_can_soft_delete_precarriageby(self):
        carrier = PreCarriageByFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("precarriageby-detail", args=[carrier.id]))
        assert response.status_code == 204
        carrier.refresh_from_db()
        assert carrier.is_active is False

    def test_soft_deleted_precarriageby_hidden_from_default_list(self):
        active = PreCarriageByFactory()
        inactive = PreCarriageByFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("precarriageby-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_precarriageby(self):
        PreCarriageByFactory(is_active=True)
        inactive = PreCarriageByFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("precarriageby-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


# ---------------------------------------------------------------------------
# Organisation endpoints (FR-04)
# ---------------------------------------------------------------------------

def _org_payload(country_id):
    """Minimal valid Organisation payload for POST/PUT tests."""
    return {
        "name": "Sunrise Exports Pvt Ltd",
        "iec_code": None,
        "tags": [{"tag": "CONSIGNEE"}],
        "addresses": [
            {
                "address_type": "REGISTERED",
                "line1": "123 Marine Drive",
                "city": "Mumbai",
                "country": country_id,
                "email": "contact@sunrise.com",
                "contact_name": "Raj Mehta",
                "phone_country_code": "",
                "phone_number": "",
            }
        ],
        "tax_codes": [],
    }


@pytest.mark.django_db
class TestOrganisationEndpoints:
    # Test 9: A Maker (any logged-in user) can view the list of organisations.
    def test_maker_can_list_organisations(self):
        OrganisationFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("organisation-list"))
        assert response.status_code == 200
        assert len(response.data) >= 2

    # Test 10: Someone who is not logged in at all cannot access the organisation list.
    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(reverse("organisation-list"))
        assert response.status_code == 401

    # Test 11: A Maker does not have permission to create an organisation.
    def test_maker_cannot_create_organisation(self):
        country = CountryFactory()
        client = auth_client(MakerFactory())
        response = client.post(
            reverse("organisation-list"), _org_payload(country.id), format="json"
        )
        assert response.status_code == 403

    # Test 12: A Checker can create a complete and valid organisation.
    def test_checker_can_create_organisation(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-list"), _org_payload(country.id), format="json"
        )
        assert response.status_code == 201
        assert response.data["name"] == "Sunrise Exports Pvt Ltd"

    # Test 13: Trying to create an organisation with no tags is rejected with a clear error.
    def test_create_without_tags_returns_validation_error(self):
        country = CountryFactory()
        payload = _org_payload(country.id)
        payload["tags"] = []
        client = auth_client(CheckerFactory())
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400
        assert "tags" in response.data

    # Test 14: Trying to create an organisation with no addresses is rejected with a clear error.
    def test_create_without_addresses_returns_validation_error(self):
        country = CountryFactory()
        payload = _org_payload(country.id)
        payload["addresses"] = []
        client = auth_client(CheckerFactory())
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400
        assert "addresses" in response.data

    # Test 15: An Exporter-tagged organisation requires an IEC code — omitting it is rejected.
    def test_exporter_without_iec_code_returns_validation_error(self):
        country = CountryFactory()
        payload = _org_payload(country.id)
        payload["tags"] = [{"tag": "EXPORTER"}]
        payload["iec_code"] = None
        client = auth_client(CheckerFactory())
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400
        assert "iec_code" in response.data

    # Test 16: An Exporter-tagged organisation with a valid IEC code is created successfully.
    def test_exporter_with_valid_iec_code_succeeds(self):
        country = CountryFactory()
        payload = _org_payload(country.id)
        payload["tags"] = [{"tag": "EXPORTER"}]
        payload["iec_code"] = "AABCD1234E"
        client = auth_client(CheckerFactory())
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 201
        assert response.data["iec_code"] == "AABCD1234E"

    # Test 17: Calling DELETE on an organisation returns 405 (organisations cannot be deleted).
    def test_delete_organisation_returns_405(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        OrganisationTagFactory(organisation=org, tag="CONSIGNEE")
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("organisation-detail", args=[org.id]))
        assert response.status_code == 405

    # Test 18: A Checker can deactivate an organisation by patching is_active to false.
    def test_checker_can_deactivate_organisation(self):
        org = OrganisationFactory(is_active=True)
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-detail", args=[org.id]),
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 200
        org.refresh_from_db()
        assert org.is_active is False

    # Test 19: A deactivated organisation does not appear in the default list (only active shown).
    def test_inactive_org_hidden_from_default_list(self):
        active_org = OrganisationFactory(is_active=True)
        inactive_org = OrganisationFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("organisation-list"))
        ids_returned = [item["id"] for item in response.data]
        assert active_org.id in ids_returned
        assert inactive_org.id not in ids_returned

    # Test 20: Filtering by ?tag=EXPORTER returns only organisations tagged as Exporter.
    def test_filter_by_tag_returns_matching_organisations(self):
        exporter = OrganisationFactory(name="Export Co")
        OrganisationTagFactory(organisation=exporter, tag="EXPORTER")
        consignee = OrganisationFactory(name="Consignee Co")
        OrganisationTagFactory(organisation=consignee, tag="CONSIGNEE")
        client = auth_client(MakerFactory())
        response = client.get(reverse("organisation-list") + "?tag=EXPORTER")
        names_returned = [item["name"] for item in response.data]
        assert "Export Co" in names_returned
        assert "Consignee Co" not in names_returned

    def test_invalid_iec_code_format_rejected(self):
        """IEC code must be exactly 10 uppercase alphanumeric chars. Any other format is rejected."""
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        payload = _org_payload(country.id)
        payload["tags"] = [{"tag": "EXPORTER"}]
        payload["iec_code"] = "abc123"  # too short and lowercase
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400
        assert "iec_code" in response.data

    def test_create_with_valid_gstin_tax_code_succeeds(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        payload = _org_payload(country.id)
        payload["tax_codes"] = [{"tax_type": "GSTIN", "tax_code": "22AAAAA0000A1Z5"}]
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 201
        assert len(response.data["tax_codes"]) == 1

    def test_create_with_invalid_gstin_rejected(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        payload = _org_payload(country.id)
        payload["tax_codes"] = [{"tax_type": "GSTIN", "tax_code": "BADGSTIN"}]
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400

    def test_create_with_invalid_pan_rejected(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        payload = _org_payload(country.id)
        payload["tax_codes"] = [{"tax_type": "PAN", "tax_code": "BADPAN"}]
        response = client.post(reverse("organisation-list"), payload, format="json")
        assert response.status_code == 400

    def test_maker_cannot_patch_organisation(self):
        org = OrganisationFactory()
        client = auth_client(MakerFactory())
        response = client.patch(
            reverse("organisation-detail", args=[org.id]),
            {"name": "Attempted Change"},
            format="json",
        )
        assert response.status_code == 403

    def test_checker_can_patch_organisation_name(self):
        org = OrganisationFactory(name="Original Name")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-detail", args=[org.id]),
            {"name": "Updated Name"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == "Updated Name"

    def test_patch_with_new_tags_replaces_existing_tags(self):
        """Sending tags in a PATCH replaces the existing tags wholesale."""
        org = OrganisationFactory()
        OrganisationTagFactory(organisation=org, tag="CONSIGNEE")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-detail", args=[org.id]),
            {"tags": [{"tag": "BUYER"}]},
            format="json",
        )
        assert response.status_code == 200
        tag_values = [t["tag"] for t in response.data["tags"]]
        assert "BUYER" in tag_values
        assert "CONSIGNEE" not in tag_values

    def test_patch_omitting_tags_leaves_tags_unchanged(self):
        """A PATCH that does not include 'tags' must leave existing tags intact."""
        org = OrganisationFactory(name="Test Org")
        OrganisationTagFactory(organisation=org, tag="CONSIGNEE")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-detail", args=[org.id]),
            {"name": "Test Org Renamed"},
            format="json",
        )
        assert response.status_code == 200
        tag_values = [t["tag"] for t in response.data["tags"]]
        assert "CONSIGNEE" in tag_values

    def test_inactive_filter_returns_inactive_organisations(self):
        OrganisationFactory(is_active=True)
        inactive = OrganisationFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("organisation-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids

    def test_get_detail_returns_nested_addresses_and_tags(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        OrganisationTagFactory(organisation=org, tag="CONSIGNEE")
        client = auth_client(MakerFactory())
        response = client.get(reverse("organisation-detail", args=[org.id]))
        assert response.status_code == 200
        assert "addresses" in response.data
        assert "tags" in response.data
        assert len(response.data["addresses"]) >= 1
        assert len(response.data["tags"]) >= 1


@pytest.mark.django_db
class TestOrganisationAddressEndpoints:
    # Test 21: A Checker can add a new address to an organisation that already has one.
    def test_checker_can_add_address(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Office Contact",
                "phone_country_code": "",
                "phone_number": "",
            },
            format="json",
        )
        assert response.status_code == 201

    # Test 22: A Maker cannot add an address to an organisation (write is restricted).
    def test_maker_cannot_add_address(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(MakerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Office Contact",
                "phone_country_code": "",
                "phone_number": "",
            },
            format="json",
        )
        assert response.status_code == 403

    # Test 23: Deleting one of two addresses succeeds — there's still one left.
    def test_can_delete_address_when_another_exists(self):
        org = OrganisationFactory()
        address1 = OrganisationAddressFactory(organisation=org, address_type="REGISTERED")
        OrganisationAddressFactory(organisation=org, address_type="OFFICE")
        client = auth_client(CheckerFactory())
        response = client.delete(
            reverse("organisation-address-detail", args=[org.id, address1.id])
        )
        assert response.status_code == 204

    # Test 24: Deleting the only address is blocked — every organisation must keep at least one.
    def test_cannot_delete_last_address(self):
        org = OrganisationFactory()
        address = OrganisationAddressFactory(organisation=org)
        client = auth_client(CheckerFactory())
        response = client.delete(
            reverse("organisation-address-detail", args=[org.id, address.id])
        )
        assert response.status_code == 400

    # Test 25: Adding a second address of the same type to an organisation is blocked.
    def test_cannot_add_duplicate_address_type(self):
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org, address_type="REGISTERED")
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "REGISTERED",
                "line1": "Another Registered Address",
                "city": "Delhi",
                "country": country.id,
                "email": "reg2@org.com",
                "contact_name": "Second Reg",
                "phone_country_code": "",
                "phone_number": "",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "address_type" in str(response.data)

    # Test 26: Org create with two addresses of the same type is blocked.
    def test_org_create_duplicate_address_type_rejected(self):
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-list"),
            {
                "name": "Duplicate Addr Org",
                "iec_code": "",
                "tags": [{"tag": "CONSIGNEE"}],
                "addresses": [
                    {
                        "address_type": "OFFICE",
                        "line1": "First Office",
                        "city": "Mumbai",
                        "country": country.id,
                        "email": "a@org.com",
                        "contact_name": "Contact A",
                        "phone_country_code": "",
                        "phone_number": "",
                    },
                    {
                        "address_type": "OFFICE",
                        "line1": "Second Office",
                        "city": "Delhi",
                        "country": country.id,
                        "email": "b@org.com",
                        "contact_name": "Contact B",
                        "phone_country_code": "",
                        "phone_number": "",
                    },
                ],
                "tax_codes": [],
            },
            format="json",
        )
        assert response.status_code == 400
        assert "addresses" in str(response.data)

    def test_phone_number_without_country_code_rejected(self):
        """Providing a phone number without a country code must be rejected."""
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Contact",
                "phone_country_code": "",
                "phone_number": "9876543210",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "phone" in str(response.data)

    def test_phone_country_code_without_number_rejected(self):
        """Providing a country code without a phone number must be rejected."""
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Contact",
                "phone_country_code": "+91",
                "phone_number": "",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "phone" in str(response.data)

    def test_invalid_phone_format_rejected(self):
        """Both fields provided but in an unparseable format must be rejected."""
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Contact",
                "phone_country_code": "NOTACODE",
                "phone_number": "NOTANUMBER",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "phone" in str(response.data)

    def test_valid_phone_accepted(self):
        """A proper dial code + local number combo must be accepted."""
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org)
        country = CountryFactory()
        client = auth_client(CheckerFactory())
        response = client.post(
            reverse("organisation-address-list", args=[org.id]),
            {
                "address_type": "OFFICE",
                "line1": "456 BKC",
                "city": "Mumbai",
                "country": country.id,
                "email": "office@org.com",
                "contact_name": "Contact",
                "phone_country_code": "+91",
                "phone_number": "9876543210",
            },
            format="json",
        )
        assert response.status_code == 201

    def test_maker_cannot_patch_address(self):
        org = OrganisationFactory()
        address = OrganisationAddressFactory(organisation=org)
        client = auth_client(MakerFactory())
        response = client.patch(
            reverse("organisation-address-detail", args=[org.id, address.id]),
            {"city": "Delhi"},
            format="json",
        )
        assert response.status_code == 403

    def test_checker_can_patch_address(self):
        org = OrganisationFactory()
        address = OrganisationAddressFactory(organisation=org, city="Mumbai")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-address-detail", args=[org.id, address.id]),
            {"city": "Delhi"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["city"] == "Delhi"

    def test_patch_to_existing_address_type_rejected(self):
        """Changing an address's type to one that already exists for this org is blocked."""
        org = OrganisationFactory()
        OrganisationAddressFactory(organisation=org, address_type="REGISTERED")
        office = OrganisationAddressFactory(organisation=org, address_type="OFFICE")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("organisation-address-detail", args=[org.id, office.id]),
            {"address_type": "REGISTERED"},  # REGISTERED already exists on this org
            format="json",
        )
        assert response.status_code == 400
        assert "address_type" in str(response.data)


# ---------------------------------------------------------------------------
# Currency endpoints (FR-05)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCurrencyEndpoints:
    # Test 25: Any authenticated user can list currencies (needed for Bank form dropdown).
    def test_maker_can_list_currencies(self):
        CurrencyFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("currency-list"))
        assert response.status_code == 200
        assert len(response.data) >= 2

    # Test 26: A Maker cannot create currencies — write is restricted to Checker/Admin.
    def test_maker_cannot_create_currency(self):
        client = auth_client(MakerFactory())
        response = client.post(reverse("currency-list"), {"code": "USD", "name": "US Dollar"})
        assert response.status_code == 403

    # Test 27: A Checker can create a currency.
    def test_checker_can_create_currency(self):
        client = auth_client(CheckerFactory())
        response = client.post(reverse("currency-list"), {"code": "USD", "name": "US Dollar"})
        assert response.status_code == 201
        assert response.data["code"] == "USD"

    # Test 28: An unauthenticated request is rejected.
    def test_unauthenticated_cannot_list_currencies(self):
        client = APIClient()
        response = client.get(reverse("currency-list"))
        assert response.status_code == 401

    def test_company_admin_can_create_currency(self):
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("currency-list"), {"code": "EUR", "name": "Euro"})
        assert response.status_code == 201

    def test_checker_can_patch_currency(self):
        currency = CurrencyFactory(code="USD", name="US Dollar")
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("currency-detail", args=[currency.id]),
            {"name": "United States Dollar"},
        )
        assert response.status_code == 200
        assert response.data["name"] == "United States Dollar"

    def test_delete_currency_does_not_hard_delete_record(self):
        """CurrencyViewSet inherits ReferenceDataViewSet.destroy which sets instance.is_active = False.
        Currency has no is_active field so the attribute is set in memory but not persisted.
        The row must NOT be removed from the database — the response is still 204."""
        from apps.master_data.models import Currency as CurrencyModel
        currency = CurrencyFactory()
        currency_id = currency.id
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("currency-detail", args=[currency_id]))
        assert response.status_code == 204
        assert CurrencyModel.objects.filter(id=currency_id).exists()


# ---------------------------------------------------------------------------
# Bank endpoints (FR-05)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBankEndpoints:
    def _valid_payload(self, country, currency, organisation=None):
        """Return a minimal valid bank creation payload."""
        org = organisation or OrganisationFactory()
        OrganisationTagFactory(organisation=org, tag="EXPORTER")
        return {
            "organisation": org.id,
            "nickname": "USD Operating Account",
            "beneficiary_name": "Sunrise Exports Pvt Ltd",
            "bank_name": "HDFC Bank",
            "bank_country": country.id,
            "branch_name": "Fort Branch",
            "account_number": "50100123456789",
            "account_type": "CURRENT",
            "currency": currency.id,
        }

    # Test 29: Any authenticated user can list banks (needed for PI/CI dropdowns).
    def test_maker_can_list_banks(self):
        BankFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("bank-list"))
        assert response.status_code == 200
        assert len(response.data) >= 2

    # Test 30: A Maker cannot create a bank — write is Checker/Admin only.
    def test_maker_cannot_create_bank(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        client = auth_client(MakerFactory())
        response = client.post(reverse("bank-list"), self._valid_payload(country, currency))
        assert response.status_code == 403

    # Test 31: A Company Admin can create a bank with all required fields.
    def test_company_admin_can_create_bank(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("bank-list"), self._valid_payload(country, currency))
        assert response.status_code == 201
        assert response.data["bank_name"] == "HDFC Bank"

    # Test 32: Response includes read-only display fields so the frontend doesn't need extra calls.
    def test_create_response_includes_display_fields(self):
        country = CountryFactory(name="India")
        currency = CurrencyFactory(code="INR", name="Indian Rupee")
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), self._valid_payload(country, currency))
        assert response.status_code == 201
        assert response.data["bank_country_name"] == "India"
        assert response.data["currency_code"] == "INR"
        assert response.data["currency_name"] == "Indian Rupee"

    # Test 33: A valid 8-char SWIFT code is accepted.
    def test_valid_swift_8_chars_accepted(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["swift_code"] = "HDFCINBB"
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 201

    # Test 34: An invalid SWIFT code (wrong length) is rejected.
    def test_invalid_swift_rejected(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["swift_code"] = "BADC0DE"  # 7 chars
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400
        assert "swift_code" in response.data

    # Test 35: A valid IBAN is accepted.
    def test_valid_iban_accepted(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["iban"] = "GB29NWBK60161331926819"
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 201

    # Test 36: An invalid IBAN (starts with digits) is rejected.
    def test_invalid_iban_rejected(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["iban"] = "12BADIBAN"
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400
        assert "iban" in response.data

    # Test 37: Omitting a required field returns 400.
    def test_missing_required_field_rejected(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        del payload["account_number"]
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400

    # Test 38: An unauthenticated request is rejected.
    def test_unauthenticated_cannot_list_banks(self):
        client = APIClient()
        response = client.get(reverse("bank-list"))
        assert response.status_code == 401

    # Test 39: A Checker can update an existing bank via PATCH.
    def test_checker_can_patch_bank(self):
        bank = BankFactory()
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("bank-detail", args=[bank.id]),
            {"nickname": "Updated Nickname"},
        )
        assert response.status_code == 200
        assert response.data["nickname"] == "Updated Nickname"

    def test_checker_can_create_bank(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), self._valid_payload(country, currency))
        assert response.status_code == 201

    def test_non_exporter_org_rejected(self):
        """A bank must belong to an Exporter-tagged organisation — other tags are not allowed."""
        country = CountryFactory()
        currency = CurrencyFactory()
        org = OrganisationFactory()
        OrganisationTagFactory(organisation=org, tag="CONSIGNEE")
        # Build the payload manually to avoid _valid_payload adding an EXPORTER tag.
        payload = {
            "organisation": org.id,
            "nickname": "Test Account",
            "beneficiary_name": "Test Co",
            "bank_name": "Test Bank",
            "bank_country": country.id,
            "branch_name": "Main Branch",
            "account_number": "ACC12345",
            "account_type": "CURRENT",
            "currency": currency.id,
        }
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400
        assert "organisation" in response.data

    def test_intermediary_partial_fields_rejected(self):
        """Providing some but not all 4 intermediary fields must be rejected."""
        country = CountryFactory()
        currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["intermediary_bank_name"] = "Correspondent Bank"
        # intentionally omitting: intermediary_account_number, intermediary_swift_code, intermediary_currency
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400

    def test_intermediary_all_fields_accepted(self):
        """Providing all 4 intermediary fields together is a valid submission."""
        country = CountryFactory()
        currency = CurrencyFactory()
        intermediary_currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["intermediary_bank_name"] = "Correspondent Bank"
        payload["intermediary_account_number"] = "ACC123456"
        payload["intermediary_swift_code"] = "CORRUS33"
        payload["intermediary_currency"] = intermediary_currency.id
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 201

    def test_intermediary_swift_invalid_format_rejected(self):
        country = CountryFactory()
        currency = CurrencyFactory()
        intermediary_currency = CurrencyFactory()
        payload = self._valid_payload(country, currency)
        payload["intermediary_bank_name"] = "Correspondent Bank"
        payload["intermediary_account_number"] = "ACC123456"
        payload["intermediary_swift_code"] = "BADC0DE"  # 7 chars — invalid
        payload["intermediary_currency"] = intermediary_currency.id
        client = auth_client(CheckerFactory())
        response = client.post(reverse("bank-list"), payload)
        assert response.status_code == 400
        assert "intermediary_swift_code" in response.data

    def test_maker_cannot_patch_bank(self):
        bank = BankFactory()
        client = auth_client(MakerFactory())
        response = client.patch(
            reverse("bank-detail", args=[bank.id]),
            {"nickname": "Attempted Change"},
        )
        assert response.status_code == 403

    def test_checker_can_deactivate_bank_via_patch(self):
        bank = BankFactory(is_active=True)
        client = auth_client(CheckerFactory())
        response = client.patch(reverse("bank-detail", args=[bank.id]), {"is_active": False})
        assert response.status_code == 200
        bank.refresh_from_db()
        assert bank.is_active is False

    def test_inactive_bank_hidden_from_default_list(self):
        active = BankFactory(is_active=True)
        inactive = BankFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("bank-list"))
        ids = [item["id"] for item in response.data]
        assert active.id in ids
        assert inactive.id not in ids

    def test_inactive_filter_returns_inactive_banks(self):
        BankFactory(is_active=True)
        inactive = BankFactory(is_active=False)
        client = auth_client(MakerFactory())
        response = client.get(reverse("bank-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids


# ---------------------------------------------------------------------------
# T&C Template endpoints (FR-07)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTCTemplateEndpoints:
    def _valid_payload(self, org_id: int) -> dict:
        return {
            "name": "Standard Terms",
            "body": "<p>Standard terms and conditions apply.</p>",
            "organisations": [org_id],
        }

    # Happy path: any authenticated user can list templates.
    def test_maker_can_list_templates(self):
        TCTemplateFactory.create_batch(2)
        client = auth_client(MakerFactory())
        response = client.get(reverse("tctemplate-list"))
        assert response.status_code == 200
        assert len(response.data) >= 2

    # Happy path: Checker can create a template.
    def test_checker_can_create_template(self):
        org = OrganisationFactory()
        client = auth_client(CheckerFactory())
        response = client.post(reverse("tctemplate-list"), self._valid_payload(org.id), format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Standard Terms"

    # Happy path: Company Admin can create a template.
    def test_company_admin_can_create_template(self):
        org = OrganisationFactory()
        client = auth_client(CompanyAdminFactory())
        response = client.post(reverse("tctemplate-list"), self._valid_payload(org.id), format="json")
        assert response.status_code == 201

    # Permission denial: Maker cannot create a template.
    def test_maker_cannot_create_template(self):
        org = OrganisationFactory()
        client = auth_client(MakerFactory())
        response = client.post(reverse("tctemplate-list"), self._valid_payload(org.id), format="json")
        assert response.status_code == 403

    # Validation: empty body is rejected.
    def test_empty_body_rejected(self):
        org = OrganisationFactory()
        client = auth_client(CheckerFactory())
        payload = self._valid_payload(org.id)
        payload["body"] = "   "  # whitespace only
        response = client.post(reverse("tctemplate-list"), payload, format="json")
        assert response.status_code == 400
        assert "body" in response.data

    # Validation: no organisations is rejected.
    def test_no_organisations_rejected(self):
        client = auth_client(CheckerFactory())
        payload = {
            "name": "Orphan Template",
            "body": "<p>Some content</p>",
            "organisations": [],
        }
        response = client.post(reverse("tctemplate-list"), payload, format="json")
        assert response.status_code == 400
        assert "organisations" in response.data

    # Validation: duplicate name is rejected.
    def test_duplicate_name_rejected(self):
        org = OrganisationFactory()
        TCTemplateFactory(name="Existing Template", organisations=[org])
        client = auth_client(CheckerFactory())
        payload = self._valid_payload(org.id)
        payload["name"] = "Existing Template"
        response = client.post(reverse("tctemplate-list"), payload, format="json")
        assert response.status_code == 400
        assert "name" in response.data

    # Soft delete: DELETE sets is_active=False, does not hard-delete.
    def test_delete_soft_deletes_template(self):
        template = TCTemplateFactory()
        client = auth_client(CheckerFactory())
        response = client.delete(reverse("tctemplate-detail", args=[template.id]))
        assert response.status_code == 204
        template.refresh_from_db()
        assert template.is_active is False

    # After soft delete, the template no longer appears in the default list.
    def test_soft_deleted_template_not_in_list(self):
        template = TCTemplateFactory()
        template.is_active = False
        template.save()
        client = auth_client(MakerFactory())
        response = client.get(reverse("tctemplate-list"))
        ids = [t["id"] for t in response.data]
        assert template.id not in ids

    # Maker cannot delete a template.
    def test_maker_cannot_delete_template(self):
        template = TCTemplateFactory()
        client = auth_client(MakerFactory())
        response = client.delete(reverse("tctemplate-detail", args=[template.id]))
        assert response.status_code == 403

    # Unauthenticated requests are rejected.
    def test_unauthenticated_cannot_list(self):
        client = APIClient()
        response = client.get(reverse("tctemplate-list"))
        assert response.status_code == 401

    def test_maker_cannot_patch_template(self):
        template = TCTemplateFactory()
        client = auth_client(MakerFactory())
        response = client.patch(
            reverse("tctemplate-detail", args=[template.id]),
            {"name": "Attempted Change"},
            format="json",
        )
        assert response.status_code == 403

    def test_checker_can_patch_template(self):
        org = OrganisationFactory()
        template = TCTemplateFactory(name="Original Name", organisations=[org])
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("tctemplate-detail", args=[template.id]),
            {"name": "Updated Name"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["name"] == "Updated Name"

    def test_name_update_excludes_self_from_uniqueness_check(self):
        """PATCHing a template with its own existing name must not trigger a duplicate error."""
        org = OrganisationFactory()
        template = TCTemplateFactory(name="My Terms", organisations=[org])
        client = auth_client(CheckerFactory())
        response = client.patch(
            reverse("tctemplate-detail", args=[template.id]),
            {"name": "My Terms"},  # same name — should be allowed
            format="json",
        )
        assert response.status_code == 200

    def test_response_includes_organisation_names(self):
        org = OrganisationFactory(name="Sunrise Exports")
        template = TCTemplateFactory(organisations=[org])
        client = auth_client(MakerFactory())
        response = client.get(reverse("tctemplate-detail", args=[template.id]))
        assert response.status_code == 200
        assert "organisation_names" in response.data
        assert "Sunrise Exports" in response.data["organisation_names"]

    def test_inactive_filter_returns_inactive_templates(self):
        TCTemplateFactory()
        inactive = TCTemplateFactory()
        inactive.is_active = False
        inactive.save()
        client = auth_client(MakerFactory())
        response = client.get(reverse("tctemplate-list") + "?is_active=false")
        ids = [item["id"] for item in response.data]
        assert inactive.id in ids
