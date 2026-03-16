import re

from django.core.exceptions import ValidationError
from django.db import models


class Country(models.Model):
    """ISO country. Referenced by Port, Location, Organisation, and Bank."""
    name = models.CharField(max_length=100)
    iso2 = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 Alpha-2 code, e.g. IN")
    iso3 = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 Alpha-3 code, e.g. IND")

    class Meta:
        db_table = "master_data_country"
        ordering = ["name"]
        verbose_name_plural = "countries"

    def __str__(self):
        return f"{self.name} ({self.iso2})"


class Port(models.Model):
    """Seaport or airport. Used for Port of Loading / Discharge on documents."""
    name = models.CharField(max_length=150)
    # UN/LOCODE is the international standard port identifier (e.g. INBOM for Mumbai)
    code = models.CharField(max_length=10, unique=True, help_text="UN/LOCODE, e.g. INBOM")
    # Constraint #7: PROTECT prevents deleting a Country that has ports referencing it
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="ports")

    class Meta:
        db_table = "master_data_port"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Location(models.Model):
    """
    A named place used for Place of Receipt, Final Destination, etc.
    Broader than a port — includes inland cities, warehouses, and depots.
    """
    name = models.CharField(max_length=150)
    # Constraint #7: PROTECT prevents deleting a Country that has locations referencing it
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="locations")

    class Meta:
        db_table = "master_data_location"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class Incoterm(models.Model):
    """International Commerce Terms (e.g. FOB, CIF, EXW)."""
    code = models.CharField(max_length=10, unique=True, help_text="Short code, e.g. FOB")
    full_name = models.CharField(max_length=100, help_text="e.g. Free On Board")
    description = models.TextField(blank=True)

    class Meta:
        db_table = "master_data_incoterm"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} – {self.full_name}"


class UOM(models.Model):
    """Unit of Measurement used on line items (e.g. MT, KG, PCS, CBM)."""
    name = models.CharField(max_length=50, help_text="e.g. Metric Tonnes")
    abbreviation = models.CharField(max_length=20, unique=True, help_text="e.g. MT")

    class Meta:
        db_table = "master_data_uom"
        ordering = ["abbreviation"]
        verbose_name = "UOM"
        verbose_name_plural = "UOMs"

    def __str__(self):
        return self.abbreviation


class PaymentTerm(models.Model):
    """Payment terms used on Proforma Invoices (e.g. Advance Payment, LC at Sight)."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "master_data_paymentterm"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PreCarriageBy(models.Model):
    """Mode of pre-carriage transport (e.g. Truck, Rail, Feeder Vessel)."""
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "master_data_precarriageby"
        ordering = ["name"]
        verbose_name = "Pre-Carriage By"
        verbose_name_plural = "Pre-Carriage By"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Organisation and its sub-records (FR-04)
# ---------------------------------------------------------------------------

class Organisation(models.Model):
    """
    A trading party used on documents — could be an Exporter, Consignee, Buyer,
    or Notify Party depending on which tags are attached.

    Constraint #8: never hard-deleted; deactivated via is_active=False instead.
    """
    name = models.CharField(max_length=255, unique=True)
    # IEC Code is required only when the org is tagged as Exporter (enforced in serializer).
    # null=True so multiple orgs without an IEC code don't conflict on the unique constraint.
    iec_code = models.CharField(
        max_length=10, unique=True, null=True, blank=True,
        help_text="DGFT Importer–Exporter Code; exactly 10 alphanumeric chars"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "master_data_organisation"
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrganisationTag(models.Model):
    """
    Document role tag for an organisation (EXPORTER / CONSIGNEE / BUYER / NOTIFY_PARTY).
    Determines which document dropdowns the organisation appears in.
    """
    class Tag(models.TextChoices):
        EXPORTER = "EXPORTER", "Exporter"
        CONSIGNEE = "CONSIGNEE", "Consignee"
        BUYER = "BUYER", "Buyer"
        NOTIFY_PARTY = "NOTIFY_PARTY", "Notify Party"

    # CASCADE: if the parent Organisation is removed, its tags go with it.
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="tags"
    )
    tag = models.CharField(max_length=20, choices=Tag.choices)

    class Meta:
        db_table = "master_data_organisation_tag"
        # Each tag value can appear at most once per organisation.
        unique_together = [("organisation", "tag")]

    def __str__(self):
        return f"{self.organisation.name} — {self.get_tag_display()}"


def _validate_gstin(value):
    """GSTIN regex: 15-char state code + PAN-derived code + Z + checksum digit."""
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Invalid GSTIN format. Expected: 2 digits + 5 letters + 4 digits + letter + "
            "alphanumeric + Z + alphanumeric (total 15 characters)."
        )


def _validate_pan(value):
    """PAN regex: 10-char code issued by Indian income tax department."""
    pattern = r'^[A-Z]{3}[PCHFATBLJGE]{1}[A-Z]{1}[0-9]{4}[A-Z]{1}$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Invalid PAN format. Expected: 3 letters + entity type letter + "
            "letter + 4 digits + letter (total 10 characters)."
        )


class OrganisationTaxCode(models.Model):
    """
    A tax registration entry for an organisation (e.g. GSTIN, PAN, VAT).
    Tax type and tax code must always be saved together.
    """
    # CASCADE: tax codes belong to the organisation; they go away if the org is removed.
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="tax_codes"
    )
    tax_type = models.CharField(max_length=50, help_text="e.g. GSTIN, PAN, VAT")
    tax_code = models.CharField(max_length=50)

    class Meta:
        db_table = "master_data_organisation_tax_code"

    def __str__(self):
        return f"{self.tax_type}: {self.tax_code}"

    def clean(self):
        """Apply format validation depending on the tax type."""
        tax_type_upper = self.tax_type.upper().strip()
        if tax_type_upper in ("GST", "GSTIN"):
            _validate_gstin(self.tax_code)
        elif tax_type_upper == "PAN":
            _validate_pan(self.tax_code)
        # All other types: no format validation; stored as entered.


class OrganisationAddress(models.Model):
    """
    A physical address for an organisation. An organisation must have at least one.
    Contact details (email, phone, contact name) live here, not on Organisation itself,
    because a Maker can choose which address (and therefore which contact) to use per document.
    """
    class AddressType(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        FACTORY = "FACTORY", "Factory"
        OFFICE = "OFFICE", "Office"

    # CASCADE: addresses belong to the organisation; they go away if the org is removed.
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="addresses"
    )
    address_type = models.CharField(max_length=20, choices=AddressType.choices)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    pin = models.CharField(max_length=20, blank=True)
    # Constraint #7: PROTECT — cannot delete a Country that addresses reference.
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, related_name="organisation_addresses"
    )
    email = models.EmailField()
    contact_name = models.CharField(max_length=150)
    # Phone stored as two fields: dial code (e.g. +91) and local number.
    # Both are optional overall, but if one is provided the other must be too (enforced in serializer).
    phone_country_code = models.CharField(
        max_length=5, blank=True,
        help_text="E.164 dial code, e.g. +91"
    )
    phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "master_data_organisation_address"
        ordering = ["address_type"]

    def __str__(self):
        return f"{self.organisation.name} — {self.get_address_type_display()} — {self.city}"
