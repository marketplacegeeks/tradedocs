from rest_framework import serializers
from .models import Country, Incoterm, Location, Port, PaymentTerm, PreCarriageBy, UOM


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
