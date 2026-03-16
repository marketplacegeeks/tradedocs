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
