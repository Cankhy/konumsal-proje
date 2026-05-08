import json
import secrets
import string

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .file_security import CHAT_IMAGE_RULE, CHAT_WORD_RULE, DOCUMENT_RULES, validate_uploaded_file
from .forms import (
    ApplicationBulkActionForm,
    ApplicationForm,
    ApplicationQueryForm,
    DailyLogForm,
    DocumentReviewForm,
    InternApplicationForm,
    InternDocumentUploadForm,
    InternLogForm,
    PersonnelTaskForm,
    ReviewForm,
    TaskCommentForm,
    log_form_errors,
)
from .mail_utils import send_intern_credentials_email
from .models import (
    Announcement,
    Application,
    ApplicationStatusHistory,
    ConversationMessage,
    DailyLog,
    FormErrorLog,
    InternApplication,
    InternDocument,
    InternLog,
    Log,
    LogReview,
    PersonnelProfile,
    PersonnelTask,
    PersonnelTaskComment,
    Review,
)

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

DOCUMENT_REQUIREMENTS = [
    {
        "category": InternDocument.Category.INTERN_AGREEMENT,
        "title": "Staj Sözleşmesi",
        "description": "Kurum ve okul onaylı sözleşme dosyanı PDF olarak yükle.",
    },
    {
        "category": InternDocument.Category.DAILY_FORM,
        "title": "İmzalı Günlük Formu",
        "description": "İmzalı günlük formunu PDF olarak yükle.",
    },
    {
        "category": InternDocument.Category.REPORT,
        "title": "Staj Raporu",
        "description": "Final staj raporunu PDF olarak sisteme ekle.",
    },
    {
        "category": InternDocument.Category.PRESENTATION,
        "title": "Sunum Dosyası",
        "description": "Sunum dosyanı PDF olarak yükle.",
    },
]


def _gen_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _slug(text: str) -> str:
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = (text or "").lower().translate(tr_map)
    allowed = string.ascii_lowercase + string.digits
    cleaned = "".join(ch for ch in text if ch in allowed)
    return cleaned or "stajyer"


def _unique_username(first_name, last_name):
    base = (_slug(first_name) + _slug(last_name))[:16]
    while True:
        username = f"{base}{secrets.token_hex(2)}"
        if not User.objects.filter(username=username).exists():
            return username


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def is_personnel(user):
    return user.is_authenticated and user.groups.filter(name="Personel").exists()


def _is_stajyer_user(user):
    if not user.is_authenticated or user.is_superuser or is_personnel(user):
        return False
    if user.groups.filter(name="Stajyer").exists():
        return True
    if getattr(user, "email", None):
        return InternApplication.objects.filter(email=user.email).exists()
    return False


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
        messages.info(request, "Güvenlik gereği, devam etmeden önce şifrenizi değiştirmeniz gerekmektedir.")
        return redirect("website:intern_password_change")
    return None


def _require_personnel(request):
    if not is_personnel(request.user):
        messages.error(request, "Bu alan yalnızca yetkili personel için kullanılabilir.")
        return False
    return True


def _require_intern(request):
    if not _is_stajyer_user(request.user):
        messages.error(request, "Bu alan yalnızca aktif stajyer hesabı ile kullanılabilir.")
        return False
    return True


def _record_application_history(application, actor, to_status, note=""):
    from_status = application.status
    if from_status == to_status and not note:
        return
    ApplicationStatusHistory.objects.create(
        application=application,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
        note=note,
    )
    application.status = to_status
    if to_status != "rejected":
        application.rejection_reason = ""
    elif note:
        application.rejection_reason = note
    application.save(update_fields=["status", "rejection_reason", "status_updated_at"])


def _build_daily_task_choices(application):
    choices = [("", "Bugünkü odak görevi seçin")]
    assigned_tasks = PersonnelTask.objects.filter(
        application=application,
        is_active=True,
        is_completed=False,
    ).order_by("task_date", "due_date", "-created_at")
    for task in assigned_tasks:
        due_text = f" · Teslim: {task.due_date:%d.%m.%Y}" if task.due_date else ""
        choices.append((task.title, f"Personel görevi: {task.title}{due_text}"))
    for item in [
        "Oryantasyon ve kurum tanıma",
        "Temel araç kurulumu",
        "Kod okuma ve dokümantasyon",
        "Küçük geliştirme görevi",
        "Test ve hata kontrolü",
        "Raporlama ve sunum hazırlığı",
    ]:
        choices.append((item, item))
    return choices


def _base_payload(data):
    payload = {}
    for key, value in data.items():
        if hasattr(value, "name"):
            payload[key] = getattr(value, "name", "")
        else:
            payload[key] = value
    return payload


def _log_form(form_name, request, form):
    log_form_errors(form_name, request.path, _base_payload(request.POST or {}), form.errors.get_json_data())


def _build_conversation_entries(conversations, request_user):
    entries = []
    current_date = None
    for item in conversations:
        if item.deleted_at:
            continue
        item_date = timezone.localtime(item.created_at).date()
        if item_date != current_date:
            entries.append({"type": "date", "label": item_date.strftime("%d.%m.%Y")})
            current_date = item_date
        entries.append(
            {
                "type": "message",
                "message": item,
                "is_mine": item.sender_id == request_user.id,
            }
        )
    return entries


def _save_conversation_message(request, application):
    message = (request.POST.get("message") or "").strip()
    attachment = request.FILES.get("attachment")
    attachment_mode = (request.POST.get("attachment_mode") or "image").strip().lower()
    if not message and not attachment:
        messages.error(request, "Mesaj veya dosya eklemelisiniz.")
        return False

    attachment_kind = ""
    if attachment:
        if attachment_mode == "image":
            validate_uploaded_file(attachment, CHAT_IMAGE_RULE)
            attachment_kind = "image"
        elif attachment_mode == "document":
            validate_uploaded_file(attachment, CHAT_WORD_RULE)
            attachment_kind = "document"
        else:
            messages.error(request, "Geçersiz dosya yükleme türü seçildi.")
            return False

    ConversationMessage.objects.create(
        application=application,
        sender=request.user,
        message=message,
        attachment=attachment,
        attachment_kind=attachment_kind,
    )
    return True


def _mark_conversation_read(application, user):
    ConversationMessage.objects.filter(application=application, read_at__isnull=True).exclude(sender=user).update(
        read_at=timezone.now()
    )


def _application_queryset_for_personnel(user):
    personnel = PersonnelProfile.objects.filter(user=user, is_active=True).first()
    queryset = InternApplication.objects.select_related("user", "supervisor").order_by("-created_at")
    if personnel:
        queryset = queryset.filter(Q(supervisor=personnel) | Q(supervisor__isnull=True))
    return personnel, queryset


@login_required
@user_passes_test(is_admin)
def panel_dashboard(request):
    applications = InternApplication.objects.select_related("supervisor", "user").order_by("-created_at")
    total_applications = applications.count()
    approved_applications = applications.filter(status="approved").count()
    pending_applications = applications.filter(status="pending").count()
    rejected_applications = applications.filter(status="rejected").count()
    completion_rate = round((approved_applications / total_applications) * 100) if total_applications else 0

    month_labels = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran"]
    # Placeholder chart data keeps the UI ready until month-based reporting is connected.
    chart_approved = [1, 2, 3, 4, 3, max(approved_applications, 1)]
    chart_pending = [4, 3, 4, 2, 3, max(pending_applications, 1)]
    chart_rejected = [0, 1, 0, 1, 1, rejected_applications]

    context = {
        "total_applications": total_applications,
        "approved_applications": approved_applications,
        "pending_applications": pending_applications,
        "rejected_applications": rejected_applications,
        "completion_rate": completion_rate,
        "recent_applications": applications[:5],
        "recent_logs": DailyLog.objects.select_related("application").order_by("-date", "-created_at")[:5],
        "notifications": Announcement.objects.filter(is_active=True).order_by("-created_at")[:5],
        "chart_labels_json": json.dumps(month_labels, ensure_ascii=False),
        "chart_approved_json": json.dumps(chart_approved),
        "chart_pending_json": json.dumps(chart_pending),
        "chart_rejected_json": json.dumps(chart_rejected),
    }
    return render(request, "internship/panel_dashboard.html", context)


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
    return render(request, "internship/application_query.html", {"form": form, "application": application})


@login_required
def intern_log_create_view(request):
    form = InternLogForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            log = form.save(commit=False)
            log.created_by = request.user
            log.save()
            messages.success(request, "Günlük kaydedildi.")
            return redirect("internship:intern_logs")
        _log_form("InternLogForm", request, form)
    return render(request, "internship/log_form.html", {"form": form})


@login_required
def intern_log_list_view(request):
    logs = InternLog.objects.select_related("application").filter(created_by=request.user)
    return render(request, "internship/log_list.html", {"logs": logs})


class PanelLoginView(LoginView):
    template_name = "internship/panel_login.html"


panel_login_view = PanelLoginView.as_view()


@user_passes_test(is_admin)
def dashboard_view(request):
    total_applications = Application.objects.count()
    pending = Application.objects.filter(status=Application.Status.PENDING).count()
    approved = Application.objects.filter(status=Application.Status.APPROVED).count()
    rejected = Application.objects.filter(status=Application.Status.REJECTED).count()
    return render(
        request,
        "internship/dashboard.html",
        {"total_applications": total_applications, "pending": pending, "approved": approved, "rejected": rejected},
    )


@user_passes_test(is_admin)
def application_list_view(request):
    applications = Application.objects.all()
    return render(request, "internship/application_list.html", {"applications": applications})


@login_required
@user_passes_test(is_personnel)
def panel_applications(request):
    personnel, applications = _application_queryset_for_personnel(request.user)
    q = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    supervisor_filter = (request.GET.get("supervisor") or "").strip()

    if q:
        applications = applications.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(tc_no__icontains=q)
            | Q(phone__icontains=q)
            | Q(school__icontains=q)
            | Q(department__icontains=q)
        )
    if status_filter in {"pending", "approved", "rejected"}:
        applications = applications.filter(status=status_filter)
    if supervisor_filter == "assigned":
        applications = applications.filter(supervisor__isnull=False)
    elif supervisor_filter == "unassigned":
        applications = applications.filter(supervisor__isnull=True)

    bulk_form = ApplicationBulkActionForm(request.POST or None)
    if request.method == "POST" and bulk_form.is_valid():
        action = bulk_form.cleaned_data["action"]
        note = (bulk_form.cleaned_data.get("note") or "").strip()
        selected_ids = [int(pk) for pk in request.POST.getlist("selected_ids") if pk.isdigit()]
        queryset = applications.filter(pk__in=selected_ids)
        if not queryset.exists():
            messages.error(request, "İşlem için en az bir başvuru seçmelisiniz.")
        else:
            for app in queryset:
                if action == "approve":
                    _approve_application(app, personnel, request.user)
                else:
                    _reject_application(app, note or "Toplu işlem ile reddedildi.", request.user)
            messages.success(request, f"{queryset.count()} başvuru için toplu işlem uygulandı.")
        return redirect(request.path)

    stats_source = applications
    stats = {
        "total": stats_source.count(),
        "pending": stats_source.filter(status="pending").count(),
        "approved": stats_source.filter(status="approved").count(),
        "rejected": stats_source.filter(status="rejected").count(),
    }
    supervisors = PersonnelProfile.objects.filter(is_active=True).order_by("first_name", "last_name")
    return render(
        request,
        "panel/applications_list.html",
        {
            "applications": applications.prefetch_related("status_history", "documents"),
            "stats": stats,
            "bulk_form": bulk_form,
            "q": q,
            "status_filter": status_filter,
            "supervisor_filter": supervisor_filter,
            "supervisors": supervisors,
        },
    )


def _approve_application(app, personnel, actor):
    if getattr(app, "user_id", None):
        if personnel and not app.supervisor_id:
            app.supervisor = personnel
            app.save(update_fields=["supervisor"])
        _record_application_history(app, actor, "approved", "Başvuru onaylandı.")
        return None, None

    stajyer_group, _ = Group.objects.get_or_create(name="Stajyer")
    username = _unique_username(app.first_name, app.last_name)
    password = _gen_password()
    user = User.objects.create_user(username=username, password=password, email=app.email or "")
    user.is_staff = False
    user.is_superuser = False
    user.save()
    user.groups.add(stajyer_group)

    app.user = user
    app.account_created_at = timezone.now()
    app.credentials_sent = False
    app.must_change_password = True
    if personnel and not app.supervisor_id:
        app.supervisor = personnel
    app.save(update_fields=["user", "account_created_at", "credentials_sent", "must_change_password", "supervisor"])
    _record_application_history(app, actor, "approved", "Başvuru onaylandı ve hesap oluşturuldu.")

    if app.email:
        try:
            sent, error_message = send_intern_credentials_email(app, username, password)
            if sent:
                app.credentials_sent = True
                app.save(update_fields=["credentials_sent"])
        except Exception:
            pass
    return username, password


def _reject_application(app, reason, actor):
    reason = reason or "Başvuru reddedildi."
    _record_application_history(app, actor, "rejected", reason)


@login_required
@user_passes_test(is_personnel)
def panel_application_approve(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    app = get_object_or_404(applications, pk=pk)
    username, password = _approve_application(app, personnel, request.user)
    if username and password:
        messages.success(request, f"Başvuru #{app.id} onaylandı. Kullanıcı: {username} | Şifre: {password}")
    else:
        messages.success(request, f"Başvuru #{app.id} onaylandı.")
    return redirect("internship:panel_applications")


@login_required
@user_passes_test(is_personnel)
def panel_application_reject(request, pk):
    _, applications = _application_queryset_for_personnel(request.user)
    app = get_object_or_404(applications, pk=pk)
    field_reason = request.POST.get(f"reason_{pk}") if request.method == "POST" else ""
    reason = (field_reason or request.POST.get("reason") or request.GET.get("reason") or "Personel tarafından uygun bulunmadı.").strip()
    _reject_application(app, reason, request.user)
    messages.warning(request, f"Başvuru #{app.id} reddedildi.")
    return redirect("internship:panel_applications")


@login_required
@user_passes_test(is_personnel)
def panel_logs_list(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    logs = DailyLog.objects.select_related("application", "application__supervisor").prefetch_related("reviews").order_by(
        "-date", "-created_at"
    )
    if personnel:
        logs = logs.filter(application__supervisor=personnel)
    stats = {
        "total": logs.count(),
        "reviewed": logs.filter(reviews__isnull=False).distinct().count(),
        "pending": logs.filter(reviews__isnull=True).count(),
    }
    return render(request, "panel/logs_list.html", {"logs": logs, "stats": stats})


@login_required
@user_passes_test(is_personnel)
def panel_log_review(request, pk):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    logs = DailyLog.objects.select_related("application", "application__supervisor")
    if personnel:
        logs = logs.filter(application__supervisor=personnel)
    log = get_object_or_404(logs, pk=pk)
    existing_review = log.reviews.order_by("-created_at").first()
    form = ReviewForm(request.POST or None, instance=existing_review)
    if request.method == "POST":
        if form.is_valid():
            review = form.save(commit=False)
            review.log = log
            review.reviewer = request.user
            review.save()
            messages.success(request, "Günlük başarıyla değerlendirildi.")
            return redirect("internship:panel_logs_list")
        _log_form("ReviewForm", request, form)
    return render(request, "panel/log_review.html", {"log": log, "existing_review": existing_review, "form": form})


@login_required
@user_passes_test(is_personnel)
def panel_conversation(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    application = get_object_or_404(applications.filter(supervisor=personnel), pk=pk)

    if request.method == "POST":
        action = request.POST.get("message_action")
        if action == "edit":
            message = get_object_or_404(ConversationMessage, pk=request.POST.get("message_id"), sender=request.user, application=application)
            message.message = (request.POST.get("edited_message") or "").strip()
            message.edited_at = timezone.now()
            message.save(update_fields=["message", "edited_at"])
            messages.success(request, "Mesaj güncellendi.")
            return redirect("internship:panel_conversation", pk=application.pk)
        if action == "delete":
            message = get_object_or_404(ConversationMessage, pk=request.POST.get("message_id"), sender=request.user, application=application)
            message.deleted_at = timezone.now()
            message.save(update_fields=["deleted_at"])
            messages.success(request, "Mesaj silindi.")
            return redirect("internship:panel_conversation", pk=application.pk)
        if _save_conversation_message(request, application):
            return redirect("internship:panel_conversation", pk=application.pk)

    _mark_conversation_read(application, request.user)
    conversations = ConversationMessage.objects.filter(application=application).select_related("sender")
    return render(
        request,
        "internship/conversation.html",
        {
            "application": application,
            "conversation_entries": _build_conversation_entries(conversations, request.user),
            "conversations": conversations,
            "mode": "personnel",
        },
    )


@login_required
@user_passes_test(is_personnel)
@require_GET
def panel_conversation_poll(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    application = get_object_or_404(applications.filter(supervisor=personnel), pk=pk)
    latest = ConversationMessage.objects.filter(application=application, deleted_at__isnull=True).order_by("-created_at").first()
    unread = ConversationMessage.objects.filter(application=application, read_at__isnull=True).exclude(sender=request.user).count()
    return JsonResponse(
        {
            "latest_id": latest.pk if latest else 0,
            "latest_at": latest.created_at.isoformat() if latest else None,
            "unread_count": unread,
        }
    )


@login_required
@user_passes_test(is_personnel)
def panel_task_assign(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    application = get_object_or_404(applications.filter(supervisor=personnel), pk=pk)
    form = PersonnelTaskForm(request.POST or None)
    comment_form = TaskCommentForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("task_action")
        if action == "comment":
            task = get_object_or_404(PersonnelTask, pk=request.POST.get("task_id"), application=application)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.task = task
                comment.author = request.user
                comment.save()
                messages.success(request, "Görev yorumu kaydedildi.")
                return redirect("internship:panel_task_assign", pk=application.pk)
        elif action == "toggle":
            task = get_object_or_404(PersonnelTask, pk=request.POST.get("task_id"), application=application)
            task.is_completed = not task.is_completed
            task.completed_at = timezone.now() if task.is_completed else None
            task.save(update_fields=["is_completed", "completed_at"])
            messages.success(request, "Görev durumu güncellendi.")
            return redirect("internship:panel_task_assign", pk=application.pk)
        elif form.is_valid():
            task = form.save(commit=False)
            task.application = application
            task.personnel = personnel
            task.save()
            messages.success(request, "Stajyere özel görev kaydedildi.")
            return redirect("internship:panel_task_assign", pk=application.pk)
        else:
            _log_form("PersonnelTaskForm", request, form)

    tasks = PersonnelTask.objects.filter(application=application).prefetch_related("comments__author").order_by(
        "-task_date", "-created_at"
    )
    return render(
        request,
        "panel/task_assign.html",
        {
            "application": application,
            "form": form,
            "tasks": tasks,
            "comment_form": TaskCommentForm(),
        },
    )


@login_required
@user_passes_test(is_personnel)
def panel_document_review(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    application = get_object_or_404(applications.filter(supervisor=personnel), pk=pk)
    documents = application.documents.all().order_by("category", "-uploaded_at")
    if request.method == "POST":
        document = get_object_or_404(InternDocument, pk=request.POST.get("document_id"), application=application)
        form = DocumentReviewForm(request.POST, instance=document)
        if form.is_valid():
            reviewed = form.save(commit=False)
            reviewed.reviewed_at = timezone.now()
            reviewed.save()
            messages.success(request, "Belge değerlendirmesi kaydedildi.")
            return redirect("internship:panel_document_review", pk=application.pk)
        _log_form("DocumentReviewForm", request, form)
    docs_with_forms = [{"document": doc, "form": DocumentReviewForm(instance=doc)} for doc in documents]
    return render(
        request,
        "panel/document_review.html",
        {
            "application": application,
            "docs_with_forms": docs_with_forms,
        },
    )


def intern_log_create(request):
    if not _require_intern(request):
        return redirect("website:home")
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Log.objects.create(intern=request.user, content=content)
            messages.success(request, "Günlük kaydı oluşturuldu.")
            return redirect("internship:intern_logs")
    logs = Log.objects.filter(intern=request.user).order_by("-date")
    return render(request, "panel/intern_logs.html", {"logs": logs})


def intern_apply(request):
    form = InternApplicationForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            application = form.save()
            ApplicationStatusHistory.objects.create(
                application=application,
                actor=request.user if request.user.is_authenticated else None,
                from_status="",
                to_status="pending",
                note="Başvuru oluşturuldu.",
            )
            messages.success(request, "Başvurunuz başarıyla alınmıştır.")
            return render(request, "internship/apply_success.html", {"application": application})
        _log_form("InternApplicationForm", request, form)
    return render(request, "internship/apply.html", {"form": form})


def intern_application_query(request):
    result = None
    form = ApplicationQueryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tc_no = form.cleaned_data.get("tc_no") or form.cleaned_data.get("tc_kimlik")
        phone = form.cleaned_data.get("phone")
        try:
            result = InternApplication.objects.prefetch_related("status_history").get(tc_no=tc_no, phone=phone)
        except InternApplication.DoesNotExist:
            messages.error(request, "Bu bilgilerle kayıtlı bir başvuru bulunamadı.")
    return render(request, "internship/query.html", {"form": form, "result": result})


def intern_daily_log(request):
    if not request.user.is_authenticated:
        messages.info(request, "Günlük girişi için önce stajyer hesabınızla giriş yapmalısınız.")
        return redirect(f"{reverse('website:intern_login')}?next={reverse('internship:intern_daily_log')}")
    if not _require_intern(request):
        return redirect("website:home")

    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)
    if not application:
        messages.error(request, "Hesabınıza bağlı bir staj başvurusu bulunamadı.")
        return redirect("internship:intern_dashboard")

    task_choices = _build_daily_task_choices(application)
    form = DailyLogForm(request.POST or None, task_choices=task_choices)
    if request.method == "POST":
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
            _log_form("DailyLogForm", request, form)

    last_log = DailyLog.objects.filter(application=application).order_by("-date", "-created_at").first()
    todays_tasks = PersonnelTask.objects.filter(application=application, is_active=True).order_by("task_date", "-created_at")[:4]
    return render(
        request,
        "internship/daily_log.html",
        {
            "form": form,
            "application": application,
            "last_log": last_log,
            "todays_tasks": todays_tasks,
            "internship_tasks": INTERNSHIP_TASKS,
        },
    )


def intern_portal(request):
    return render(request, "internship/login_choice.html")


@login_required
def intern_dashboard_view(request):
    if not _require_intern(request):
        return redirect("website:home")
    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect

    application = _get_intern_application_for_user(request.user)
    last_logs = DailyLog.objects.none()
    logs_count = 0
    reviewed_logs_count = 0
    active_tasks = PersonnelTask.objects.none()
    unread_messages_count = 0
    pending_documents_count = 0

    if application:
        last_logs = DailyLog.objects.filter(application=application).order_by("-date", "-created_at")[:5]
        logs_count = DailyLog.objects.filter(application=application).count()
        reviewed_logs_count = DailyLog.objects.filter(application=application, reviews__isnull=False).distinct().count()
        active_tasks = PersonnelTask.objects.filter(application=application, is_active=True).order_by("task_date", "-created_at")[:4]
        unread_messages_count = ConversationMessage.objects.filter(
            application=application, read_at__isnull=True, deleted_at__isnull=True
        ).exclude(sender=request.user).count()
        pending_documents_count = application.documents.filter(status__in=["pending", "missing"]).count()

    announcements = Announcement.objects.filter(is_active=True).order_by("-created_at")[:5]
    return render(
        request,
        "internship/intern_dashboard.html",
        {
            "application": application,
            "last_logs": last_logs,
            "logs_count": logs_count,
            "reviewed_logs_count": reviewed_logs_count,
            "unread_messages_count": unread_messages_count,
            "active_tasks": active_tasks,
            "announcements": announcements,
            "pending_documents_count": pending_documents_count,
        },
    )


@login_required
def intern_application_detail_view(request):
    if not _require_intern(request):
        return redirect("website:home")
    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect
    application = _get_intern_application_for_user(request.user)
    return render(request, "internship/intern_application_detail.html", {"application": application})


@login_required
def intern_daily_logs_view(request):
    if not _require_intern(request):
        return redirect("website:home")
    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect
    application = _get_intern_application_for_user(request.user)
    logs = DailyLog.objects.none()
    active_tasks = PersonnelTask.objects.none()
    if application:
        logs = DailyLog.objects.filter(application=application).prefetch_related("reviews__reviewer").order_by("-date", "-created_at")
        active_tasks = PersonnelTask.objects.filter(application=application, is_active=True).order_by("task_date", "-created_at")[:4]
    return render(
        request,
        "internship/intern_daily_logs.html",
        {"application": application, "logs": logs, "active_tasks": active_tasks, "internship_tasks": INTERNSHIP_TASKS},
    )


@login_required
def intern_conversation_view(request):
    if not _require_intern(request):
        return redirect("website:home")
    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect
    application = _get_intern_application_for_user(request.user)
    if not application or not application.supervisor_id:
        messages.warning(request, "Mesajlaşma için önce sorumlu personel eşleşmesi yapılmalıdır.")
        return redirect("internship:intern_dashboard")

    if request.method == "POST":
        action = request.POST.get("message_action")
        if action == "edit":
            message = get_object_or_404(ConversationMessage, pk=request.POST.get("message_id"), sender=request.user, application=application)
            message.message = (request.POST.get("edited_message") or "").strip()
            message.edited_at = timezone.now()
            message.save(update_fields=["message", "edited_at"])
            messages.success(request, "Mesaj güncellendi.")
            return redirect("internship:intern_conversation")
        if action == "delete":
            message = get_object_or_404(ConversationMessage, pk=request.POST.get("message_id"), sender=request.user, application=application)
            message.deleted_at = timezone.now()
            message.save(update_fields=["deleted_at"])
            messages.success(request, "Mesaj silindi.")
            return redirect("internship:intern_conversation")
        if _save_conversation_message(request, application):
            return redirect("internship:intern_conversation")

    _mark_conversation_read(application, request.user)
    conversations = ConversationMessage.objects.filter(application=application).select_related("sender")
    return render(
        request,
        "internship/conversation.html",
        {
            "application": application,
            "conversation_entries": _build_conversation_entries(conversations, request.user),
            "conversations": conversations,
            "mode": "intern",
        },
    )


@login_required
@require_GET
def intern_conversation_poll(request):
    if not _require_intern(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    application = _get_intern_application_for_user(request.user)
    if not application or not application.supervisor_id:
        return JsonResponse({"error": "no-match"}, status=404)
    latest = ConversationMessage.objects.filter(application=application, deleted_at__isnull=True).order_by("-created_at").first()
    unread = ConversationMessage.objects.filter(
        application=application, read_at__isnull=True, deleted_at__isnull=True
    ).exclude(sender=request.user).count()
    return JsonResponse(
        {
            "latest_id": latest.pk if latest else 0,
            "latest_at": latest.created_at.isoformat() if latest else None,
            "unread_count": unread,
        }
    )


@login_required
@require_POST
def task_toggle_complete(request, pk):
    task = get_object_or_404(PersonnelTask, pk=pk, application__user=request.user)
    task.is_completed = not task.is_completed
    task.completed_at = timezone.now() if task.is_completed else None
    task.save(update_fields=["is_completed", "completed_at"])
    messages.success(request, "Görev durumu güncellendi.")
    return redirect("internship:intern_dashboard")


@login_required
def intern_documents_view(request):
    if not _require_intern(request):
        return redirect("website:home")
    password_redirect = _redirect_if_password_change_required(request)
    if password_redirect:
        return password_redirect
    application = _get_intern_application_for_user(request.user)
    if not application:
        messages.error(request, "Hesabınıza bağlı başvuru bulunamadı.")
        return redirect("internship:intern_dashboard")

    form = InternDocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            document = form.save(commit=False)
            document.application = application
            document.status = InternDocument.Status.PENDING
            document.reupload_requested = False
            document.personnel_note = ""
            document.reviewed_at = None
            document.save()
            messages.success(request, "Belge başarıyla yüklendi.")
            return redirect("internship:intern_documents")
        _log_form("InternDocumentUploadForm", request, form)

    documents = application.documents.all().order_by("category", "-uploaded_at")
    grouped_documents = []
    for requirement in DOCUMENT_REQUIREMENTS:
        docs = [doc for doc in documents if doc.category == requirement["category"]]
        latest = docs[0] if docs else None
        grouped_documents.append(
            {
                **requirement,
                "latest": latest,
                "history": docs,
                "rule": DOCUMENT_RULES[requirement["category"]],
            }
        )

    return render(
        request,
        "internship/intern_documents.html",
        {"application": application, "form": form, "grouped_documents": grouped_documents},
    )


@login_required
@user_passes_test(is_personnel)
def panel_application_approve(request, pk):
    personnel, applications = _application_queryset_for_personnel(request.user)
    app = get_object_or_404(applications, pk=pk)
    username, password = _approve_application(app, personnel, request.user)
    if username and password:
        if app.email:
            messages.success(
                request,
                f"Başvuru #{app.id} onaylandı. Kullanıcı adı {username} için giriş bilgileri e-posta adresine gönderildi.",
            )
        else:
            messages.warning(
                request,
                f"Başvuru #{app.id} onaylandı. Kullanıcı adı {username} oluşturuldu ancak e-posta adresi olmadığı için geçici şifre gönderilemedi.",
            )
    else:
        messages.success(request, f"Başvuru #{app.id} onaylandı.")
    return redirect("internship:panel_applications")
