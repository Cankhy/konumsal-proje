from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import secrets
import string

from .forms import (
    InternApplicationForm,
    ApplicationForm,
    ApplicationQueryForm,
    InternLogForm,
    DailyLogForm,
)

from .models import (
    Application,
    InternLog,
    LogReview,
    Log,
    InternApplication,
    DailyLog,
    PersonnelProfile,
    Review,
    Announcement,
    ConversationMessage,
)
from .mail_utils import send_intern_credentials_email

User = get_user_model()

INTERNSHIP_TASKS = [
    {
        "week": "1. Hafta",
        "title": "Oryantasyon ve araç kurulumu",
        "duration": "3-5 gün",
        "detail": "Kurum yapısını tanı, hesaplarını tamamla, geliştirme araçlarını kur ve ilk günlük kaydını oluştur.",
    },
    {
        "week": "2. Hafta",
        "title": "Kod okuma ve küçük görev",
        "duration": "5 iş günü",
        "detail": "Mevcut projeyi incele, ilgili modülün notlarını çıkar ve küçük bir düzeltme/geliştirme görevi tamamla.",
    },
    {
        "week": "3. Hafta",
        "title": "Uygulama geliştirme",
        "duration": "7 iş günü",
        "detail": "Personelinin verdiği görevi parçalara ayır, günlük ilerleme yaz ve test sonuçlarını ekle.",
    },
    {
        "week": "4. Hafta",
        "title": "Teslim, rapor ve sunum",
        "duration": "3-4 gün",
        "detail": "Yaptığın işleri toparla, eksiklerini kapat, final raporu ve kısa sunum hazırlığını tamamla.",
    },
]


# =========================
# ESKİ BAŞVURU AKIŞI
# =========================
def application_create_view(request):
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Başvurunuz başarıyla alındı. Teşekkür ederiz.")
            return redirect("internship:intern_apply")
    else:
        form = ApplicationForm()

    return render(request, "internship/application_form.html", {"form": form})


def application_query_view(request):
    application = None
    form = ApplicationQueryForm(request.GET or None)

    if form.is_valid():
        tc = form.cleaned_data.get("tc_kimlik") or form.cleaned_data.get("tc_no")
        phone = form.cleaned_data.get("phone")
        try:
            application = Application.objects.get(tc_kimlik=tc, phone=phone)
        except Application.DoesNotExist:
            messages.error(request, "Bu bilgilere ait başvuru bulunamadı.")

    return render(
        request,
        "internship/application_query.html",
        {"form": form, "application": application},
    )


@login_required
def intern_log_create_view(request):
    if request.method == "POST":
        form = InternLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.created_by = request.user
            log.save()
            messages.success(request, "Günlük kaydedildi.")
            return redirect("internship:intern_logs")
    else:
        form = InternLogForm()

    return render(request, "internship/log_form.html", {"form": form})


@login_required
def intern_log_list_view(request):
    logs = InternLog.objects.select_related("application").filter(created_by=request.user)
    return render(request, "internship/log_list.html", {"logs": logs})


# =========================
# ESKİ PANEL GİRİŞİ
# =========================
class PanelLoginView(LoginView):
    template_name = "internship/panel_login.html"


panel_login_view = PanelLoginView.as_view()


def is_admin(user):
    return getattr(user, "role", None) == "ADMIN" or user.is_superuser


@user_passes_test(is_admin)
def dashboard_view(request):
    total_applications = Application.objects.count()
    pending = Application.objects.filter(status=Application.Status.PENDING).count()
    approved = Application.objects.filter(status=Application.Status.APPROVED).count()
    rejected = Application.objects.filter(status=Application.Status.REJECTED).count()

    context = {
        "total_applications": total_applications,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }
    return render(request, "internship/dashboard.html", context)


@user_passes_test(is_admin)
def application_list_view(request):
    applications = Application.objects.all()
    return render(request, "internship/application_list.html", {"applications": applications})


# =========================
# PERSONEL KONTROLÜ + YARDIMCILAR
# =========================
def is_personnel(user):
    return user.is_authenticated and user.groups.filter(name="Personel").exists()


def _gen_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _slug(text: str) -> str:
    text = (text or "").lower()
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr_map)
    allowed = string.ascii_lowercase + string.digits
    cleaned = "".join(ch for ch in text if ch in allowed)
    return cleaned or "stajyer"


def _unique_username(first_name, last_name):
    base = (_slug(first_name) + _slug(last_name))[:16]
    while True:
        suf = secrets.token_hex(2)
        username = f"{base}{suf}"
        if not User.objects.filter(username=username).exists():
            return username


def _is_stajyer_user(user):
    if not user.is_authenticated:
        return False

    in_group = user.groups.filter(name="Stajyer").exists()
    has_application = False

    if getattr(user, "email", None):
        has_application = InternApplication.objects.filter(email=user.email).exists()

    return in_group or has_application


def _get_intern_application_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return None

    application = InternApplication.objects.filter(user=user).order_by("-created_at").first()
    if application:
        return application

    if getattr(user, "email", None):
        return InternApplication.objects.filter(email=user.email).order_by("-created_at").first()

    return None


def _redirect_if_password_change_required(request):
    application = _get_intern_application_for_user(request.user)
    if application and application.must_change_password:
        messages.info(
            request,
            "Güvenlik gereği, devam etmeden önce şifrenizi değiştirmeniz gerekmektedir."
        )
        return redirect("website:intern_password_change")
    return None


# =========================
# PERSONEL PANELİ
# =========================
@login_required
@user_passes_test(is_personnel)
def panel_applications(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    applications = InternApplication.objects.select_related("user", "supervisor").order_by("-created_at")
    if personnel:
        applications = applications.filter(Q(supervisor=personnel) | Q(supervisor__isnull=True))
    stats = {
        "total": applications.count(),
        "pending": applications.filter(status="pending").count(),
        "approved": applications.filter(status="approved").count(),
        "rejected": applications.filter(status="rejected").count(),
    }
    return render(
        request,
        "panel/applications_list.html",
        {
            "applications": applications,
            "stats": stats,
        },
    )


@login_required
@user_passes_test(is_personnel)
def panel_application_approve(request, pk):
    app = get_object_or_404(InternApplication, pk=pk)
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()

    if getattr(app, "user_id", None):
        app.status = "approved"
        if personnel and not app.supervisor_id:
            app.supervisor = personnel
            app.save(update_fields=["status", "supervisor"])
        else:
            app.save(update_fields=["status"])
        messages.success(request, f"Başvuru #{app.id} onaylandı (hesap zaten vardı).")
        return redirect("internship:panel_applications")

    stajyer_group, _ = Group.objects.get_or_create(name="Stajyer")

    username = _unique_username(app.first_name, app.last_name)
    password = _gen_password()

    user = User.objects.create_user(username=username, password=password)
    user.is_staff = False
    user.is_superuser = False
    if app.email:
        user.email = app.email
    user.save()
    user.groups.add(stajyer_group)

    if hasattr(app, "user"):
        app.user = user
    if hasattr(app, "account_created_at"):
        app.account_created_at = timezone.now()
    if hasattr(app, "credentials_sent"):
        app.credentials_sent = False
    if hasattr(app, "must_change_password"):
        app.must_change_password = True

    app.status = "approved"
    if personnel and not app.supervisor_id:
        app.supervisor = personnel
    app.save()

    if app.email:
        try:
            sent, error_message = send_intern_credentials_email(app, username, password)
            if sent:
                app.credentials_sent = True
                app.save(update_fields=["credentials_sent"])
                messages.success(request, "Giriş bilgileri e-posta ile gönderildi.")
            elif error_message:
                messages.warning(request, f"Giriş bilgileri oluşturuldu ancak mail gönderilemedi: {error_message}")
        except Exception as exc:
            messages.warning(request, f"Giriş bilgileri oluşturuldu ancak mail gönderilemedi: {exc}")
    else:
        messages.warning(request, "Başvuruda e-posta adresi olmadığı için mail gönderilmedi.")

    messages.success(
        request,
        f"Başvuru #{app.id} onaylandı. Kullanıcı: {username} | Şifre: {password}"
    )
    return redirect("internship:panel_applications")


@login_required
@user_passes_test(is_personnel)
def panel_application_reject(request, pk):
    app = get_object_or_404(InternApplication, pk=pk)
    app.status = "rejected"
    app.save(update_fields=["status"])
    messages.warning(request, f"Başvuru #{app.id} reddedildi.")
    return redirect("internship:panel_applications")


@login_required
@user_passes_test(is_personnel)
def panel_logs_list(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    logs = (
        DailyLog.objects.select_related("application", "application__supervisor")
        .annotate(review_count=Count("reviews"))
        .prefetch_related("reviews")
        .order_by("-date", "-created_at")
    )
    if personnel:
        logs = logs.filter(application__supervisor=personnel)
    stats = {
        "total": logs.count(),
        "reviewed": logs.filter(reviews__isnull=False).distinct().count(),
        "pending": logs.filter(reviews__isnull=True).count(),
    }
    return render(
        request,
        "panel/logs_list.html",
        {
            "logs": logs,
            "stats": stats,
        },
    )


@login_required
@user_passes_test(is_personnel)
def panel_log_review(request, pk):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    logs = DailyLog.objects.select_related("application", "application__supervisor")
    if personnel:
        logs = logs.filter(application__supervisor=personnel)
    log = get_object_or_404(logs, pk=pk)
    existing_review = log.reviews.order_by("-created_at").first()

    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        comment = request.POST.get("comment", "").strip()
        if 0 < score <= 10:
            if existing_review:
                existing_review.score = score
                existing_review.comment = comment
                existing_review.reviewer = request.user
                existing_review.save(update_fields=["score", "comment", "reviewer"])
            else:
                Review.objects.create(
                    log=log,
                    reviewer=request.user,
                    score=score,
                    comment=comment,
                )
            messages.success(request, "Günlük başarıyla değerlendirildi.")
        else:
            messages.error(request, "Geçerli bir puan giriniz.")
        return redirect("internship:panel_logs_list")

    return render(
        request,
        "panel/log_review.html",
        {
            "log": log,
            "existing_review": existing_review,
        },
    )


def _save_conversation_message(request, application):
    message = (request.POST.get("message") or "").strip()
    attachment = request.FILES.get("attachment")
    if not message and not attachment:
        messages.error(request, "Mesaj veya dosya eklemelisiniz.")
        return False

    ConversationMessage.objects.create(
        application=application,
        sender=request.user,
        message=message,
        attachment=attachment,
    )
    return True


def _mark_conversation_read(application, user):
    ConversationMessage.objects.filter(
        application=application,
        read_at__isnull=True,
    ).exclude(sender=user).update(read_at=timezone.now())


@login_required
@user_passes_test(is_personnel)
def panel_conversation(request, pk):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    applications = InternApplication.objects.select_related("user", "supervisor")
    if personnel:
        applications = applications.filter(supervisor=personnel)
    application = get_object_or_404(applications, pk=pk)

    if request.method == "POST":
        if _save_conversation_message(request, application):
            return redirect("internship:panel_conversation", pk=application.pk)

    _mark_conversation_read(application, request.user)
    conversations = ConversationMessage.objects.filter(application=application).select_related("sender")
    return render(
        request,
        "internship/conversation.html",
        {
            "application": application,
            "conversations": conversations,
            "mode": "personnel",
        },
    )


# =========================
# STAJYER LOG EKLEME
# =========================
def intern_log_create(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Log.objects.create(intern=request.user, content=content)
            messages.success(request, "Günlük kaydı oluşturuldu.")
            return redirect("internship:intern_logs")

    logs = Log.objects.filter(intern=request.user).order_by("-date")
    return render(request, "panel/intern_logs.html", {"logs": logs})


# =========================
# YENİ STAJ BAŞVURU AKIŞI
# =========================
def intern_apply(request):
    if request.method == "POST":
        form = InternApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            messages.success(request, "Başvurunuz başarıyla alınmıştır.")
            return render(request, "internship/apply_success.html", {"application": application})
    else:
        form = InternApplicationForm()

    return render(request, "internship/apply.html", {"form": form})


def intern_application_query(request):
    result = None

    if request.method == "POST":
        form = ApplicationQueryForm(request.POST)
        if form.is_valid():
            tc_no = form.cleaned_data.get("tc_no") or form.cleaned_data.get("tc_kimlik")
            phone = form.cleaned_data.get("phone")

            try:
                result = InternApplication.objects.get(tc_no=tc_no, phone=phone)
            except InternApplication.DoesNotExist:
                messages.error(request, "Bu bilgilerle kayıtlı bir başvuru bulunamadı.")
    else:
        form = ApplicationQueryForm()

    return render(request, "internship/query.html", {"form": form, "result": result})


def intern_daily_log(request):
    if not request.user.is_authenticated:
        messages.info(request, "Günlük girişi için önce stajyer hesabınızla giriş yapmalısınız.")
        return redirect(f"{reverse('website:intern_login')}?next={reverse('internship:intern_daily_log')}")

    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)
    if not application:
        messages.error(request, "Hesabınıza bağlı bir staj başvurusu bulunamadı.")
        return redirect("internship:intern_dashboard")

    if request.method == "POST":
        form = DailyLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.application = application

            existing_log = DailyLog.objects.filter(application=application, date=log.date).first()
            if existing_log:
                messages.error(request, "Aynı tarih için daha önce günlük kaydı oluşturulmuş.")
            else:
                log.save()
                messages.success(request, "Günlük kaydınız başarıyla oluşturuldu.")
                return redirect("internship:intern_daily_logs")
    else:
        form = DailyLogForm()

    last_log = DailyLog.objects.filter(application=application).order_by("-date", "-created_at").first()
    return render(
        request,
        "internship/daily_log.html",
        {
            "form": form,
            "application": application,
            "last_log": last_log,
            "internship_tasks": INTERNSHIP_TASKS,
        },
    )


# =========================
# STAJ PORTALI ANA SAYFA
# =========================
def intern_portal(request):
    return render(request, "internship/login_choice.html")


# =========================
# STAJYER PANELİ
# =========================
@login_required
def intern_dashboard_view(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)
    last_logs = DailyLog.objects.none()
    logs_count = 0
    reviewed_logs_count = 0

    if application:
        last_logs = DailyLog.objects.filter(application=application).order_by("-date", "-created_at")[:5]
        logs_count = DailyLog.objects.filter(application=application).count()
        reviewed_logs_count = DailyLog.objects.filter(application=application, reviews__isnull=False).distinct().count()
        unread_messages_count = ConversationMessage.objects.filter(
            application=application,
            read_at__isnull=True,
        ).exclude(sender=request.user).count()
    else:
        unread_messages_count = 0

    announcements = Announcement.objects.filter(is_active=True).order_by("-created_at")[:5]

    context = {
        "application": application,
        "last_logs": last_logs,
        "logs_count": logs_count,
        "reviewed_logs_count": reviewed_logs_count,
        "unread_messages_count": unread_messages_count,
        "announcements": announcements,
        "internship_tasks": INTERNSHIP_TASKS,
    }
    return render(request, "internship/intern_dashboard.html", context)


@login_required
def intern_application_detail_view(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)

    return render(
        request,
        "internship/intern_application_detail.html",
        {"application": application},
    )


@login_required
def intern_daily_logs_view(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = None
    logs = DailyLog.objects.none()

    application = _get_intern_application_for_user(request.user)

    if application:
        logs = DailyLog.objects.filter(application=application).prefetch_related("reviews__reviewer").order_by("-date", "-created_at")

    return render(
        request,
        "internship/intern_daily_logs.html",
        {
            "application": application,
            "logs": logs,
            "internship_tasks": INTERNSHIP_TASKS,
        },
    )


@login_required
def intern_conversation_view(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)
    if not application or not application.supervisor_id:
        messages.warning(request, "Mesajlaşma için önce sorumlu personel eşleşmesi yapılmalıdır.")
        return redirect("internship:intern_dashboard")

    if request.method == "POST":
        if _save_conversation_message(request, application):
            return redirect("internship:intern_conversation")

    _mark_conversation_read(application, request.user)
    conversations = ConversationMessage.objects.filter(application=application).select_related("sender")
    return render(
        request,
        "internship/conversation.html",
        {
            "application": application,
            "conversations": conversations,
            "mode": "intern",
        },
    )


@login_required
def intern_documents_view(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu kullanıcı için aktif stajyer yetkisi bulunamadı.")
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    documents = [
        {
            "title": "Staj Sözleşmesi Örneği",
            "description": "Kuruma teslim edilecek standart staj sözleşmesi şablonu.",
            "url": "/static/docs/staj_sozlesmesi.pdf",
        },
        {
            "title": "Günlük Formu",
            "description": "İmza için çıktı alınabilecek günlük formu.",
            "url": "/static/docs/gunluk_formu.pdf",
        },
    ]
    return render(
        request,
        "internship/intern_documents.html",
        {"documents": documents},
    )
