from django.urls import path

from .views import ManualEditsListView, ManualEditUploadView

urlpatterns = [
    path("manual-edits/", ManualEditsListView.as_view(), name="manual-edits-list"),
    path(
        "manual-edits/<str:document_type>/<int:document_id>/upload/",
        ManualEditUploadView.as_view(),
        name="manual-edits-upload",
    ),
]
