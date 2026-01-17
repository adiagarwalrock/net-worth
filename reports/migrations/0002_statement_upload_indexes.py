from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="statementupload",
            index=models.Index(fields=["upload_type", "-uploaded_at"], name="statement_upload_type_idx"),
        ),
        migrations.AddIndex(
            model_name="statementupload",
            index=models.Index(fields=["user", "status"], name="statement_user_status_idx"),
        ),
    ]
