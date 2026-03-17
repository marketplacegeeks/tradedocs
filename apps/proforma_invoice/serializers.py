"""
Serializers for ProformaInvoice, ProformaInvoiceLineItem, ProformaInvoiceCharge.

Constraint #18: Serializers are state-aware — content fields become read_only when
the document is not in DRAFT or REWORK.
"""

import re
from datetime import date
from decimal import Decimal

from rest_framework import serializers

from apps.workflow.constants import EDITABLE_STATES
from .models import ProformaInvoice, ProformaInvoiceCharge, ProformaInvoiceLineItem
from .services import generate_document_number


# ---- Incoterms cost-field visibility map (FR-09.7.3) -----------------------
# Maps incoterm code → set of cost fields the seller bears (and must fill in).
# EXW = no cost fields; any unknown incoterm → no cost fields.
INCOTERM_SELLER_FIELDS = {
    "EXW": set(),
    "FCA": {"freight"},
    "FOB": {"freight"},
    "CFR": {"freight", "insurance_amount"},
    "CIF": {"freight", "insurance_amount"},
    "CPT": {"freight", "insurance_amount"},
    "CIP": {"freight", "insurance_amount"},
    "DAP": {"freight", "insurance_amount"},
    "DPU": {"freight", "insurance_amount", "destination_charges"},
    "DDP": {"freight", "insurance_amount", "import_duty", "destination_charges"},
}

# Incoterms that show only FOB Value (no additional cost fields)
FOB_ONLY_INCOTERMS = {"FCA", "FOB"}


# ---- Line item serializer --------------------------------------------------

class ProformaInvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoiceLineItem
        fields = [
            "id", "hsn_code", "item_code", "description",
            "quantity", "uom", "rate_usd", "amount_usd",
        ]
        read_only_fields = ["id", "amount_usd"]

    def validate_hsn_code(self, value):
        if value and not re.match(r"^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?$", value):
            raise serializers.ValidationError(
                "HSN code must be 2, 4, 6, or 8 digits (e.g. 09, 0901, 090111)."
            )
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_rate_usd(self, value):
        if value < 0:
            raise serializers.ValidationError("Rate must be zero or greater.")
        return value


# ---- Charge serializer -----------------------------------------------------

class ProformaInvoiceChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoiceCharge
        fields = ["id", "description", "amount_usd"]
        read_only_fields = ["id"]

    def validate_amount_usd(self, value):
        if value < 0:
            raise serializers.ValidationError("Charge amount must be zero or greater.")
        return value


# ---- Main PI serializer ----------------------------------------------------

class ProformaInvoiceSerializer(serializers.ModelSerializer):
    """
    Handles both create and update for ProformaInvoice.

    On read: includes nested line_items, charges, and computed totals.
    On write: enforces required fields and validates cost breakdown per FR-09.7.8.
    Constraint #18: content fields are set read_only when status is not DRAFT/REWORK.
    """
    line_items = ProformaInvoiceLineItemSerializer(many=True, read_only=True)
    charges = ProformaInvoiceChargeSerializer(many=True, read_only=True)

    # Computed fields returned in responses (not stored on model)
    line_items_total = serializers.SerializerMethodField()
    charges_total = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()
    invoice_total = serializers.SerializerMethodField()

    # Nested read helpers so the frontend gets the incoterm code alongside the FK id
    incoterms_code = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    # Returns the full URL to the signed copy file, or null if none uploaded.
    signed_copy_url = serializers.SerializerMethodField()

    class Meta:
        model = ProformaInvoice
        extra_kwargs = {
            # pi_date defaults to today when not supplied (set in create())
            "pi_date": {"required": False},
        }
        fields = [
            # Header
            "id", "pi_number", "pi_date",
            "exporter", "consignee", "buyer",
            "buyer_order_no", "buyer_order_date", "other_references",
            "country_of_origin", "country_of_final_destination",
            # Shipping
            "pre_carriage_by", "place_of_receipt", "vessel_flight_no",
            "port_of_loading", "port_of_discharge", "final_destination",
            # Payment & Terms
            "payment_terms", "incoterms", "incoterms_code", "bank",
            "validity_for_acceptance", "validity_for_shipment",
            "partial_shipment", "transshipment",
            # T&C
            "tc_template", "tc_content",
            # Cost breakdown (FR-09.7)
            "freight", "insurance_amount", "import_duty", "destination_charges",
            # Computed totals (read-only, returned in responses)
            "line_items_total", "charges_total", "grand_total", "invoice_total",
            # Nested
            "line_items", "charges",
            # Metadata
            "status", "created_by", "created_by_name", "created_at", "updated_at",
            # Signed copy (FR-08.4)
            "signed_copy_url",
        ]
        read_only_fields = [
            "id", "pi_number", "status",
            "created_by", "created_by_name", "created_at", "updated_at",
            "line_items", "charges",
            "line_items_total", "charges_total", "grand_total", "invoice_total",
            "incoterms_code",
            "signed_copy_url",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Constraint #18: make all content fields read-only when not in an editable state.
        instance = kwargs.get("instance")
        if instance and instance.status not in EDITABLE_STATES:
            content_fields = [
                "pi_date", "exporter", "consignee", "buyer",
                "buyer_order_no", "buyer_order_date", "other_references",
                "country_of_origin", "country_of_final_destination",
                "pre_carriage_by", "place_of_receipt", "vessel_flight_no",
                "port_of_loading", "port_of_discharge", "final_destination",
                "payment_terms", "incoterms", "bank",
                "validity_for_acceptance", "validity_for_shipment",
                "partial_shipment", "transshipment",
                "tc_template", "tc_content",
                "freight", "insurance_amount", "import_duty", "destination_charges",
            ]
            for field_name in content_fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = True

    def validate(self, attrs):
        # Determine incoterm code for validation (from instance or incoming data)
        incoterms_obj = attrs.get("incoterms") or (self.instance and self.instance.incoterms)
        incoterm_code = incoterms_obj.code if incoterms_obj else None
        seller_fields = INCOTERM_SELLER_FIELDS.get(incoterm_code, set())

        # FR-09.7.8: If a cost field is visible (seller-borne), it must not be blank.
        # Applies only to the fields that are being submitted in this request.
        cost_field_names = {
            "freight": "Freight",
            "insurance_amount": "Insurance Amount",
            "import_duty": "Import Duty / Taxes",
            "destination_charges": "Destination Charges",
        }
        for field_key, label in cost_field_names.items():
            if field_key in seller_fields and field_key in attrs:
                if attrs[field_key] is None:
                    raise serializers.ValidationError(
                        {field_key: f"{label} is required for {incoterm_code}. Enter 0 if not applicable."}
                    )

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("pi_date", date.today())
        # Auto-assign the logged-in user as creator
        validated_data["created_by"] = self.context["request"].user
        # Generate a unique PI number (constraint #16)
        validated_data["pi_number"] = generate_document_number()
        # Snapshot the T&C template body if a template was selected (FR-09.4)
        tc_template = validated_data.get("tc_template")
        if tc_template and not validated_data.get("tc_content"):
            validated_data["tc_content"] = tc_template.body
        return super().create(validated_data)

    # ---- Computed fields ------------------------------------------------

    def get_line_items_total(self, obj):
        """Sum of all line item amounts."""
        total = sum(
            (item.amount_usd for item in obj.line_items.all()),
            Decimal("0.00"),
        )
        return str(total)

    def get_charges_total(self, obj):
        """Sum of all additional charge amounts."""
        total = sum(
            (charge.amount_usd for charge in obj.charges.all()),
            Decimal("0.00"),
        )
        return str(total)

    def get_grand_total(self, obj):
        """Grand Total = line items total + charges total."""
        line_total = sum(
            (item.amount_usd for item in obj.line_items.all()),
            Decimal("0.00"),
        )
        charge_total = sum(
            (charge.amount_usd for charge in obj.charges.all()),
            Decimal("0.00"),
        )
        return str(line_total + charge_total)

    def get_invoice_total(self, obj):
        """
        Invoice Total = FOB Value (= grand total) + seller-borne cost fields.
        FR-09.7.4: Only visible fields (per incoterm) are included.
        """
        incoterm_code = obj.incoterms.code if obj.incoterms else None
        seller_fields = INCOTERM_SELLER_FIELDS.get(incoterm_code, set())

        line_total = sum(
            (item.amount_usd for item in obj.line_items.all()),
            Decimal("0.00"),
        )
        charge_total = sum(
            (charge.amount_usd for charge in obj.charges.all()),
            Decimal("0.00"),
        )
        grand_total = line_total + charge_total

        # EXW and no-incoterm: Invoice Total = Grand Total
        if not incoterm_code or incoterm_code == "EXW":
            return str(grand_total)

        # FCA / FOB: FOB Value only
        if incoterm_code in FOB_ONLY_INCOTERMS:
            return str(grand_total)

        total = grand_total
        if "freight" in seller_fields and obj.freight is not None:
            total += obj.freight
        if "insurance_amount" in seller_fields and obj.insurance_amount is not None:
            total += obj.insurance_amount
        if "import_duty" in seller_fields and obj.import_duty is not None:
            total += obj.import_duty
        if "destination_charges" in seller_fields and obj.destination_charges is not None:
            total += obj.destination_charges

        return str(total)

    def get_incoterms_code(self, obj):
        return obj.incoterms.code if obj.incoterms else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None

    def get_signed_copy_url(self, obj):
        """Return the absolute URL to the signed copy file, or None if not uploaded."""
        if not obj.signed_copy:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.signed_copy.url)
        return obj.signed_copy.url


# ---- Audit log serializer (read-only) -------------------------------------

class AuditLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.CharField()
    from_status = serializers.CharField()
    to_status = serializers.CharField()
    comment = serializers.CharField()
    performed_by_name = serializers.SerializerMethodField()
    performed_at = serializers.DateTimeField()

    def get_performed_by_name(self, obj):
        return obj.performed_by.full_name if obj.performed_by else None
