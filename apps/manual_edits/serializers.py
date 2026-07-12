from rest_framework import serializers


class ManualEditsRowSerializer(serializers.Serializer):
    """Serializes one row produced by services.list_all_documents()."""
    document_type = serializers.CharField()
    document_id = serializers.IntegerField()
    document_number = serializers.CharField()
    exporter_name = serializers.CharField()
    importer_name = serializers.CharField()
    vendor_name = serializers.CharField()
    first_generated_at = serializers.DateTimeField(allow_null=True)
    has_manual_edit = serializers.BooleanField()
    edit_comment = serializers.CharField(allow_blank=True)
    edited_at = serializers.DateTimeField(allow_null=True)
    edited_by_name = serializers.CharField(allow_blank=True)
    edited_word_file = serializers.SerializerMethodField()
    edited_pdf_file = serializers.SerializerMethodField()
    download_pdf_path = serializers.CharField(allow_null=True)
    download_word_path = serializers.CharField(allow_null=True)

    def _file_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(file_field.url) if request else file_field.url

    def get_edited_word_file(self, row):
        return self._file_url(row["edited_word_file"])

    def get_edited_pdf_file(self, row):
        return self._file_url(row["edited_pdf_file"])


class ManualEditUploadSerializer(serializers.Serializer):
    """
    Validates a manual-edit upload. Rule #7 spirit: the reason comment is
    mandatory. At least one replacement file (Word or PDF) must be provided.
    """
    comment = serializers.CharField(allow_blank=False, trim_whitespace=True)
    word_file = serializers.FileField(required=False)
    pdf_file = serializers.FileField(required=False)

    def validate(self, attrs):
        if not attrs.get("word_file") and not attrs.get("pdf_file"):
            raise serializers.ValidationError(
                {"detail": "Upload at least a Word file or a PDF file."}
            )
        return attrs
