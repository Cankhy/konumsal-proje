from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("internship", "0010_conversationmessage_read_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonnelTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140, verbose_name="Görev Başlığı")),
                ("details", models.TextField(blank=True, verbose_name="Görev Açıklaması")),
                ("task_date", models.DateField(default=django.utils.timezone.localdate, verbose_name="Görev Günü")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("is_completed", models.BooleanField(default=False, verbose_name="Tamamlandı")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="personnel_tasks", to="internship.internapplication", verbose_name="Stajyer Eşleşmesi")),
                ("personnel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assigned_tasks", to="internship.personnelprofile", verbose_name="Görevi Veren Personel")),
            ],
            options={
                "verbose_name": "Personel Görevi",
                "verbose_name_plural": "Personel Görevleri",
                "ordering": ["task_date", "-created_at"],
            },
        ),
    ]
