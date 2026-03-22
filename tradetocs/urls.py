from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.accounts.urls import auth_urlpatterns, user_urlpatterns
from apps.proforma_invoice.report_views import CommoditySalesReportView, ConsigneeBusinessSummaryView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include(auth_urlpatterns)),
    path("api/v1/users/", include(user_urlpatterns)),
    path("api/v1/master-data/", include("apps.master_data.urls")),
    path("api/v1/proforma-invoices/", include("apps.proforma_invoice.urls")),
    path("api/v1/", include("apps.packing_list.urls")),
    path("api/v1/", include("apps.commercial_invoice.urls")),
    path("api/v1/", include("apps.purchase_order.urls")),
    # Report endpoints
    path("api/v1/reports/commodity-sales/", CommoditySalesReportView.as_view(), name="report-commodity-sales"),
    path("api/v1/reports/consignee-business-summary/", ConsigneeBusinessSummaryView.as_view(), name="report-consignee-business-summary"),
]

# Serve uploaded files in development (Django handles this; in production use nginx/CDN).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
