from django.db import migrations


def backfill_application_history(apps, schema_editor):
    InternApplication = apps.get_model("internship", "InternApplication")
    ApplicationStatusHistory = apps.get_model("internship", "ApplicationStatusHistory")
    for application in InternApplication.objects.all():
        if not ApplicationStatusHistory.objects.filter(application=application).exists():
            ApplicationStatusHistory.objects.create(
                application=application,
                actor=None,
                from_status="",
                to_status=application.status,
                note="Mevcut kayıt için geçmiş başlangıcı otomatik oluşturuldu.",
            )


class Migration(migrations.Migration):
    dependencies = [
        ("internship", "0012_formerrorlog_conversationmessage_attachment_kind_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_application_history, migrations.RunPython.noop),
    ]
