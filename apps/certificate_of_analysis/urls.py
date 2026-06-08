from rest_framework.routers import DefaultRouter
from .views import CertificateOfAnalysisViewSet

router = DefaultRouter()
router.register("coas", CertificateOfAnalysisViewSet, basename="coa")

urlpatterns = router.urls
