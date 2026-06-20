from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("certificate_of_analysis", "0004_coa_packing_list"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coaparameter",
            name="spec_min",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="coaparameter",
            name="spec_max",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="coaparameter",
            name="result_value",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
