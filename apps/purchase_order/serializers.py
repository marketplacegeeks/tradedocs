"""
Serializers for PurchaseOrder and PurchaseOrderLineItem.

Constraint #18: Serializers are state-aware — content fields become read_only when
the document is not in DRAFT or REWORK.
"""

from datetime import date
from decimal import Decimal

from rest_framework import serializers

from apps.workflow.constants import EDITABLE_STATES
from apps.workflow.models import AuditLog

from .models import PurchaseOrder, PurchaseOrderLineItem


# ---- AuditLog serializer (shared with views) --------------------------------

class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source="performed_by.get_full_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "document_type", "document_number",
            "action", "from_status", "to_status",
            "comment", "performed_by_name", "created_at",
        ]


# ---- Line item serializer ---------------------------------------------------

class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    """
    All computed fields (taxable_amount, igst_amount, etc.) are read_only.
    They are recalculated on every model.save() call.
    """

    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            "id",
            "description",
            "item_code",
            "hsn_code",
            "manufacturer",
            "uom",
            "quantity",
            "packaging_description",
            "unit_price",
            # Computed — read_only
            "taxable_amount",
            "igst_percent",
            "igst_amount",
            "cgst_percent",
            "cgst_amount",
            "sgst_percent",
            "sgst_amount",
            "total_tax",
            "total",
            "sort_order",
        ]
        read_only_fields = [
            "id",
            "taxable_amount",
            "igst_amount",
            "cgst_amount",
            "sgst_amount",
            "total_tax",
            "total",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price must be zero or greater.")
        return value


# ---- Main PO serializer -----------------------------------------------------

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Handles create and update for PurchaseOrder.

    Constraint #18: content fields are read_only when status is not DRAFT or REWORK.

    List mode (nested=False): returns summary fields + computed total.
    Detail mode (nested=True): also returns nested line_items.
    """

    # Nested read-only line items (detail mode)
    line_items = PurchaseOrderLineItemSerializer(many=True, read_only=True)

    # Computed total (sum of all line item totals) — not stored on the header
    total = serializers.SerializerMethodField()

    # Human-readable name fields for FK display
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", allow_null=True, read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    internal_contact_name = serializers.CharField(source="internal_contact.get_full_name", read_only=True)
    internal_contact_email = serializers.EmailField(source="internal_contact.email", read_only=True)
    internal_contact_phone = serializers.SerializerMethodField()
    payment_terms_name = serializers.CharField(source="payment_terms.name", allow_null=True, read_only=True)
    country_of_origin_name = serializers.CharField(source="country_of_origin.name", allow_null=True, read_only=True)
    bank_name = serializers.SerializerMethodField()
    delivery_address_detail = serializers.SerializerMethodField()

    # Report aggregate fields (R-06)
    line_item_count = serializers.SerializerMethodField()
    total_taxable = serializers.SerializerMethodField()
    total_igst = serializers.SerializerMethodField()
    total_cgst = serializers.SerializerMethodField()
    total_sgst = serializers.SerializerMethodField()
    total_tax_amount = serializers.SerializerMethodField()
    delivery_city_country = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "po_date",
            "customer_no",
            "vendor",
            "vendor_name",
            "buyer",
            "buyer_name",
            "internal_contact",
            "internal_contact_name",
            "internal_contact_email",
            "internal_contact_phone",
            "delivery_address",
            "bank",
            "currency",
            "currency_code",
            "payment_terms",
            "country_of_origin",
            "transaction_type",
            "time_of_delivery",
            "tc_template",
            "tc_content",
            "line_item_remarks",
            "remarks",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "line_items",
            "total",
            "payment_terms_name",
            "country_of_origin_name",
            "bank_name",
            "delivery_address_detail",
            # Report aggregate fields
            "line_item_count",
            "total_taxable",
            "total_igst",
            "total_cgst",
            "total_sgst",
            "total_tax_amount",
            "delivery_city_country",
        ]
        read_only_fields = ["id", "po_number", "status", "created_by", "created_at", "updated_at"]

    def get_total(self, obj):
        """Sum of all line item totals."""
        return sum(item.total for item in obj.line_items.all())

    def get_line_item_count(self, obj):
        return obj.line_items.count()

    def get_total_taxable(self, obj):
        return sum(item.taxable_amount for item in obj.line_items.all())

    def get_total_igst(self, obj):
        return sum(item.igst_amount or Decimal("0") for item in obj.line_items.all())

    def get_total_cgst(self, obj):
        return sum(item.cgst_amount or Decimal("0") for item in obj.line_items.all())

    def get_total_sgst(self, obj):
        return sum(item.sgst_amount or Decimal("0") for item in obj.line_items.all())

    def get_total_tax_amount(self, obj):
        return sum(item.total_tax for item in obj.line_items.all())

    def get_delivery_city_country(self, obj):
        """Short form delivery address: 'Mumbai, India'."""
        addr = obj.delivery_address
        if not addr:
            return ""
        parts = filter(None, [addr.city, getattr(addr.country, "name", None)])
        return ", ".join(parts)

    def get_bank_name(self, obj):
        if not obj.bank:
            return None
        return obj.bank.bank_name

    def get_delivery_address_detail(self, obj):
        """Return a formatted single-line address string for the delivery address."""
        addr = obj.delivery_address
        if not addr:
            return ""
        parts = [p for p in [addr.line1, addr.line2] if p]
        city_state = ", ".join(filter(None, [addr.city, addr.state]))
        if city_state:
            parts.append(city_state)
        if addr.pin:
            parts.append(addr.pin)
        if getattr(addr, "country", None):
            parts.append(addr.country.name)
        return ", ".join(parts)

    def get_internal_contact_phone(self, obj):
        """Return formatted phone string or empty string."""
        user = obj.internal_contact
        if user.phone_country_code and user.phone_number:
            return f"{user.phone_country_code} {user.phone_number}"
        return ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Constraint #18: make content fields read_only when document is not editable.
        # Guard with isinstance — in list mode DRF passes the full queryset as instance.
        instance = self.instance
        if isinstance(instance, PurchaseOrder) and instance.status not in EDITABLE_STATES:
            editable_fields = ["po_number", "status", "created_by", "created_at", "updated_at"]
            for field_name in self.fields:
                if field_name not in editable_fields:
                    self.fields[field_name].read_only = True

    def validate(self, attrs):
        request = self.context.get("request")

        # Validate delivery_address belongs to the buyer (if set) or the vendor, and is DELIVERY type
        vendor = attrs.get("vendor", getattr(self.instance, "vendor", None))
        buyer = attrs.get("buyer", getattr(self.instance, "buyer", None))
        delivery_address = attrs.get("delivery_address", getattr(self.instance, "delivery_address", None))

        if delivery_address:
            if delivery_address.address_type != "DELIVERY":
                raise serializers.ValidationError(
                    {"delivery_address": "Selected address must be a Delivery address type."}
                )
            # When a buyer is selected, delivery address must belong to the buyer.
            # Otherwise it must belong to the vendor.
            owner = buyer if buyer else vendor
            if owner and delivery_address.organisation_id != owner.pk:
                owner_label = "buyer" if buyer else "vendor"
                raise serializers.ValidationError(
                    {"delivery_address": f"Delivery address must belong to the selected {owner_label}."}
                )

        # Default po_date to today if not provided on creation
        if not self.instance and "po_date" not in attrs:
            attrs["po_date"] = date.today()

        return attrs

    def create(self, validated_data):
        from .services import generate_document_number
        validated_data["po_number"] = generate_document_number()
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
