from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("internship", "0006_personnelprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="internapplication",
            name="cv_file",
            field=models.FileField(blank=True, null=True, upload_to="intern_cvs/", verbose_name="CV"),
        ),
    ]
