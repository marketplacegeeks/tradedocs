import re

import phonenumbers
from rest_framework import serializers

from .models import (
    Bank, Country, Currency, Incoterm, Location, Organisation, OrganisationAddress,
    OrganisationTag, Port, PaymentTerm, PreCarriageBy, TCTemplate, UOM,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "iso2", "iso3", "is_active"]


class PortSerializer(serializers.ModelSerializer):
    # country_name is included read-only so the frontend can display it without a second request
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Port
        fields = ["id", "name", "code", "country", "country_name", "is_active"]


class LocationSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Location
        fields = ["id", "name", "country", "country_name", "is_active"]


class IncotermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incoterm
        fields = ["id", "code", "full_name", "description", "is_active"]


class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = ["id", "name", "abbreviation", "is_active"]


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ["id", "name", "description", "is_active"]


class PreCarriageBySerializer(serializers.ModelSerializer):
    class Meta:
        model = PreCarriageBy
        fields = ["id", "name", "is_active"]


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
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    intermediary_currency_code = serializers.CharField(
        source="intermediary_currency.code", read_only=True, default=None
    )

    class Meta:
        model = Bank
        fields = [
            "id", "organisation", "organisation_name",
            "nickname", "beneficiary_name", "bank_name",
            "bank_country", "bank_country_name",
            "branch_name", "branch_address",
            "account_number", "account_type",
            "currency", "currency_code", "currency_name",
            "swift_code", "iban", "routing_number", "ad_code",
            "intermediary_bank_name", "intermediary_account_number",
            "intermediary_swift_code",
            "intermediary_currency", "intermediary_currency_code",
            "is_active",
        ]

    def validate_organisation(self, value):
        """The selected organisation must be tagged as Exporter."""
        if value and not value.tags.filter(tag="EXPORTER").exists():
            raise serializers.ValidationError(
                "The selected organisation must be tagged as Exporter."
            )
        return value

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

    def validate_intermediary_swift_code(self, value):
        """If intermediary SWIFT is provided, apply the same ISO 9362 format check."""
        if value:
            value = value.strip().upper()
            if not re.match(r'^[A-Z0-9]{8}$|^[A-Z0-9]{11}$', value):
                raise serializers.ValidationError(
                    "SWIFT/BIC code must be exactly 8 or 11 uppercase letters and digits (ISO 9362)."
                )
        return value

    def validate(self, data):
        """All four intermediary fields must be provided together or not at all."""
        intermediary_fields = [
            data.get("intermediary_bank_name", ""),
            data.get("intermediary_account_number", ""),
            data.get("intermediary_swift_code", ""),
            data.get("intermediary_currency"),
        ]
        filled = [bool(f) for f in intermediary_fields]
        if any(filled) and not all(filled):
            raise serializers.ValidationError(
                "If any intermediary institution field is entered, all four fields are required."
            )
        return data


# ---------------------------------------------------------------------------
# Organisation serializers (FR-04)
# ---------------------------------------------------------------------------

class OrganisationTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationTag
        fields = ["id", "tag"]


class OrganisationAddressSerializer(serializers.ModelSerializer):
    # Read-only country name so the frontend can display it without a second request.
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = OrganisationAddress
        fields = [
            "id", "address_type", "line1", "line2", "city", "state", "pin",
            "country", "country_name", "email", "contact_name",
            "phone_country_code", "phone_number",
            "iec_code", "tax_type", "tax_code",
        ]

    def validate(self, data):
        """
        1. Phone validation: if either field is provided, both are required and must parse.
        2. Uniqueness: each address_type can appear at most once per organisation.
           This is enforced here (in addition to the DB constraint) to return a clear
           error message before hitting the database.
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

        # Duplicate address_type check for the standalone address endpoint.
        # self.context["view"] carries the organisation_pk from the URL.
        address_type = data.get("address_type")
        view = self.context.get("view")
        if address_type and view and hasattr(view, "kwargs"):
            org_pk = view.kwargs.get("organisation_pk")
            if org_pk:
                qs = OrganisationAddress.objects.filter(
                    organisation_id=org_pk,
                    address_type=address_type,
                )
                # On update (PUT/PATCH), exclude the current instance.
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError(
                        {"address_type": f"This organisation already has a {address_type.capitalize()} address."}
                    )

        return data


class OrganisationSerializer(serializers.ModelSerializer):
    addresses = OrganisationAddressSerializer(many=True)
    tags = OrganisationTagSerializer(many=True)

    class Meta:
        model = Organisation
        fields = ["id", "name", "is_active", "addresses", "tags",
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

        # Each address_type must appear at most once in the submitted list.
        if "addresses" in data:
            seen_types = set()
            for addr in data["addresses"]:
                atype = addr.get("address_type")
                if atype in seen_types:
                    raise serializers.ValidationError(
                        {"addresses": f"Duplicate address type: only one {atype.capitalize()} address is allowed per organisation."}
                    )
                seen_types.add(atype)

        return data

    def create(self, validated_data):
        """Create the organisation and all nested sub-records in one operation."""
        addresses_data = validated_data.pop("addresses")
        tags_data = validated_data.pop("tags")

        organisation = Organisation.objects.create(**validated_data)

        for address_data in addresses_data:
            OrganisationAddress.objects.create(organisation=organisation, **address_data)
        for tag_data in tags_data:
            OrganisationTag.objects.create(organisation=organisation, **tag_data)

        return organisation

    def update(self, instance, validated_data):
        """
        Update the organisation's top-level fields and replace nested sub-records
        wholesale when they are included in the request body.

        A PATCH that omits 'addresses' or 'tags' will leave those sub-records
        untouched. Sending an explicit list (even empty) replaces them.
        """
        addresses_data = validated_data.pop("addresses", None)
        tags_data = validated_data.pop("tags", None)

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
