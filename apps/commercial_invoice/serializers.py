"""
Serializers for CommercialInvoice and CommercialInvoiceLineItem.

CommercialInvoice is created and workflow-transitioned via the PackingList endpoints.
Direct writes are limited to financial fields (fob_rate, freight, insurance, lc_details,
bank) via PATCH on the CI, and rate_usd / packages_kind on individual line items.
"""

from rest_framework import serializers

from .models import CommercialInvoice, CommercialInvoiceLineItem


# ---- Line item serializer ---------------------------------------------------

class CommercialInvoiceLineItemSerializer(serializers.ModelSerializer):
    uom_abbr = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommercialInvoiceLineItem
        fields = [
            "id", "ci",
            "item_code", "description", "hsn_code", "packages_kind",
            "uom", "uom_abbr",
            "total_quantity", "rate_usd", "amount_usd",
        ]
        read_only_fields = [
            "id", "ci",
            "item_code", "description", "hsn_code",
            "uom", "uom_abbr", "total_quantity", "amount_usd",
        ]

    def get_uom_abbr(self, obj):
        return obj.uom.abbreviation if obj.uom_id else None

    def validate_rate_usd(self, value):
        if value < 0:
            raise serializers.ValidationError("Rate must be zero or greater.")
        # Reject more than 2 decimal places
        if value.as_tuple().exponent < -2:
            raise serializers.ValidationError("Rate can have at most 2 decimal places.")
        return value


# ---- CommercialInvoice serializer -------------------------------------------

class CommercialInvoiceSerializer(serializers.ModelSerializer):
    line_items = CommercialInvoiceLineItemSerializer(many=True, read_only=True)

    # Display labels
    pl_number_display = serializers.SerializerMethodField()
    bank_display = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    signed_copy_url = serializers.SerializerMethodField()

    class Meta:
        model = CommercialInvoice
        fields = [
            "id", "ci_number", "ci_date", "status",
            "packing_list", "pl_number_display",
            "bank", "bank_display", "bank_details",
            "fob_rate", "freight", "insurance", "lc_details",
            "created_by", "created_at", "updated_at",
            # Signed copy (FR-08.4)
            "signed_copy_url",
            "line_items",
        ]
        read_only_fields = [
            "id", "ci_number", "status",
            "packing_list", "pl_number_display",
            "created_by", "created_at", "updated_at",
        ]

    def get_pl_number_display(self, obj):
        return obj.packing_list.pl_number if obj.packing_list_id else None

    def get_bank_display(self, obj):
        if obj.bank_id:
            return f"{obj.bank.bank_name} – {obj.bank.beneficiary_name}"
        return None

    def get_signed_copy_url(self, obj):
        """Return the absolute URL to the signed copy file, or None if not uploaded."""
        if not obj.signed_copy:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.signed_copy.url)
        return obj.signed_copy.url

    def get_bank_details(self, obj):
        """Full bank details for the Bank & Payment tab on the detail page."""
        if not obj.bank_id:
            return None
        b = obj.bank
        return {
            "beneficiary_name": b.beneficiary_name,
            "bank_name": b.bank_name,
            "branch_name": b.branch_name,
            "branch_address": b.branch_address,
            "account_number": b.account_number,
            "routing_number": b.routing_number,
            "swift_code": b.swift_code,
            "iban": b.iban,
            "intermediary_bank_name": b.intermediary_bank_name,
            "intermediary_account_number": b.intermediary_account_number,
            "intermediary_swift_code": b.intermediary_swift_code,
            "intermediary_currency": (
                b.intermediary_currency.code
                if b.intermediary_currency_id else None
            ),
        }


class CommercialInvoiceUpdateSerializer(serializers.ModelSerializer):
    """Allows updating financial fields on a CI (bank, rates, lc_details)."""

    class Meta:
        model = CommercialInvoice
        fields = ["ci_date", "bank", "fob_rate", "freight", "insurance", "lc_details"]
