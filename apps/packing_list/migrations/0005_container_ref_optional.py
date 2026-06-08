from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("packing_list", "0004_containeritem_packaging_redesign"),
    ]

    operations = [
        migrations.AlterField(
            model_name="container",
            name="container_ref",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
