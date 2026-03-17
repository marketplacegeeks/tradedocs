import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("master_data", "0006_bank_intermediary_organisation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProformaInvoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pi_number", models.CharField(max_length=20, unique=True)),
                ("pi_date", models.DateField()),
                ("buyer_order_no", models.CharField(blank=True, default="", max_length=100)),
                ("buyer_order_date", models.DateField(blank=True, null=True)),
                ("other_references", models.TextField(blank=True, default="")),
                ("vessel_flight_no", models.CharField(blank=True, default="", max_length=100)),
                ("validity_for_acceptance", models.DateField(blank=True, null=True)),
                ("validity_for_shipment", models.DateField(blank=True, null=True)),
                ("partial_shipment", models.CharField(blank=True, choices=[("ALLOWED", "Allowed"), ("NOT_ALLOWED", "Not Allowed")], default="", max_length=20)),
                ("transshipment", models.CharField(blank=True, choices=[("ALLOWED", "Allowed"), ("NOT_ALLOWED", "Not Allowed")], default="", max_length=20)),
                ("tc_content", models.TextField(blank=True, default="")),
                ("freight", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("insurance_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("import_duty", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("destination_charges", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("PENDING_APPROVAL", "Pending Approval"), ("APPROVED", "Approved"), ("REWORK", "Rework"), ("PERMANENTLY_REJECTED", "Permanently Rejected"), ("DISABLED", "Disabled")], db_index=True, default="DRAFT", max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("bank", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.bank")),
                ("buyer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_as_buyer", to="master_data.organisation")),
                ("consignee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pi_as_consignee", to="master_data.organisation")),
                ("country_of_final_destination", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_as_final_destination", to="master_data.country")),
                ("country_of_origin", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_as_origin", to="master_data.country")),
                ("created_by", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name="created_proforma_invoices", to=settings.AUTH_USER_MODEL)),
                ("exporter", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pi_as_exporter", to="master_data.organisation")),
                ("final_destination", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_final_destination", to="master_data.location")),
                ("incoterms", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.incoterm")),
                ("payment_terms", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.paymentterm")),
                ("place_of_receipt", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_place_of_receipt", to="master_data.location")),
                ("port_of_discharge", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_port_of_discharge", to="master_data.port")),
                ("port_of_loading", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pi_port_of_loading", to="master_data.port")),
                ("pre_carriage_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.precarriageby")),
                ("tc_template", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.tctemplate")),
            ],
            options={"db_table": "proforma_invoice", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ProformaInvoiceLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hsn_code", models.CharField(blank=True, default="", max_length=8)),
                ("item_code", models.CharField(blank=True, default="", max_length=100)),
                ("description", models.TextField()),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=12)),
                ("rate_usd", models.DecimalField(decimal_places=2, max_digits=15)),
                ("amount_usd", models.DecimalField(decimal_places=2, editable=False, max_digits=15)),
                ("pi", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="proforma_invoice.proformainvoice")),
                ("uom", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="master_data.uom")),
            ],
            options={"db_table": "proforma_invoice_line_item", "ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="ProformaInvoiceCharge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=255)),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=15)),
                ("pi", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="charges", to="proforma_invoice.proformainvoice")),
            ],
            options={"db_table": "proforma_invoice_charge", "ordering": ["id"]},
        ),
    ]
