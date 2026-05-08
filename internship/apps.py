from django.apps import AppConfig


class InternshipConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "internship"
    verbose_name = "Staj ve Personel Yönetimi"

    def ready(self):
        # İleride sinyal, grup oluşturma vs. yazmak istersen
        # buraya import edersin. ŞİMDİLİK BOŞ KALSIN.
        pass
