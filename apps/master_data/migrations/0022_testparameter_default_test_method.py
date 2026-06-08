from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0021_remove_test_method_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="testparameter",
            name="default_test_method",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="test_parameters",
                to="master_data.testmethod",
            ),
        ),
    ]
