"""
Serializers for PackingList, Container, ContainerItem.

Constraint #18: Serializers are state-aware — fields become read_only when the
document is not in DRAFT or REWORK.
"""

import re
from datetime import date
from decimal import Decimal

from rest_framework import serializers

from apps.workflow.constants import EDITABLE_STATES
from .models import Container, ContainerItem, PackingList
from .services import generate_document_number as generate_pl_number


HSN_REGEX = re.compile(r"^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?)?$")


# ---- ContainerItem serializer -----------------------------------------------

class ContainerItemSerializer(serializers.ModelSerializer):
    # Expose UOM abbreviation and package type name for display without extra requests.
    uom_abbr = serializers.SerializerMethodField(read_only=True)
    type_of_package_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContainerItem
        fields = [
            "id", "container",
            "hsn_code", "item_code", "description", "batch_details",
            "uom", "uom_abbr",
            "type_of_package", "type_of_package_name",
            "no_of_packages", "qty_per_package", "weight_per_unit_packaging",
            "net_material_weight", "item_gross_weight",
        ]
        read_only_fields = ["id", "net_material_weight", "item_gross_weight", "uom_abbr", "type_of_package_name"]

    def get_uom_abbr(self, obj):
        return obj.uom.abbreviation if obj.uom_id else None

    def get_type_of_package_name(self, obj):
        return obj.type_of_package.name if obj.type_of_package_id else None

    def validate_hsn_code(self, value):
        if value and not HSN_REGEX.match(value):
            raise serializers.ValidationError(
                "HSN code must be 2, 4, 6, 8, or 10 digits (e.g. 09, 0901, 090111, 0901111100)."
            )
        return value

    def validate_no_of_packages(self, value):
        if value <= 0:
            raise serializers.ValidationError("Number of packages must be greater than zero.")
        return value

    def validate_qty_per_package(self, value):
        if value < 0:
            raise serializers.ValidationError("Qty per package must be zero or greater.")
        return value

    def validate_weight_per_unit_packaging(self, value):
        if value < 0:
            raise serializers.ValidationError("Weight per unit packaging must be zero or greater.")
        return value


# ---- Container serializer ---------------------------------------------------

class ContainerSerializer(serializers.ModelSerializer):
    items = ContainerItemSerializer(many=True, read_only=True)

    class Meta:
        model = Container
        fields = [
            "id", "packing_list",
            "container_ref", "marks_numbers", "seal_number",
            "tare_weight", "gross_weight",
            "items",
        ]
        read_only_fields = ["id", "gross_weight", "items"]

    def validate_tare_weight(self, value):
        if value < 0:
            raise serializers.ValidationError("Tare weight must be zero or greater.")
        return value


# ---- PackingList serializer -------------------------------------------------

class PackingListSerializer(serializers.ModelSerializer):
    """
    Read serializer — returns full PL with nested containers + CI summary fields.
    """
    containers = ContainerSerializer(many=True, read_only=True)

    # Nested CI fields (read-only; CI is managed via the CI endpoints)
    ci_number = serializers.SerializerMethodField()
    ci_id = serializers.SerializerMethodField()
    ci_status = serializers.SerializerMethodField()
    ci_date = serializers.SerializerMethodField()
    bank_id = serializers.SerializerMethodField()
    bank_display = serializers.SerializerMethodField()
    fob_rate = serializers.SerializerMethodField()
    freight = serializers.SerializerMethodField()
    insurance = serializers.SerializerMethodField()
    lc_details = serializers.SerializerMethodField()
    # R-03 report computed fields
    ci_total = serializers.SerializerMethodField()
    fob_value = serializers.SerializerMethodField()
    incoterms_code = serializers.SerializerMethodField()

    # Display labels for FK fields
    exporter_name = serializers.SerializerMethodField()
    consignee_name = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    notify_party_name = serializers.SerializerMethodField()
    pi_number_display = serializers.SerializerMethodField()
    incoterms_display = serializers.SerializerMethodField()
    payment_terms_display = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    signed_copy_url = serializers.SerializerMethodField()

    # Display names for shipping / geography FK fields (avoids raw IDs on the detail page)
    pre_carriage_by_name = serializers.SerializerMethodField()
    place_of_receipt_name = serializers.SerializerMethodField()
    place_of_receipt_by_pre_carrier_name = serializers.SerializerMethodField()
    port_of_loading_name = serializers.SerializerMethodField()
    port_of_discharge_name = serializers.SerializerMethodField()
    final_destination_name = serializers.SerializerMethodField()
    country_of_origin_name = serializers.SerializerMethodField()
    country_of_final_destination_name = serializers.SerializerMethodField()

    class Meta:
        model = PackingList
        fields = [
            "id", "pl_number", "pl_date", "status",
            "proforma_invoice", "pi_number_display",
            "exporter", "exporter_name",
            "consignee", "consignee_name",
            "buyer", "buyer_name",
            "notify_party", "notify_party_name",
            # Order references
            "po_number", "po_date",
            "lc_number", "lc_date",
            "bl_number", "bl_date",
            "so_number", "so_date",
            "other_references", "other_references_date",
            "additional_description",
            # Shipping
            "pre_carriage_by",
            "place_of_receipt", "place_of_receipt_by_pre_carrier",
            "vessel_flight_no",
            "port_of_loading", "port_of_discharge", "final_destination",
            # Countries
            "country_of_origin", "country_of_final_destination",
            # Payment & Terms
            "incoterms", "incoterms_display",
            "payment_terms", "payment_terms_display",
            # CI fields (read-only here)
            "ci_id", "ci_number", "ci_status", "ci_date",
            "bank_id", "bank_display",
            "fob_rate", "freight", "insurance", "lc_details",
            # R-03 report computed fields
            "ci_total", "fob_value", "incoterms_code",
            # Shipping display names
            "pre_carriage_by_name",
            "place_of_receipt_name",
            "place_of_receipt_by_pre_carrier_name",
            "port_of_loading_name",
            "port_of_discharge_name",
            "final_destination_name",
            "country_of_origin_name",
            "country_of_final_destination_name",
            # Meta
            "created_by", "created_by_name",
            "created_at", "updated_at",
            # Signed copy (FR-08.4)
            "signed_copy_url",
            # Nested
            "containers",
        ]
        read_only_fields = [
            "id", "pl_number", "status",
            "created_by", "created_at", "updated_at",
        ]

    def _get_ci(self, obj):
        """Helper: return linked CI or None without raising."""
        try:
            return obj.commercial_invoice
        except Exception:
            return None

    def get_ci_number(self, obj):
        ci = self._get_ci(obj)
        return ci.ci_number if ci else None

    def get_ci_id(self, obj):
        ci = self._get_ci(obj)
        return ci.pk if ci else None

    def get_ci_status(self, obj):
        ci = self._get_ci(obj)
        return ci.status if ci else None

    def get_ci_date(self, obj):
        ci = self._get_ci(obj)
        return ci.ci_date if ci else None

    def get_bank_id(self, obj):
        ci = self._get_ci(obj)
        return ci.bank_id if ci else None

    def get_bank_display(self, obj):
        ci = self._get_ci(obj)
        if ci and ci.bank_id:
            b = ci.bank
            return f"{b.bank_name} – {b.beneficiary_name}"
        return None

    def get_fob_rate(self, obj):
        ci = self._get_ci(obj)
        return str(ci.fob_rate) if ci and ci.fob_rate is not None else None

    def get_freight(self, obj):
        ci = self._get_ci(obj)
        return str(ci.freight) if ci and ci.freight is not None else None

    def get_insurance(self, obj):
        ci = self._get_ci(obj)
        return str(ci.insurance) if ci and ci.insurance is not None else None

    def get_lc_details(self, obj):
        ci = self._get_ci(obj)
        return ci.lc_details if ci else ""

    def get_exporter_name(self, obj):
        return obj.exporter.name if obj.exporter_id else None

    def get_consignee_name(self, obj):
        return obj.consignee.name if obj.consignee_id else None

    def get_buyer_name(self, obj):
        return obj.buyer.name if obj.buyer_id else None

    def get_notify_party_name(self, obj):
        return obj.notify_party.name if obj.notify_party_id else None

    def get_pi_number_display(self, obj):
        return obj.proforma_invoice.pi_number if obj.proforma_invoice_id else None

    def get_incoterms_display(self, obj):
        if obj.incoterms_id:
            return f"{obj.incoterms.code} – {obj.incoterms.full_name}"
        return None

    def get_payment_terms_display(self, obj):
        return obj.payment_terms.name if obj.payment_terms_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name or obj.created_by.email

    def get_signed_copy_url(self, obj):
        """Return the absolute URL to the signed copy file, or None if not uploaded."""
        if not obj.signed_copy:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.signed_copy.url)
        return obj.signed_copy.url

    # --- Shipping / geography display names ----------------------------------

    def get_pre_carriage_by_name(self, obj):
        return obj.pre_carriage_by.name if obj.pre_carriage_by_id else None

    def get_place_of_receipt_name(self, obj):
        return obj.place_of_receipt.name if obj.place_of_receipt_id else None

    def get_place_of_receipt_by_pre_carrier_name(self, obj):
        return obj.place_of_receipt_by_pre_carrier.name if obj.place_of_receipt_by_pre_carrier_id else None

    def get_port_of_loading_name(self, obj):
        return obj.port_of_loading.name if obj.port_of_loading_id else None

    def get_port_of_discharge_name(self, obj):
        return obj.port_of_discharge.name if obj.port_of_discharge_id else None

    def get_final_destination_name(self, obj):
        return obj.final_destination.name if obj.final_destination_id else None

    def get_country_of_origin_name(self, obj):
        return obj.country_of_origin.name if obj.country_of_origin_id else None

    def get_country_of_final_destination_name(self, obj):
        return obj.country_of_final_destination.name if obj.country_of_final_destination_id else None

    def get_incoterms_code(self, obj):
        return obj.incoterms.code if obj.incoterms_id else None

    def get_ci_total(self, obj):
        """Sum of all CI line item amounts. Used by the R-03 Shipment Register report."""
        ci = self._get_ci(obj)
        if not ci:
            return None
        total = sum(
            (item.amount_usd for item in ci.line_items.all()),
            Decimal("0.00"),
        )
        return str(total)

    def get_fob_value(self, obj):
        """
        FOB Value = fob_rate × sum of CI line item total_quantity.
        Returns None if no CI, no fob_rate, or incoterm is EXW (no FOB value applies).
        """
        ci = self._get_ci(obj)
        if not ci or ci.fob_rate is None:
            return None
        if obj.incoterms_id and obj.incoterms.code == "EXW":
            return None
        total_qty = sum(
            (item.total_quantity for item in ci.line_items.all()),
            Decimal("0.000"),
        )
        return str((ci.fob_rate * total_qty).quantize(Decimal("0.01")))


class PackingListWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer — used for create and update.
    CI-specific fields (bank, ci_date, fob_rate, freight, insurance, lc_details)
    are accepted here and applied to the linked CI inside create/update.
    """
    # CI fields accepted at the PL level
    ci_date = serializers.DateField(required=False, default=date.today)
    bank = serializers.IntegerField(required=False, allow_null=True)
    fob_rate = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True
    )
    freight = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True
    )
    insurance = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True
    )
    lc_details = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = PackingList
        fields = [
            "proforma_invoice", "pl_date",
            "exporter", "consignee", "buyer", "notify_party",
            # Order references
            "po_number", "po_date",
            "lc_number", "lc_date",
            "bl_number", "bl_date",
            "so_number", "so_date",
            "other_references", "other_references_date",
            "additional_description",
            # Shipping
            "pre_carriage_by",
            "place_of_receipt", "place_of_receipt_by_pre_carrier",
            "vessel_flight_no",
            "port_of_loading", "port_of_discharge", "final_destination",
            # Countries
            "country_of_origin", "country_of_final_destination",
            # Payment & Terms
            "incoterms", "payment_terms",
            # CI fields
            "ci_date", "bank", "fob_rate", "freight", "insurance", "lc_details",
        ]

    def validate(self, data):
        # On create, proforma_invoice is required and must be Approved.
        if self.instance is None:
            pi = data.get("proforma_invoice")
            if not pi:
                raise serializers.ValidationError(
                    {"proforma_invoice": "A Proforma Invoice must be selected."}
                )
            from apps.workflow.constants import APPROVED
            if pi.status != APPROVED:
                raise serializers.ValidationError(
                    {"proforma_invoice": "Only Approved Proforma Invoices can be selected."}
                )
        return data
