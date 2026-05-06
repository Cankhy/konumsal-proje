from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("internship", "0005_internapplication_must_change_password_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonnelProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=50, verbose_name="Ad")),
                ("last_name", models.CharField(max_length=50, verbose_name="Soyad")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-posta")),
                ("phone", models.CharField(blank=True, max_length=15, verbose_name="Telefon")),
                ("title", models.CharField(blank=True, max_length=80, verbose_name="Görev / Ünvan")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("account_created_at", models.DateTimeField(null=True, blank=True, verbose_name="Hesap Oluşturulma")),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="personnel_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Oluşturulan Kullanıcı",
                    ),
                ),
            ],
            options={
                "verbose_name": "Personel Hesabı",
                "verbose_name_plural": "Personel Hesapları",
                "ordering": ["first_name", "last_name"],
            },
        ),
        migrations.AddField(
            model_name="internapplication",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="intern_applications",
                to="internship.personnelprofile",
                verbose_name="Sorumlu Personel",
            ),
        ),
    ]
