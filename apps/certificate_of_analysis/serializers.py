from rest_framework import serializers

from apps.workflow.models import AuditLog

from .models import CertificateOfAnalysis, COAParameter


class COAParameterSerializer(serializers.ModelSerializer):
    unit_abbreviation = serializers.CharField(source="unit.abbreviation", read_only=True, default=None)
    parameter_name = serializers.CharField(source="parameter.name", read_only=True, default=None)
    test_method_code = serializers.CharField(source="test_method.code", read_only=True, default=None)

    class Meta:
        model = COAParameter
        fields = [
            "id", "s_no",
            "parameter", "parameter_name",
            "unit", "unit_abbreviation",
            "spec_type",
            "spec_min", "spec_max", "spec_description",
            "result_value", "result_text",
            "test_method", "test_method_code",
        ]

    def validate(self, data):
        spec_type = data.get("spec_type")
        if spec_type == "QUANTITATIVE":
            if data.get("spec_min") is None and data.get("spec_max") is None:
                raise serializers.ValidationError(
                    {"spec": "Quantitative rows require at least one of spec_min or spec_max."}
                )
            if data.get("result_value") is None:
                raise serializers.ValidationError(
                    {"result_value": "Result value is required for quantitative rows."}
                )
        elif spec_type == "QUALITATIVE":
            if not data.get("spec_description", "").strip():
                raise serializers.ValidationError(
                    {"spec_description": "Spec description is required for qualitative rows."}
                )
            if not data.get("result_text", "").strip():
                raise serializers.ValidationError(
                    {"result_text": "Result text is required for qualitative rows."}
                )
        return data


class CertificateOfAnalysisSerializer(serializers.ModelSerializer):
    parameters = COAParameterSerializer(many=True)

    # Read-only display fields
    product_name = serializers.CharField(source="product_grade.product.name", read_only=True)
    grade = serializers.CharField(source="product_grade.grade", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    package_uom_abbreviation = serializers.CharField(source="package_uom.abbreviation", read_only=True)
    package_type_name = serializers.CharField(source="package_type.name", read_only=True)
    footer_organisation_name = serializers.CharField(source="footer_organisation.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CertificateOfAnalysis
        fields = [
            "id", "coa_number",
            "product_grade", "product_name", "grade",
            "customer", "customer_name",
            "batch_number",
            "package_count", "package_volume", "package_uom", "package_uom_abbreviation",
            "package_type", "package_type_name",
            "date_of_despatch",
            "date_of_manufacture", "date_of_retest",
            "date_time_of_sampling", "date_time_of_analysis",
            "analyst_name", "qc_incharge_name",
            "footer_organisation", "footer_organisation_name",
            "status",
            "created_by", "created_by_name",
            "created_at", "updated_at",
            "parameters",
        ]
        read_only_fields = ["id", "coa_number", "status", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        # User model exposes `full_name` as a property, not Django's `get_full_name()`.
        return obj.created_by.full_name or obj.created_by.email

    def validate(self, data):
        # Date validation rules
        dom = data.get("date_of_manufacture")
        dor = data.get("date_of_retest")
        if dom and dor and dor < dom:
            raise serializers.ValidationError(
                {"date_of_retest": "Date of retest must be on or after date of manufacture."}
            )
        dts = data.get("date_time_of_sampling")
        dta = data.get("date_time_of_analysis")
        if dts and dta and dta < dts:
            raise serializers.ValidationError(
                {"date_time_of_analysis": "Date and time of analysis must be on or after date and time of sampling."}
            )
        return data

    def create(self, validated_data):
        from .services import generate_document_number
        parameters_data = validated_data.pop("parameters")
        coa = CertificateOfAnalysis.objects.create(
            coa_number=generate_document_number(),
            **validated_data,
        )
        for param_data in parameters_data:
            COAParameter.objects.create(coa=coa, **param_data)
        return coa

    def update(self, instance, validated_data):
        parameters_data = validated_data.pop("parameters", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if parameters_data is not None:
            # Replace all parameters wholesale on update
            instance.parameters.all().delete()
            for param_data in parameters_data:
                COAParameter.objects.create(coa=instance, **param_data)
        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "from_status", "to_status",
            "comment", "performed_by", "performed_by_name", "performed_at",
        ]

    def get_performed_by_name(self, obj):
        # User model exposes `full_name` as a property, not Django's `get_full_name()`.
        return obj.performed_by.full_name or obj.performed_by.email
