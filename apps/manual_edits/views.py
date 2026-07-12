"""
Views for the Manual Edits page.
Rule #10: All views explicitly declare permission_classes.
"""
from django.http import Http404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAnyRole

from .models import DocumentEditTracking
from .serializers import ManualEditsRowSerializer, ManualEditUploadSerializer
from .services import DOCUMENT_MODELS, list_all_documents


class ManualEditsListView(APIView):
    """GET /api/v1/manual-edits/ — every document across all 5 doc types."""
    permission_classes = [IsAuthenticated, IsAnyRole]

    def get(self, request):
        rows = list_all_documents()
        serializer = ManualEditsRowSerializer(rows, many=True, context={"request": request})
        return Response(serializer.data)


class ManualEditUploadView(APIView):
    """
    POST /api/v1/manual-edits/{document_type}/{document_id}/upload/
    Accepts multipart/form-data: comment (required), word_file and/or pdf_file.
    Overwrites any previously uploaded manual-edit files for this document.
    """
    permission_classes = [IsAuthenticated, IsAnyRole]

    def post(self, request, document_type, document_id):
        if document_type not in DOCUMENT_MODELS:
            raise Http404(f"Unknown document type '{document_type}'.")

        model, number_field = DOCUMENT_MODELS[document_type]
        try:
            document = model.objects.get(pk=document_id)
        except model.DoesNotExist:
            raise Http404(f"No {document_type} with id {document_id}.")

        serializer = ManualEditUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tracking, _ = DocumentEditTracking.objects.get_or_create(
            document_type=document_type,
            document_id=document_id,
            defaults={"document_number": getattr(document, number_field)},
        )
        tracking.document_number = getattr(document, number_field)

        if data.get("word_file"):
            if tracking.edited_word_file:
                tracking.edited_word_file.delete(save=False)
            tracking.edited_word_file = data["word_file"]
        if data.get("pdf_file"):
            if tracking.edited_pdf_file:
                tracking.edited_pdf_file.delete(save=False)
            tracking.edited_pdf_file = data["pdf_file"]

        tracking.edit_comment = data["comment"]
        tracking.edited_by = request.user
        tracking.edited_at = timezone.now()
        tracking.save()

        row = next(
            r for r in list_all_documents()
            if r["document_type"] == document_type and r["document_id"] == document_id
        )
        return Response(ManualEditsRowSerializer(row, context={"request": request}).data)
