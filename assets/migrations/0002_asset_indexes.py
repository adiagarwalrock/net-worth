from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="asset",
            index=models.Index(fields=["currency", "is_active"], name="asset_currency_active_idx"),
        ),
        migrations.AddIndex(
            model_name="assethistory",
            index=models.Index(fields=["asset", "source"], name="asset_history_source_idx"),
        ),
    ]
