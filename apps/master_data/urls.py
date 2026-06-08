from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BankViewSet, CountryViewSet, CurrencyViewSet, IncotermViewSet, LocationViewSet,
    OrganisationAddressViewSet, OrganisationViewSet,
    PortViewSet, PaymentTermViewSet, PreCarriageByViewSet, TCTemplateViewSet, TypeOfPackageViewSet, UOMViewSet,
    ProductViewSet, ProductGradeViewSet, TestParameterViewSet, TestMethodViewSet,
    ProductTestTemplateView,
)

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("ports", PortViewSet, basename="port")
router.register("locations", LocationViewSet, basename="location")
router.register("incoterms", IncotermViewSet, basename="incoterm")
router.register("uom", UOMViewSet, basename="uom")
router.register("payment-terms", PaymentTermViewSet, basename="paymentterm")
router.register("pre-carriage", PreCarriageByViewSet, basename="precarriageby")
router.register("currencies", CurrencyViewSet, basename="currency")
router.register("banks", BankViewSet, basename="bank")
router.register("organisations", OrganisationViewSet, basename="organisation")
router.register("tc-templates", TCTemplateViewSet, basename="tctemplate")
router.register("type-of-packages", TypeOfPackageViewSet, basename="typeofpackage")
router.register("products", ProductViewSet, basename="product")
router.register("test-parameters", TestParameterViewSet, basename="testparameter")
router.register("test-methods", TestMethodViewSet, basename="testmethod")

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

# Nested grade routes under /products/{product_pk}/grades/
product_grade_patterns = [
    path(
        "products/<int:product_pk>/grades/",
        ProductGradeViewSet.as_view({"get": "list", "post": "create"}),
        name="product-grade-list",
    ),
    path(
        "products/<int:product_pk>/grades/<int:pk>/",
        ProductGradeViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="product-grade-detail",
    ),
]

# Test template route: /product-grades/{product_grade_pk}/test-template/
test_template_patterns = [
    path(
        "product-grades/<int:product_grade_pk>/test-template/",
        ProductTestTemplateView.as_view(),
        name="product-grade-test-template",
    ),
]

urlpatterns = router.urls + address_patterns + product_grade_patterns + test_template_patterns
