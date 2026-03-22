import re

from django.core.exceptions import ValidationError
from django.db import models


class Country(models.Model):
    """ISO country. Referenced by Port, Location, Organisation, and Bank."""
    name = models.CharField(max_length=100)
    iso2 = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 Alpha-2 code, e.g. IN")
    iso3 = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 Alpha-3 code, e.g. IND")
    is_active = models.BooleanField(default=True)

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
    is_active = models.BooleanField(default=True)

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
    is_active = models.BooleanField(default=True)

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
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_data_incoterm"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} – {self.full_name}"


class UOM(models.Model):
    """Unit of Measurement used on line items (e.g. MT, KG, PCS, CBM)."""
    name = models.CharField(max_length=50, help_text="e.g. Metric Tonnes")
    abbreviation = models.CharField(max_length=20, unique=True, help_text="e.g. MT")
    is_active = models.BooleanField(default=True)

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
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_data_paymentterm"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PreCarriageBy(models.Model):
    """Mode of pre-carriage transport (e.g. Truck, Rail, Feeder Vessel)."""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_data_precarriageby"
        ordering = ["name"]
        verbose_name = "Pre-Carriage By"
        verbose_name_plural = "Pre-Carriage By"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Terms & Conditions Templates (FR-07)
# ---------------------------------------------------------------------------

class TCTemplate(models.Model):
    """
    A reusable Terms & Conditions template selectable when creating trade documents.
    Body stores rich HTML produced by the TipTap editor on the frontend.
    Soft-deleted via is_active=False — never hard-deleted — so templates already
    referenced by documents remain retrievable for historical display.
    """
    name = models.CharField(max_length=255, unique=True)
    body = models.TextField(help_text="Rich HTML content produced by the rich text editor")
    # A template can be associated with multiple organisations; an org can have many templates.
    organisations = models.ManyToManyField(
        "Organisation",
        related_name="tc_templates",
        help_text="Organisations this template is available to",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "master_data_tctemplate"
        ordering = ["name"]
        verbose_name = "T&C Template"
        verbose_name_plural = "T&C Templates"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Bank and Currency (FR-05)
# ---------------------------------------------------------------------------

class Currency(models.Model):
    """ISO 4217 currency. Referenced by Bank accounts."""
    code = models.CharField(
        max_length=3, unique=True,
        help_text="ISO 4217 currency code, e.g. USD, AED, INR"
    )
    name = models.CharField(max_length=100, help_text="e.g. US Dollar")

    class Meta:
        db_table = "master_data_currency"
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return f"{self.code} – {self.name}"


def _validate_swift(value):
    """SWIFT/BIC must be 8 or 11 uppercase alphanumeric characters (ISO 9362)."""
    if not re.match(r'^[A-Z0-9]{8}$|^[A-Z0-9]{11}$', value):
        raise ValidationError(
            "SWIFT/BIC code must be exactly 8 or 11 uppercase letters and digits (ISO 9362)."
        )


def _validate_iban(value):
    """IBAN: 2-letter country code, 2 check digits, up to 30 alphanumeric chars. Max 34."""
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', value):
        raise ValidationError(
            "IBAN must start with a 2-letter country code, 2 check digits, "
            "and up to 30 alphanumeric characters (max 34 total)."
        )


class Bank(models.Model):
    """
    A bank account record used on Proforma Invoices (optional) and
    Commercial Invoices (mandatory). Details print on both PDFs.
    Constraint #7: all FK references use PROTECT.
    Each bank account belongs to one Exporter organisation.
    """
    class AccountType(models.TextChoices):
        CURRENT = "CURRENT", "Current"
        SAVINGS = "SAVINGS", "Savings"
        CHECKING = "CHECKING", "Checking"

    # The Exporter organisation this bank account belongs to.
    # Constraint #7: cannot delete an Organisation that a Bank references.
    organisation = models.ForeignKey(
        "Organisation",
        on_delete=models.PROTECT,
        related_name="banks",
        null=True,  # nullable at DB level to allow safe migration of existing rows
        blank=True,
        help_text="Exporter organisation this bank account belongs to",
    )
    nickname = models.CharField(max_length=255, help_text="Short internal label, e.g. 'USD Operating Account'")
    beneficiary_name = models.CharField(max_length=255, help_text="Account holder name as it appears on wire instructions")
    bank_name = models.CharField(max_length=255)
    # Constraint #7: cannot delete a Country that a Bank references.
    bank_country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="banks")
    branch_name = models.CharField(max_length=255)
    branch_address = models.TextField(blank=True)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=10, choices=AccountType.choices)
    # Constraint #7: cannot delete a Currency that a Bank references.
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="banks")
    swift_code = models.CharField(
        max_length=11, blank=True,
        validators=[_validate_swift],
        help_text="Optional. 8 or 11 uppercase alphanumeric characters (ISO 9362)."
    )
    iban = models.CharField(
        max_length=34, blank=True,
        validators=[_validate_iban],
        help_text="Optional. Up to 34 alphanumeric characters."
    )
    # Stores IFSC (India), ACH routing number (USA), sort code (UK), etc.
    routing_number = models.CharField(max_length=50, blank=True)
    # AD Code is a 14-digit number assigned by the bank to the exporter for DGFT/customs use.
    ad_code = models.CharField(max_length=255, blank=True, help_text="Authorised Dealer Code issued by the bank for customs/DGFT use")

    # --- Intermediary Institution (optional; all-or-nothing) ---
    # Used when the receiving bank requires a correspondent bank for a specific currency.
    intermediary_bank_name = models.CharField(max_length=255, blank=True)
    intermediary_account_number = models.CharField(max_length=50, blank=True)
    intermediary_swift_code = models.CharField(
        max_length=11, blank=True,
        validators=[_validate_swift],
        help_text="Optional. 8 or 11 uppercase alphanumeric characters (ISO 9362).",
    )
    # Constraint #7: cannot delete a Currency that a Bank intermediary references.
    intermediary_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="intermediary_banks",
        help_text="Currency for which this intermediary routing applies (e.g. USD)",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_data_bank"
        ordering = ["bank_name", "nickname"]

    def __str__(self):
        return f"{self.bank_name} – {self.nickname}"

    def clean(self):
        """All four intermediary fields must be filled together or not at all."""
        intermediary_fields = [
            self.intermediary_bank_name,
            self.intermediary_account_number,
            self.intermediary_swift_code,
            self.intermediary_currency_id,
        ]
        filled = [bool(f) for f in intermediary_fields]
        if any(filled) and not all(filled):
            raise ValidationError(
                "If any intermediary institution field is entered, all four are required."
            )


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
        VENDOR = "VENDOR", "Vendor"

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
    email = models.EmailField(blank=True)
    contact_name = models.CharField(max_length=150, blank=True)
    # Phone stored as two fields: dial code (e.g. +91) and local number.
    # Both are optional overall, but if one is provided the other must be too (enforced in serializer).
    phone_country_code = models.CharField(
        max_length=5, blank=True,
        help_text="E.164 dial code, e.g. +91"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    iec_code = models.CharField(
        max_length=10, blank=True, default='',
        help_text="DGFT Importer–Exporter Code for this address, e.g. AABCD1234E"
    )
    tax_type = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Tax registration type for this address, e.g. GSTIN, PAN, VAT"
    )
    tax_code = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Tax registration number for this address"
    )

    class Meta:
        db_table = "master_data_organisation_address"
        ordering = ["address_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "address_type"],
                name="unique_address_type_per_organisation",
            )
        ]

    def __str__(self):
        return f"{self.organisation.name} — {self.get_address_type_display()} — {self.city}"
