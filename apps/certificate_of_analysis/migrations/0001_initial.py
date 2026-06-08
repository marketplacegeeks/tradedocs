import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("master_data", "0018_coa_master_data"),
        ("accounts", "0004_create_super_admin_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CertificateOfAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("coa_number", models.CharField(max_length=20, unique=True)),
                ("batch_number", models.CharField(max_length=100)),
                ("package_count", models.PositiveIntegerField()),
                ("package_volume", models.DecimalField(decimal_places=3, max_digits=12)),
                ("date_of_despatch", models.DateField(blank=True, null=True)),
                ("date_of_manufacture", models.DateField()),
                ("date_of_retest", models.DateField()),
                ("date_time_of_sampling", models.DateTimeField()),
                ("date_time_of_analysis", models.DateTimeField()),
                ("analyst_name", models.CharField(max_length=150)),
                ("qc_incharge_name", models.CharField(max_length=150)),
                ("status", models.CharField(
                    choices=[
                        ("DRAFT", "Draft"),
                        ("PENDING_APPROVAL", "Pending Approval"),
                        ("APPROVED", "Approved"),
                        ("REWORK", "Rework"),
                        ("PERMANENTLY_REJECTED", "Permanently Rejected"),
                    ],
                    db_index=True,
                    default="DRAFT",
                    max_length=30,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product_grade", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coas",
                    to="master_data.productgrade",
                )),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_as_customer",
                    to="master_data.organisation",
                )),
                ("package_uom", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_package_uom",
                    to="master_data.uom",
                )),
                ("package_type", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coas",
                    to="master_data.typeofpackage",
                )),
                ("footer_organisation", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_as_footer",
                    to="master_data.organisation",
                )),
                ("created_by", models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="created_coas",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "certificate_of_analysis", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="COAParameter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("s_no", models.PositiveIntegerField()),
                ("parameter_label", models.CharField(max_length=255)),
                ("spec_type", models.CharField(
                    choices=[("QUANTITATIVE", "Quantitative"), ("QUALITATIVE", "Qualitative")],
                    max_length=20,
                )),
                ("spec_min", models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ("spec_max", models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ("spec_description", models.TextField(blank=True)),
                ("result_value", models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ("result_text", models.CharField(blank=True, max_length=100)),
                ("test_method_label", models.CharField(blank=True, max_length=100)),
                ("coa", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="parameters",
                    to="certificate_of_analysis.certificateofanalysis",
                )),
                ("parameter", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_parameters",
                    to="master_data.testparameter",
                )),
                ("unit", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_parameters",
                    to="master_data.uom",
                )),
                ("test_method", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="coa_parameters",
                    to="master_data.testmethod",
                )),
            ],
            options={"db_table": "coa_parameter", "ordering": ["s_no"]},
        ),
    ]
