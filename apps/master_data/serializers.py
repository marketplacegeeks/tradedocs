import re

import phonenumbers
from rest_framework import serializers

from .models import (
    Bank, Country, Currency, Incoterm, Location, Organisation, OrganisationAddress,
    OrganisationTag, OrganisationTaxCode, Port, PaymentTerm, PreCarriageBy, TCTemplate, UOM,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "iso2", "iso3"]


class PortSerializer(serializers.ModelSerializer):
    # country_name is included read-only so the frontend can display it without a second request
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Port
        fields = ["id", "name", "code", "country", "country_name"]


class LocationSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Location
        fields = ["id", "name", "country", "country_name"]


class IncotermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incoterm
        fields = ["id", "code", "full_name", "description"]


class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = ["id", "name", "abbreviation"]


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ["id", "name", "description"]


class PreCarriageBySerializer(serializers.ModelSerializer):
    class Meta:
        model = PreCarriageBy
        fields = ["id", "name"]


# ---------------------------------------------------------------------------
# Currency and Bank serializers (FR-05)
# ---------------------------------------------------------------------------

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "name"]


class BankSerializer(serializers.ModelSerializer):
    # Read-only display fields so the frontend can show names without extra requests.
    bank_country_name = serializers.CharField(source="bank_country.name", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    currency_name = serializers.CharField(source="currency.name", read_only=True)

    class Meta:
        model = Bank
        fields = [
            "id", "nickname", "beneficiary_name", "bank_name",
            "bank_country", "bank_country_name",
            "branch_name", "branch_address",
            "account_number", "account_type",
            "currency", "currency_code", "currency_name",
            "swift_code", "iban", "routing_number",
        ]

    def validate_swift_code(self, value):
        """If SWIFT code is provided, it must be 8 or 11 uppercase alphanumeric characters."""
        if value:
            value = value.strip().upper()
            if not re.match(r'^[A-Z0-9]{8}$|^[A-Z0-9]{11}$', value):
                raise serializers.ValidationError(
                    "SWIFT/BIC code must be exactly 8 or 11 uppercase letters and digits (ISO 9362)."
                )
        return value

    def validate_iban(self, value):
        """If IBAN is provided, validate its format: 2-letter country code + 2 digits + up to 30 alphanumeric."""
        if value:
            value = value.strip().upper()
            if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', value):
                raise serializers.ValidationError(
                    "IBAN must start with a 2-letter country code, 2 check digits, "
                    "and up to 30 alphanumeric characters (max 34 total)."
                )
        return value


# ---------------------------------------------------------------------------
# Organisation serializers (FR-04)
# ---------------------------------------------------------------------------

class OrganisationTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationTag
        fields = ["id", "tag"]


class OrganisationTaxCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationTaxCode
        fields = ["id", "tax_type", "tax_code"]

    def validate(self, data):
        """Run the model-level format validation (GSTIN regex, PAN regex)."""
        tax_type = data.get("tax_type", "").upper().strip()
        tax_code = data.get("tax_code", "")
        if tax_type in ("GST", "GSTIN"):
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', tax_code):
                raise serializers.ValidationError(
                    {"tax_code": "Invalid GSTIN format (expected 15-character GSTIN string)."}
                )
        elif tax_type == "PAN":
            if not re.match(r'^[A-Z]{3}[PCHFATBLJGE]{1}[A-Z]{1}[0-9]{4}[A-Z]{1}$', tax_code):
                raise serializers.ValidationError(
                    {"tax_code": "Invalid PAN format (expected 10-character PAN string)."}
                )
        return data


class OrganisationAddressSerializer(serializers.ModelSerializer):
    # Read-only country name so the frontend can display it without a second request.
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = OrganisationAddress
        fields = [
            "id", "address_type", "line1", "line2", "city", "state", "pin",
            "country", "country_name", "email", "contact_name",
            "phone_country_code", "phone_number",
        ]

    def validate(self, data):
        """
        Phone validation: if either the country code or the local number is provided,
        both are required and the combination must be a valid phone number.
        """
        code = data.get("phone_country_code", "").strip()
        number = data.get("phone_number", "").strip()
        if code or number:
            if not code or not number:
                raise serializers.ValidationError(
                    {"phone": "Both phone country code and phone number must be provided together."}
                )
            try:
                parsed = phonenumbers.parse(code + number)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError(
                        {"phone": "The phone number is not valid for the given country code."}
                    )
            except phonenumbers.NumberParseException:
                raise serializers.ValidationError(
                    {"phone": "Invalid phone number format. Use a dial code like +91 and a local number."}
                )
        return data


class OrganisationSerializer(serializers.ModelSerializer):
    addresses = OrganisationAddressSerializer(many=True)
    tags = OrganisationTagSerializer(many=True)
    # Tax codes are optional — an organisation may have zero tax codes.
    tax_codes = OrganisationTaxCodeSerializer(many=True, required=False, default=list)

    class Meta:
        model = Organisation
        fields = ["id", "name", "iec_code", "is_active", "addresses", "tags", "tax_codes",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        # Only check presence of tags/addresses when they are explicitly included in the
        # request body. A PATCH that only updates e.g. is_active should not be blocked.
        if "tags" in data and not data["tags"]:
            raise serializers.ValidationError(
                {"tags": "At least one document role tag is required."}
            )

        if "addresses" in data and not data["addresses"]:
            raise serializers.ValidationError(
                {"addresses": "At least one address is required."}
            )

        # Determine the effective tag list: either from the request or from the existing record.
        if "tags" in data:
            tag_values = [t["tag"] for t in data["tags"]]
        elif self.instance:
            tag_values = list(self.instance.tags.values_list("tag", flat=True))
        else:
            tag_values = []

        # Determine the effective IEC code: from the request or from the existing record.
        iec_code = data.get("iec_code") if "iec_code" in data else (
            self.instance.iec_code if self.instance else None
        )

        # EXPORTER tag requires an IEC code.
        if OrganisationTag.Tag.EXPORTER in tag_values and not iec_code:
            raise serializers.ValidationError(
                {"iec_code": "IEC Code is required for organisations tagged as Exporter."}
            )

        # IEC Code must be exactly 10 uppercase alphanumeric characters.
        if iec_code and not re.match(r'^[A-Z0-9]{10}$', iec_code):
            raise serializers.ValidationError(
                {"iec_code": "IEC Code must be exactly 10 uppercase alphanumeric characters."}
            )

        return data

    def create(self, validated_data):
        """Create the organisation and all nested sub-records in one operation."""
        addresses_data = validated_data.pop("addresses")
        tags_data = validated_data.pop("tags")
        tax_codes_data = validated_data.pop("tax_codes", [])

        organisation = Organisation.objects.create(**validated_data)

        for address_data in addresses_data:
            OrganisationAddress.objects.create(organisation=organisation, **address_data)
        for tag_data in tags_data:
            OrganisationTag.objects.create(organisation=organisation, **tag_data)
        for tax_code_data in tax_codes_data:
            OrganisationTaxCode.objects.create(organisation=organisation, **tax_code_data)

        return organisation

    def update(self, instance, validated_data):
        """
        Update the organisation's top-level fields and replace nested sub-records
        wholesale when they are included in the request body.

        A PATCH that omits 'addresses', 'tags', or 'tax_codes' will leave those
        sub-records untouched. Sending an explicit list (even empty) replaces them.
        """
        addresses_data = validated_data.pop("addresses", None)
        tags_data = validated_data.pop("tags", None)
        tax_codes_data = validated_data.pop("tax_codes", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if addresses_data is not None:
            instance.addresses.all().delete()
            for address_data in addresses_data:
                OrganisationAddress.objects.create(organisation=instance, **address_data)

        if tags_data is not None:
            instance.tags.all().delete()
            for tag_data in tags_data:
                OrganisationTag.objects.create(organisation=instance, **tag_data)

        if tax_codes_data is not None:
            instance.tax_codes.all().delete()
            for tax_code_data in tax_codes_data:
                OrganisationTaxCode.objects.create(organisation=instance, **tax_code_data)

        return instance


# ---------------------------------------------------------------------------
# T&C Template serializer (FR-07)
# ---------------------------------------------------------------------------

class TCTemplateSerializer(serializers.ModelSerializer):
    # Read-only list of org names so the frontend can display them without extra requests.
    organisation_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TCTemplate
        fields = [
            "id", "name", "body", "organisations", "organisation_names",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_organisation_names(self, obj):
        return list(obj.organisations.values_list("name", flat=True))

    def validate_name(self, value):
        """Template name must be unique across all templates (active or inactive)."""
        queryset = TCTemplate.objects.filter(name=value)
        # On update, exclude the current instance to allow saving with no name change.
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A template with this name already exists.")
        return value

    def validate_body(self, value):
        """Body must not be empty — a blank template body cannot be saved."""
        if not value or not value.strip():
            raise serializers.ValidationError("Template body cannot be empty.")
        return value

    def validate_organisations(self, value):
        """At least one organisation must be associated before the template can be saved."""
        if not value:
            raise serializers.ValidationError(
                "At least one organisation must be associated with this template."
            )
        return value
