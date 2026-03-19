from django.conf import settings
from django.db import models

from apps.workflow.constants import DRAFT, DOCUMENT_STATUS_CHOICES


class CommercialInvoice(models.Model):
    """
    Commercial Invoice record, created simultaneously with a PackingList (FR-14M).
    Both documents share a joint approval workflow — status transitions affect both.
    The financial break-up fields (FOB Rate, Freight, Insurance) live here because
    they print only on the CI PDF, not on the PL PDF.
    """

    # ---- Auto-generated number (FR-14M.11, constraint #16/17) ----------------
    # Populated by CommercialInvoiceService.generate_document_number() on first save.
    # Not overridable by the Maker (FR-14M.11).
    ci_number = models.CharField(max_length=20, unique=True)

    # ---- Header fields (FR-14M.3) -------------------------------------------
    ci_date = models.DateField()  # Defaults to today in serializer

    # Constraint #7: PROTECT — the PL record must not be deleted while a CI references it.
    packing_list = models.OneToOneField(
        "packing_list.PackingList",
        on_delete=models.PROTECT,
        related_name="commercial_invoice",
    )

    # Bank details print on the CI PDF (FR-14M.9).
    # Constraint #7: PROTECT on Bank FK.
    bank = models.ForeignKey(
        "master_data.Bank",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # ---- Financial break-up (FR-14M.8B) -------------------------------------
    # Constraint #5: DecimalField(15,2) for all monetary amounts.
    # Visibility on the form is driven by the Incoterm (FR-09.7.3 rules).
    # Fields default to null; serializer prints 0.00 when null.
    fob_rate = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    freight = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    insurance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    # Letter of Credit reference details; always shown regardless of Incoterm.
    lc_details = models.TextField(blank=True, default="")

    # ---- Workflow (FR-14M.12) -----------------------------------------------
    # Constraint #10: status values come from workflow/constants.py
    status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DRAFT,
        db_index=True,
    )

    # Constraint #7: PROTECT so deleting a user doesn't orphan records
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_commercial_invoices",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commercial_invoice"
        ordering = ["-created_at"]

    def __str__(self):
        return self.ci_number


class CommercialInvoiceLineItem(models.Model):
    """
    Aggregated line item snapshot for a Commercial Invoice (FR-14M.8B / FR-14M.10).
    Rows are generated at CI creation time by grouping ContainerItems by item_code + uom.
    amount_usd is stored and recomputed on every save (total_quantity × rate_usd).
    """

    ci = models.ForeignKey(
        CommercialInvoice,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    item_code = models.CharField(max_length=100)
    description = models.TextField()
    hsn_code = models.CharField(max_length=8, blank=True, default="")
    # "No & Kind of Packages" — editable snapshot (FR-14M.10 notes this field is editable)
    packages_kind = models.CharField(max_length=255, blank=True, default="")

    # Constraint #7: PROTECT on UOM FK
    uom = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
    )
    # Constraint #6: 3 decimal places for quantity
    total_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    # Constraint #5: 2 decimal places for monetary amounts
    rate_usd = models.DecimalField(max_digits=15, decimal_places=2)
    # Stored computed value: total_quantity × rate_usd
    amount_usd = models.DecimalField(
        max_digits=15, decimal_places=2, editable=False
    )

    class Meta:
        db_table = "commercial_invoice_line_item"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        # Recompute and store amount every time (Decimal arithmetic — no float rounding).
        self.amount_usd = self.total_quantity * self.rate_usd
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ci.ci_number} | {self.item_code}"
