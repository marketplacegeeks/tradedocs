from django.db import migrations


TEST_PARAMETERS = [
    "Appearance",
    "Colour",
    "Purity",
    "Methylene Chloride",
    "Carbon Tetrachloride",
    "Residue on evaporation",
    "Acidity as HCl",
    "Free chlorine",
    "Moisture",
    "Amylene as Stabilizer",
    "Bromo Chloromethane",
]

TEST_METHODS = [
    ("ASTM D3741-00", ""),
    ("ASTM D2108-10", ""),
    ("ASTM D6806-02 / IS 5296-K", ""),
    ("ASTM D6806-02", ""),
    ("ASTM D2109-01 IS 5296-C", ""),
    ("ASTM D2989-01 IS 5296-E", ""),
    ("IS 5296-D", ""),
    ("ASTM D3401 / IS 5296-J", ""),
    ("In house", ""),
]


def seed_data(apps, schema_editor):
    TestParameter = apps.get_model("master_data", "TestParameter")
    TestMethod = apps.get_model("master_data", "TestMethod")

    for name in TEST_PARAMETERS:
        TestParameter.objects.get_or_create(name=name, defaults={"is_active": True})

    for code, description in TEST_METHODS:
        TestMethod.objects.get_or_create(code=code, defaults={"description": description, "is_active": True})


def unseed_data(apps, schema_editor):
    TestParameter = apps.get_model("master_data", "TestParameter")
    TestMethod = apps.get_model("master_data", "TestMethod")

    TestParameter.objects.filter(name__in=TEST_PARAMETERS).delete()
    TestMethod.objects.filter(code__in=[code for code, _ in TEST_METHODS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0018_coa_master_data"),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=unseed_data),
    ]
