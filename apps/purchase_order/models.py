"""
Purchase Order model (FR-PO-06).

Constraint #1: All monetary amounts use DecimalField(max_digits=15, decimal_places=2).
Constraint #2: Quantities use DecimalField(max_digits=15, decimal_places=6) as per FR-PO-06.
Constraint #3: All FK references to master data use on_delete=PROTECT.
"""

from decimal import Decimal
from django.conf import settings
from django.db import models

from apps.workflow.constants import DRAFT, DOCUMENT_STATUS_CHOICES


class TransactionType(models.TextChoices):
    IGST = "IGST", "Inter State Transaction (IGST)"
    CGST_SGST = "CGST_SGST", "Same State Transaction (CGST+SGST)"
    ZERO_RATED = "ZERO_RATED", "Procurement for Export (Zero-Rated)"


class PurchaseOrder(models.Model):
    """
    Header record for a Purchase Order (FR-PO-06).
    Line items are stored in PurchaseOrderLineItem.
    Monetary totals are computed from line items — not stored here.
    """

    # ---- Auto-generated number (FR-PO-07) ------------------------------------
    # Populated by generate_document_number() on first save. Format: PO-YYYY-NNNN.
    po_number = models.CharField(max_length=20, unique=True)

    # ---- Header fields -------------------------------------------------------
    po_date = models.DateField()

    # Reference number the vendor uses for the buyer
    customer_no = models.CharField(max_length=100, blank=True, default="")

    # Constraint #3: PROTECT — cannot delete an Organisation that is referenced here
    vendor = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="purchase_orders_as_vendor",
        db_index=True,
    )

    # The user who is the internal point of contact for this PO
    internal_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchase_orders_as_contact",
    )

    # Optional buyer organisation — tagged as BUYER
    buyer = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="purchase_orders_as_buyer",
        null=True,
        blank=True,
    )

    # Delivery address — belongs to the buyer (when set) or the vendor
    delivery_address = models.ForeignKey(
        "master_data.OrganisationAddress",
        on_delete=models.PROTECT,
        related_name="purchase_orders_as_delivery",
    )

    bank = models.ForeignKey(
        "master_data.Bank",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    currency = models.ForeignKey(
        "master_data.Currency",
        on_delete=models.PROTECT,
    )

    payment_terms = models.ForeignKey(
        "master_data.PaymentTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    country_of_origin = models.ForeignKey(
        "master_data.Country",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Controls which tax columns appear on line items (FR-PO-06)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    time_of_delivery = models.CharField(max_length=200, blank=True, default="")

    # T&C snapshot — template FK + body copied at selection time
    tc_template = models.ForeignKey(
        "master_data.TCTemplate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    tc_content = models.TextField(blank=True, default="")

    line_item_remarks = models.TextField(blank=True, default="")
    remarks = models.TextField(blank=True, default="")

    # ---- Workflow ------------------------------------------------------------
    status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchase_orders_created",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_order"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self):
        return self.po_number


class PurchaseOrderLineItem(models.Model):
    """
    One line item on a Purchase Order (FR-PO-06).

    Tax computed fields (taxable_amount, igst_amount, cgst_amount, sgst_amount,
    total_tax, total) are recalculated on every save based on the parent PO's
    transaction_type.
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="line_items",
    )

    description = models.TextField()
    item_code = models.CharField(max_length=100, blank=True, default="")
    hsn_code = models.CharField(max_length=20, blank=True, default="")
    manufacturer = models.CharField(max_length=200, blank=True, default="")

    uom = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
    )

    # Constraint #2: up to 6 decimal places for quantity (FR-PO-06 requirement)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)

    # Free-text packing detail, e.g. "4,320 25kg bags without pallets"
    packaging_description = models.TextField(blank=True, default="")

    # Constraint #1: 2 decimal places for monetary amounts
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)

    # ---- Computed fields (stored for PDF + API read performance) -----------
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    igst_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, editable=False)

    cgst_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, editable=False)

    sgst_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, editable=False)

    total_tax = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "purchase_order_line_item"
        ordering = ["sort_order", "id"]

    def save(self, *args, **kwargs):
        """
        Recompute all derived tax fields before saving.
        Logic is driven by the parent PO's transaction_type.
        """
        self.taxable_amount = self.quantity * self.unit_price
        transaction_type = self.purchase_order.transaction_type

        if transaction_type == TransactionType.IGST:
            rate = self.igst_percent or Decimal("0")
            self.igst_amount = (self.taxable_amount * rate / Decimal("100")).quantize(Decimal("0.01"))
            # Clear CGST/SGST fields
            self.cgst_percent = None
            self.cgst_amount = None
            self.sgst_percent = None
            self.sgst_amount = None
            self.total_tax = self.igst_amount

        elif transaction_type == TransactionType.CGST_SGST:
            cgst_rate = self.cgst_percent or Decimal("0")
            sgst_rate = self.sgst_percent or Decimal("0")
            self.cgst_amount = (self.taxable_amount * cgst_rate / Decimal("100")).quantize(Decimal("0.01"))
            self.sgst_amount = (self.taxable_amount * sgst_rate / Decimal("100")).quantize(Decimal("0.01"))
            # Clear IGST fields
            self.igst_percent = None
            self.igst_amount = None
            self.total_tax = self.cgst_amount + self.sgst_amount

        else:  # ZERO_RATED
            self.igst_percent = None
            self.igst_amount = None
            self.cgst_percent = None
            self.cgst_amount = None
            self.sgst_percent = None
            self.sgst_amount = None
            self.total_tax = Decimal("0")

        self.total = self.taxable_amount + self.total_tax
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_order.po_number} | {self.description[:40]}"
