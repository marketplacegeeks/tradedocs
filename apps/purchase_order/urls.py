from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LineItemDetailView, LineItemListCreateView, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchase-order")

# Nested line item sub-resource URLs
nested_urlpatterns = [
    path(
        "purchase-orders/<int:po_id>/line-items/",
        LineItemListCreateView.as_view(),
        name="po-line-item-list",
    ),
    path(
        "purchase-orders/<int:po_id>/line-items/<int:lid>/",
        LineItemDetailView.as_view(),
        name="po-line-item-detail",
    ),
]

urlpatterns = router.urls + nested_urlpatterns
