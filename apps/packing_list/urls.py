from rest_framework.routers import DefaultRouter

from .views import ContainerItemViewSet, ContainerViewSet, PackingListViewSet

router = DefaultRouter()
router.register(r"packing-lists", PackingListViewSet, basename="packing-list")
router.register(r"containers", ContainerViewSet, basename="container")
router.register(r"container-items", ContainerItemViewSet, basename="container-item")

urlpatterns = router.urls
