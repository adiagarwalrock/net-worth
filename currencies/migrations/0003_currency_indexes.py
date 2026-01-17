from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("currencies", "0002_exchangerate_currencies__from_cu_7d8f00_idx"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="currency",
            index=models.Index(fields=["is_active"], name="currency_is_active_idx"),
        ),
        migrations.AddIndex(
            model_name="exchangerate",
            index=models.Index(fields=["to_currency", "-date"], name="exchange_rate_to_currency_idx"),
        ),
    ]
