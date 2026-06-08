from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("certificate_of_analysis", "0003_remove_test_method_label"),
        ("packing_list", "0004_containeritem_packaging_redesign"),
    ]

    operations = [
        migrations.AddField(
            model_name="certificateofanalysis",
            name="packing_list",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="coas",
                to="packing_list.packinglist",
            ),
        ),
    ]
