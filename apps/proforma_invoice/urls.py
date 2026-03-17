from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ChargeDetailView,
    ChargeListCreateView,
    LineItemDetailView,
    LineItemListCreateView,
    ProformaInvoiceViewSet,
)

router = DefaultRouter()
router.register(r"", ProformaInvoiceViewSet, basename="proforma-invoice")

# Nested sub-resource URLs (line items + charges)
nested_urlpatterns = [
    path("<int:pi_id>/line-items/", LineItemListCreateView.as_view(), name="pi-line-item-list"),
    path("<int:pi_id>/line-items/<int:lid>/", LineItemDetailView.as_view(), name="pi-line-item-detail"),
    path("<int:pi_id>/charges/", ChargeListCreateView.as_view(), name="pi-charge-list"),
    path("<int:pi_id>/charges/<int:cid>/", ChargeDetailView.as_view(), name="pi-charge-detail"),
]

urlpatterns = router.urls + nested_urlpatterns
