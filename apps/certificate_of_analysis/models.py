from django.conf import settings
from django.db import models

from apps.workflow.constants import DRAFT, DOCUMENT_STATUS_CHOICES


class CertificateOfAnalysis(models.Model):
    """
    Certificate of Analysis (COA) — quality assurance document for chemical/pharmaceutical exports.
    Uses the standard maker-checker workflow.
    """

    coa_number = models.CharField(max_length=20, unique=True)

    # Product + grade together identify which chemical this COA covers
    product_grade = models.ForeignKey(
        "master_data.ProductGrade",
        on_delete=models.PROTECT,
        related_name="coas",
    )

    # Optional link to the Packing List this COA was raised against
    packing_list = models.ForeignKey(
        "packing_list.PackingList",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="coas",
    )

    # Customer: Organisation tagged CONSIGNEE or BUYER
    customer = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="coa_as_customer",
    )

    batch_number = models.CharField(max_length=100)
    package_count = models.PositiveIntegerField()
    # Use decimal for volume (e.g. 1000.000 ml)
    package_volume = models.DecimalField(max_digits=12, decimal_places=3)
    package_uom = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
        related_name="coa_package_uom",
    )
    package_type = models.ForeignKey(
        "master_data.TypeOfPackage",
        on_delete=models.PROTECT,
        related_name="coas",
    )

    date_of_despatch = models.DateField(null=True, blank=True)
    date_of_manufacture = models.DateField()
    date_of_retest = models.DateField()
    date_time_of_sampling = models.DateTimeField()
    date_time_of_analysis = models.DateTimeField()

    analyst_name = models.CharField(max_length=150)
    qc_incharge_name = models.CharField(max_length=150)

    # Footer organisation: Organisation tagged CONSIGNEE or EXPORTER
    footer_organisation = models.ForeignKey(
        "master_data.Organisation",
        on_delete=models.PROTECT,
        related_name="coa_as_footer",
    )

    status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_coas",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "certificate_of_analysis"
        ordering = ["-created_at"]

    def __str__(self):
        return self.coa_number


class COAParameter(models.Model):
    """
    One test result row in a COA — either quantitative or qualitative.
    """
    SPEC_TYPE_CHOICES = [
        ("QUANTITATIVE", "Quantitative"),
        ("QUALITATIVE", "Qualitative"),
    ]

    coa = models.ForeignKey(
        CertificateOfAnalysis,
        on_delete=models.CASCADE,
        related_name="parameters",
    )
    s_no = models.PositiveIntegerField()

    parameter = models.ForeignKey(
        "master_data.TestParameter",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="coa_parameters",
    )
    unit = models.ForeignKey(
        "master_data.UOM",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="coa_parameters",
    )

    spec_type = models.CharField(max_length=20, choices=SPEC_TYPE_CHOICES)

    # Decimal precision 6 for trace-level chemical measurements
    spec_min = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    spec_max = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    spec_description = models.TextField(blank=True)

    result_value = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    result_text = models.CharField(max_length=100, blank=True)

    test_method = models.ForeignKey(
        "master_data.TestMethod",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="coa_parameters",
    )

    class Meta:
        db_table = "coa_parameter"
        ordering = ["s_no"]

    def __str__(self):
        return f"{self.coa.coa_number} | Row {self.s_no}: {self.parameter.name if self.parameter else ''}"
