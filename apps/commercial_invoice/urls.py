from rest_framework.routers import DefaultRouter

from .views import CommercialInvoiceLineItemViewSet, CommercialInvoiceViewSet

router = DefaultRouter()
router.register(r"commercial-invoices", CommercialInvoiceViewSet, basename="commercial-invoice")
router.register(r"ci-line-items", CommercialInvoiceLineItemViewSet, basename="ci-line-item")

urlpatterns = router.urls
