from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("internship", "0004_internapplication_account_created_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="internapplication",
            name="must_change_password",
            field=models.BooleanField(default=False, verbose_name="İlk girişte şifre değişimi zorunlu"),
        ),
        migrations.AlterUniqueTogether(
            name="dailylog",
            unique_together={("application", "date")},
        ),
        migrations.AlterModelOptions(
            name="dailylog",
            options={"ordering": ["-date", "-created_at"]},
        ),
    ]
