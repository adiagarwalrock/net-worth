from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("households", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="household",
            index=models.Index(fields=["created_by"], name="household_created_by_idx"),
        ),
        migrations.AddIndex(
            model_name="household",
            index=models.Index(fields=["name"], name="household_name_idx"),
        ),
        migrations.AddIndex(
            model_name="householdmember",
            index=models.Index(fields=["household", "role"], name="household_member_role_idx"),
        ),
        migrations.AddIndex(
            model_name="householdmember",
            index=models.Index(fields=["user", "role"], name="household_member_user_role_idx"),
        ),
        migrations.AddIndex(
            model_name="householdmember",
            index=models.Index(fields=["household", "can_view_details"], name="household_member_access_idx"),
        ),
        migrations.AddIndex(
            model_name="householdinvitation",
            index=models.Index(fields=["household", "status"], name="hh_inv_status_idx"),
        ),
        migrations.AddIndex(
            model_name="householdinvitation",
            index=models.Index(fields=["email", "status"], name="hh_inv_email_status_idx"),
        ),
    ]
