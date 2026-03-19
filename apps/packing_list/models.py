import re
from django.conf import settings
from django.db import models

from apps.workflow.constants import DRAFT, DOCUMENT_STATUS_CHOICES


class PackingList(models.Model):
    """
    Header record for the combined Packing List + Commercial Invoice (FR-14M).
    Both PL and CI records are created simultaneously and share a joint approval workflow.
    The PackingList is the parent; CommercialInvoice has a FK back to this model.
    """

    # ---- Auto-generated number (FR-14M.11, constraint #16/17) ----------------
    # Populated by PackingListService.generate_document_number() on first save.
    pl_number = models.CharField(max_length=20, unique=True)

    # ---- Header fields (FR-14M.3) -------------------------------------------
    pl_date = models.DateField()  # Defaults to today in serializer

    # Constraint #7: PROTECT prevents deleting a referenced ProformaInvoice
    proforma_invoice = models.ForeignKey(
        "proforma_invoice.ProformaInvoice",
        on_delete=models.PROTECT,
        related_name="packing_lists",
    )

    # Constraint #7: PROTECT on all Organisation FKs
    exporter = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pl_as_exporter",
    )
    consignee = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pl_as_consignee",
    )
    buyer = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pl_as_buyer",
        null=True,
        blank=True,
    )
    notify_party = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="pl_as_notify_party",
        null=True,
        blank=True,
    )

    # ---- Shipping & Logistics (FR-14M.3) ------------------------------------
    pre_carriage_by = models.ForeignKey(
        "master_data.PreCarriageBy",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    place_of_receipt = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pl_place_of_receipt",
        null=True,
        blank=True,
    )
    place_of_receipt_by_pre_carrier = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pl_place_of_receipt_by_pre_carrier",
        null=True,
        blank=True,
    )
    vessel_flight_no = models.CharField(max_length=100, blank=True, default="")
    port_of_loading = models.ForeignKey(
        "master_data.Port",
        on_delete=models.PROTECT,
        related_name="pl_port_of_loading",
        null=True,
        blank=True,
    )
    port_of_discharge = models.ForeignKey(
        "master_data.Port",
        on_delete=models.PROTECT,
        related_name="pl_port_of_discharge",
        null=True,
        blank=True,
    )
    final_destination = models.ForeignKey(
        "master_data.Location",
        on_delete=models.PROTECT,
        related_name="pl_final_destination",
        null=True,
        blank=True,
    )

    # ---- Countries (FR-14M.6) -----------------------------------------------
    country_of_origin = models.ForeignKey(
        "master_data.Country",
        on_delete=models.PROTECT,
        related_name="pl_as_origin",
        null=True,
        blank=True,
    )
    country_of_final_destination = models.ForeignKey(
        "master_data.Country",
        on_delete=models.PROTECT,
        related_name="pl_as_final_destination",
        null=True,
        blank=True,
    )

    # ---- Order References (FR-14M.2) ----------------------------------------
    # Each reference has a paired date; all are optional.
    po_number = models.CharField(max_length=100, blank=True, default="")
    po_date = models.DateField(null=True, blank=True)
    lc_number = models.CharField(max_length=100, blank=True, default="")
    lc_date = models.DateField(null=True, blank=True)
    bl_number = models.CharField(max_length=100, blank=True, default="")
    bl_date = models.DateField(null=True, blank=True)
    so_number = models.CharField(max_length=100, blank=True, default="")
    so_date = models.DateField(null=True, blank=True)
    other_references = models.CharField(max_length=255, blank=True, default="")
    other_references_date = models.DateField(null=True, blank=True)
    # Free-text supplementary description printed in the right info panel on both PDFs.
    additional_description = models.TextField(blank=True, default="")

    # ---- Payment & Terms (FR-14M.5) -----------------------------------------
    # Auto-populated from the linked PI; remain editable by Maker.
    incoterms = models.ForeignKey(
        "master_data.Incoterm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    payment_terms = models.ForeignKey(
        "master_data.PaymentTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # ---- Workflow (FR-08, FR-14M.12) ----------------------------------------
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
        related_name="created_packing_lists",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "packing_list"
        ordering = ["-created_at"]

    def __str__(self):
        return self.pl_number


class Container(models.Model):
    """
    One shipping container on a Packing List (FR-14M.4).
    gross_weight is always stored (constraint #9) and recomputed on every save
    as SUM(item.item_gross_weight) + tare_weight.
    """

    packing_list = models.ForeignKey(
        PackingList,
        on_delete=models.CASCADE,
        related_name="containers",
    )
    container_ref = models.CharField(max_length=100)
    marks_numbers = models.TextField()
    seal_number = models.CharField(max_length=100)

    # Constraint #6: 3 decimal places for all weights
    tare_weight = models.DecimalField(max_digits=12, decimal_places=3)
    # Stored computed value: SUM(item.item_gross_weight) + tare_weight (constraint #9)
    gross_weight = models.DecimalField(
        max_digits=12, decimal_places=3, default=0
    )

    class Meta:
        db_table = "container"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        """
        Recompute gross_weight before saving.
        On initial creation the items don't exist yet, so gross_weight starts
        at tare_weight and is updated again after each ContainerItem is saved.
        """
        # Sum item_gross_weight across all items already saved for this container.
        # On first save this will be 0 (no items yet); items update it on their own save().
        if self.pk:
            items_total = sum(
                item.item_gross_weight for item in self.items.all()
            )
        else:
            items_total = 0
        self.gross_weight = items_total + self.tare_weight
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.packing_list.pl_number} | {self.container_ref}"


class ContainerItem(models.Model):
    """
    One commodity line within a container (FR-14M.8A).
    item_gross_weight is stored and computed on save as net_weight + inner_packing_weight.
    item_code + uom is the aggregation key used in the Final Rates section (FR-14M.8B).
    """

    HSN_REGEX = re.compile(r"^[0-9]{2}([0-9]{2}([0-9]{2}([0-9]{2})?)?)?$")

    container = models.ForeignKey(
        Container,
        on_delete=models.CASCADE,
        related_name="items",
    )
    hsn_code = models.CharField(max_length=8, blank=True, default="")
    # item_code is mandatory — it is the aggregation key for Final Rates and the CI.
    item_code = models.CharField(max_length=100)
    # "No & Kind of Packages" e.g. "10 Boxes", "5 Pallets"
    packages_kind = models.CharField(max_length=255)
    description = models.TextField()
    batch_details = models.CharField(max_length=255, blank=True, default="")

    # Constraint #7: PROTECT on UOM FK
    uom = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
    )
    # Constraint #6: 3 decimal places for quantity and all weights
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    net_weight = models.DecimalField(max_digits=12, decimal_places=3)
    inner_packing_weight = models.DecimalField(max_digits=12, decimal_places=3)
    # Stored computed value: net_weight + inner_packing_weight
    item_gross_weight = models.DecimalField(
        max_digits=12, decimal_places=3, editable=False, default=0
    )

    class Meta:
        db_table = "container_item"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        """
        Compute item_gross_weight before saving, then propagate the change up
        to the parent Container so its gross_weight stays accurate.
        """
        self.item_gross_weight = self.net_weight + self.inner_packing_weight
        super().save(*args, **kwargs)
        # Recompute the parent container's gross_weight to reflect this item's weight.
        self.container.save()

    def __str__(self):
        return f"{self.container} | {self.item_code}"
