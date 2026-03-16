from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet, IncotermViewSet, LocationViewSet,
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

urlpatterns = router.urls
