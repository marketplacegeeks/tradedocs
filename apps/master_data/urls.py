from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CountryViewSet, IncotermViewSet, LocationViewSet,
    OrganisationAddressViewSet, OrganisationViewSet,
    PortViewSet, PaymentTermViewSet, PreCarriageByViewSet, UOMViewSet,
)

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("ports", PortViewSet, basename="port")
router.register("locations", LocationViewSet, basename="location")
router.register("incoterms", IncotermViewSet, basename="incoterm")
router.register("uom", UOMViewSet, basename="uom")
router.register("payment-terms", PaymentTermViewSet, basename="paymentterm")
router.register("pre-carriage", PreCarriageByViewSet, basename="precarriageby")
router.register("organisations", OrganisationViewSet, basename="organisation")

# Nested address routes under /organisations/{organisation_pk}/addresses/
# Written manually so we don't need an extra package (drf-nested-routers).
address_patterns = [
    path(
        "organisations/<int:organisation_pk>/addresses/",
        OrganisationAddressViewSet.as_view({"get": "list", "post": "create"}),
        name="organisation-address-list",
    ),
    path(
        "organisations/<int:organisation_pk>/addresses/<int:pk>/",
        OrganisationAddressViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="organisation-address-detail",
    ),
]

urlpatterns = router.urls + address_patterns
