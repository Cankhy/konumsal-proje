from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
import secrets
import string

from .mail_utils import send_intern_credentials_email
from .models import (
    Announcement,
    Application,
    ConversationMessage,
    DailyLog,
    InternApplication,
    InternLog,
    Log,
    LogReview,
    PersonnelProfile,
    Review,
)

User = get_user_model()


def _generate_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _slugify_basic(text: str) -> str:
    text = (text or "").lower()
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr_map)
    allowed = string.ascii_lowercase + string.digits
    cleaned = "".join(ch for ch in text if ch in allowed)
    return cleaned or "stajyer"


def _generate_unique_username(first_name: str, last_name: str) -> str:
    base = (_slugify_basic(first_name) + _slugify_basic(last_name))[:16]
    while True:
        suffix = secrets.token_hex(2)
        username = f"{base}{suffix}"
        if not User.objects.filter(username=username).exists():
            return username


@admin.register(PersonnelProfile)
class PersonnelProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "title", "email", "is_active", "user", "account_created_at")
    list_filter = ("is_active", "account_created_at")
    search_fields = ("first_name", "last_name", "email", "user__username")
    readonly_fields = ("user", "account_created_at")
    actions = ["create_personnel_accounts"]

    def create_personnel_accounts(self, request, queryset):
        personnel_group, _ = Group.objects.get_or_create(name="Personel")
        created_count = 0
        skipped_count = 0

        for profile in queryset:
            if profile.user_id:
                skipped_count += 1
                continue

            username = _generate_unique_username(profile.first_name, profile.last_name)
            password = _generate_password()
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile.email or "",
            )
            user.is_staff = False
            user.is_superuser = False
            user.save()
            user.groups.add(personnel_group)

            profile.user = user
            profile.account_created_at = timezone.now()
            profile.save(update_fields=["user", "account_created_at"])

            self.message_user(
                request,
                f"[Personel #{profile.id}] kullanıcı: {username} | şifre: {password}",
                level="SUCCESS",
            )
            created_count += 1

        self.message_user(
            request,
            f"{created_count} personel hesabı oluşturuldu. {skipped_count} kayıt atlandı.",
        )

    create_personnel_accounts.short_description = "Seçili personeller için kullanıcı adı + şifre oluştur"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "tc_kimlik",
        "phone",
        "school",
        "status",
        "created_at",
    )
    search_fields = ("first_name", "last_name", "tc_kimlik", "phone", "school")
    list_filter = ("status", "school", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    actions = ["approve_applications", "reject_applications"]

    def approve_applications(self, request, queryset):
        updated = queryset.update(status=Application.Status.APPROVED)
        self.message_user(request, f"{updated} başvuru ONAYLANDI.")

    approve_applications.short_description = "Seçili başvuruları onayla"

    def reject_applications(self, request, queryset):
        updated = queryset.update(status=Application.Status.REJECTED)
        self.message_user(request, f"{updated} başvuru REDDEDİLDİ.")

    reject_applications.short_description = "Seçili başvuruları reddet"


@admin.register(InternLog)
class InternLogAdmin(admin.ModelAdmin):
    list_display = ("application", "date", "created_by", "created_at")
    list_filter = ("date", "created_at")
    search_fields = (
        "application__first_name",
        "application__last_name",
        "application__tc_kimlik",
    )
    readonly_fields = ("created_at",)


@admin.register(LogReview)
class LogReviewAdmin(admin.ModelAdmin):
    list_display = ("log", "reviewer", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = (
        "log__application__first_name",
        "log__application__last_name",
        "reviewer__username",
    )
    readonly_fields = ("created_at",)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("intern", "date", "score", "reviewer")
    list_filter = ("date", "score")
    search_fields = ("intern__username", "intern__first_name", "intern__last_name")
    readonly_fields = ("date",)


@admin.register(InternApplication)
class InternApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "tc_no",
        "phone",
        "school",
        "department",
        "status",
        "created_at",
        "user",
        "account_created_at",
        "credentials_sent",
        "must_change_password",
        "supervisor",
        "cv_file",
    )
    search_fields = ("first_name", "last_name", "tc_no", "phone", "school", "email")
    list_filter = ("status", "supervisor", "school", "department", "created_at", "credentials_sent", "must_change_password")
    readonly_fields = ("created_at", "account_created_at", "user", "credentials_sent")
    actions = ["approve_interns_create_accounts", "reject_interns"]

    def approve_interns_create_accounts(self, request, queryset):
        stajyer_group, _ = Group.objects.get_or_create(name="Stajyer")
        created_count = 0
        skipped_count = 0

        for app in queryset:
            if getattr(app, "user_id", None):
                skipped_count += 1
                continue

            username = _generate_unique_username(app.first_name, app.last_name)
            password = _generate_password()

            user = User.objects.create_user(username=username, password=password)
            user.is_staff = False
            user.is_superuser = False
            if app.email:
                user.email = app.email
            user.save()
            user.groups.add(stajyer_group)

            app.status = "approved"
            app.user = user
            app.account_created_at = timezone.now()
            app.credentials_sent = False
            app.must_change_password = True
            app.save()

            self.message_user(
                request,
                f"[Başvuru #{app.id}] HESAP OLUŞTU → kullanıcı: {username} | şifre: {password}",
                level="SUCCESS",
            )

            if app.email:
                try:
                    sent, error_message = send_intern_credentials_email(app, username, password)
                    if sent:
                        app.credentials_sent = True
                        app.save(update_fields=["credentials_sent"])
                    elif error_message:
                        self.message_user(
                            request,
                            f"[Başvuru #{app.id}] Mail gönderilemedi: {error_message}",
                            level="WARNING",
                        )
                except Exception as exc:
                    self.message_user(
                        request,
                        f"[Başvuru #{app.id}] Mail gönderilemedi: {exc}",
                        level="WARNING",
                    )

            created_count += 1

        self.message_user(
            request,
            f"{created_count} başvuru ONAYLANDI + hesap açıldı. {skipped_count} adet atlandı (zaten hesabı vardı).",
        )

    approve_interns_create_accounts.short_description = "Seçili staj başvurularını ONAYLA + HESAP OLUŞTUR"

    def reject_interns(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} staj başvurusu REDDEDİLDİ.")

    reject_interns.short_description = "Seçili staj başvurularını reddet"


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ("application", "date", "task_focus", "created_at")
    list_filter = ("date", "task_focus", "created_at")
    search_fields = (
        "application__first_name",
        "application__last_name",
        "application__tc_no",
    )
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("log", "reviewer", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("reviewer__username",)
    readonly_fields = ("created_at",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target", "is_active", "created_at")
    list_filter = ("target", "is_active")
    search_fields = ("title", "message")


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ("application", "sender", "created_at", "attachment")
    list_filter = ("created_at",)
    search_fields = (
        "application__first_name",
        "application__last_name",
        "sender__username",
        "message",
    )
    readonly_fields = ("created_at",)
