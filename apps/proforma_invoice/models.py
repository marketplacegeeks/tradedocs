import re
from django.conf import settings
from django.db import models

from apps.workflow.constants import DRAFT, DOCUMENT_STATUS_CHOICES


class ShipmentAllowance(models.TextChoices):
    ALLOWED = "ALLOWED", "Allowed"
    NOT_ALLOWED = "NOT_ALLOWED", "Not Allowed"


class ProformaInvoice(models.Model):
    """
    Header record for a Proforma Invoice (FR-09).
    Line items and additional charges are stored as related models.
    """

    # ---- Auto-generated number (FR-09, constraint #16/17) --------------------
    # Populated by ProformaInvoiceService.generate_document_number() on first save.
    pi_number = models.CharField(max_length=20, unique=True)

    # ---- Header fields (FR-09.1) --------------------------------------------
    pi_date = models.DateField()  # Defaults to today in serializer

    # Constraint #7: PROTECT prevents deleting a referenced Organisation
    exporter = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pi_as_exporter",
    )
    consignee = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pi_as_consignee",
    )
    buyer = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pi_as_buyer",
        null=True,
        blank=True,
    )

    buyer_order_no = models.CharField(max_length=100, blank=True, default="")
    buyer_order_date = models.DateField(null=True, blank=True)
    other_references = models.TextField(blank=True, default="")

    country_of_origin = models.ForeignKey(
        "master_data.Country",
        on_delete=models.PROTECT,
        related_name="pi_as_origin",
        null=True,
        blank=True,
    )
    country_of_final_destination = models.ForeignKey(
        "master_data.Country",
        on_delete=models.PROTECT,
        related_name="pi_as_final_destination",
        null=True,
        blank=True,
    )

    # ---- Shipping & Logistics (FR-09.2) -------------------------------------
    pre_carriage_by = models.ForeignKey(
        "master_data.PreCarriageBy",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    # "Place of Receipt by Pre-Carrier" in FR-09.2; also referenced as "Place of Receipt" in 5.8.1
    place_of_receipt = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pi_place_of_receipt",
        null=True,
        blank=True,
    )
    # Separate field for the place where the pre-carrier hands over goods (FR-09.2 / FR-14M.3)
    place_of_receipt_by_pre_carrier = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pi_place_of_receipt_by_pre_carrier",
        null=True,
        blank=True,
    )
    vessel_flight_no = models.CharField(max_length=100, blank=True, default="")
    port_of_loading = models.ForeignKey(
        "master_data.Port",
        on_delete=models.PROTECT,
        related_name="pi_port_of_loading",
        null=True,
        blank=True,
    )
    port_of_discharge = models.ForeignKey(
        "master_data.Port",
        on_delete=models.PROTECT,
        related_name="pi_port_of_discharge",
        null=True,
        blank=True,
    )
    final_destination = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pi_final_destination",
        null=True,
        blank=True,
    )

    # ---- Payment & Terms (FR-09.3) ------------------------------------------
    # Required fields (enforced in serializer, not at DB level for flexibility)
    payment_terms = models.ForeignKey(
        "master_data.PaymentTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    incoterms = models.ForeignKey(
        "master_data.Incoterm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    bank = models.ForeignKey(
        "master_data.Bank",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    validity_for_acceptance = models.DateField(null=True, blank=True)
    validity_for_shipment = models.DateField(null=True, blank=True)
    partial_shipment = models.CharField(
        max_length=20, choices=ShipmentAllowance.choices, blank=True, default=""
    )
    transshipment = models.CharField(
        max_length=20, choices=ShipmentAllowance.choices, blank=True, default=""
    )

    # ---- T&C (FR-09.4) ------------------------------------------------------
    tc_template = models.ForeignKey(
        "master_data.TCTemplate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    # Snapshot of the T&C body stored at creation time (so template edits don't affect existing PIs)
    tc_content = models.TextField(blank=True, default="")

    # ---- Incoterms cost breakdown (FR-09.7) ---------------------------------
    # Constraint #5: DecimalField(15,2) for all monetary amounts
    # These fields are only filled for Incoterms where the seller bears the cost.
    # freight / insurance / import_duty / destination_charges are entered by the Maker.
    freight = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    insurance_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    import_duty = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    destination_charges = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # ---- Signed copy upload (FR-08.4) ---------------------------------------
    # Authorised users may upload a scanned signed copy once the PI is Approved.
    # Stored in MEDIA_ROOT/signed_copies/pi/; never auto-generated.
    signed_copy = models.FileField(
        upload_to="signed_copies/pi/",
        null=True,
        blank=True,
    )

    # ---- Workflow (FR-08) ---------------------------------------------------
    status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DRAFT,
        db_index=True,  # Most list views filter by status
    )

    # Constraint #7: PROTECT so deleting a user doesn't orphan PI records
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_proforma_invoices",
        db_index=True,  # Makers filter to their own documents
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "proforma_invoice"
        ordering = ["-created_at"]

    def __str__(self):
        return self.pi_number


class ProformaInvoiceLineItem(models.Model):
    """
    One commodity row on a Proforma Invoice (FR-09.5).
    Amount is stored as a computed value (Quantity × Rate) recalculated on save.
    """
    HSN_REGEX = re.compile(r"^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?)?$")

    pi = models.ForeignKey(
        ProformaInvoice,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    hsn_code = models.CharField(max_length=10, blank=True, default="")
    item_code = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField()  # Required (enforced in serializer)

    # Constraint #6: 3 decimal places for quantities
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    uom = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    # Constraint #5: 2 decimal places for monetary amounts
    rate_usd = models.DecimalField(max_digits=15, decimal_places=2)
    # Stored so PDF reads it directly without re-multiplying; updated on every save
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        db_table = "proforma_invoice_line_item"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        # Recompute and store amount every time (no floating-point: Decimal arithmetic)
        self.amount_usd = self.quantity * self.rate_usd
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pi.pi_number} | {self.description[:40]}"


class ProformaInvoiceCharge(models.Model):
    """
    Additional charge row below the line items table (FR-09.5).
    E.g. Inspection Fees, Documentation Charges.
    """
    pi = models.ForeignKey(
        ProformaInvoice,
        on_delete=models.CASCADE,
        related_name="charges",
    )
    description = models.CharField(max_length=255)
    # Constraint #5: 2 decimal places for monetary amounts
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "proforma_invoice_charge"
        ordering = ["id"]

    def __str__(self):
        return f"{self.pi.pi_number} | {self.description}"
