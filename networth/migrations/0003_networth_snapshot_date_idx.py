from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("networth", "0002_alter_networthsnapshot_currency_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="networthsnapshot",
            index=models.Index(fields=["snapshot_date"], name="networth_snapshot_date_idx"),
        ),
    ]
