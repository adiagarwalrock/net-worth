from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("liabilities", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="liability",
            index=models.Index(fields=["user", "creditor"], name="liability_user_creditor_idx"),
        ),
        migrations.AddIndex(
            model_name="liability",
            index=models.Index(fields=["currency", "is_active"], name="liability_currency_active_idx"),
        ),
        migrations.AddIndex(
            model_name="liabilityhistory",
            index=models.Index(fields=["liability", "source"], name="liability_history_source_idx"),
        ),
    ]
