from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["home_currency"], name="user_home_currency_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email_verified"], name="user_email_verified_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["home_currency", "email_verified"], name="user_curr_email_idx"),
        ),
    ]
