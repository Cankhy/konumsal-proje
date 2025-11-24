from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count


from .forms import (
    InternApplicationForm,
    ApplicationForm,
    ApplicationQueryForm,
    InternLogForm,
    DailyLogForm,
    
)
from .models import Application, InternLog, InternApplication

def application_create_view(request):
    """
    3.1 Stajyer Başvuru Ekranı – HTML form
    """
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Başvurunuz başarıyla alındı. Teşekkür ederiz.")
            return redirect("internship:application_create")
    else:
        form = ApplicationForm()

    return render(request, "internship/application_form.html", {"form": form})


def application_query_view(request):
    """
    3.2 Talep Sorgulama – TC + Telefon
    """
    application = None
    form = ApplicationQueryForm(request.GET or None)
    if form.is_valid():
        tc = form.cleaned_data["tc_kimlik"]
        phone = form.cleaned_data["phone"]
        try:
            application = Application.objects.get(tc_kimlik=tc, phone=phone)
        except Application.DoesNotExist:
            messages.error(request, "Bu bilgilere ait başvuru bulunamadı.")

    context = {"form": form, "application": application}
    return render(request, "internship/application_query.html", context)


@login_required
def intern_log_create_view(request):
    """
    3.3 – Stajyer günlük girişi (HTML)
    """
    if request.method == "POST":
        form = InternLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.created_by = request.user
            log.save()
            messages.success(request, "Günlük kaydedildi.")
            return redirect("internship:log_list")
    else:
        form = InternLogForm()

    return render(request, "internship/log_form.html", {"form": form})


@login_required
def intern_log_list_view(request):
    logs = InternLog.objects.select_related("application").filter(created_by=request.user)
    return render(request, "internship/log_list.html", {"logs": logs})


# ==== Yönetim Paneli ====


class PanelLoginView(LoginView):
    template_name = "internship/panel_login.html"

panel_login_view = PanelLoginView.as_view()


def is_admin(user):
    return getattr(user, "role", None) == "ADMIN" or user.is_superuser


@user_passes_test(is_admin)
def dashboard_view(request):
    """
    4.2 Dashboard – basic istatistikler
    """
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
    """
    4.4 Stajyer Yönetimi – başvuru listesi
    """
    applications = Application.objects.all()
    return render(request, "internship/application_list.html", {"applications": applications})

# internship/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Application, Log

# Personel mi kontrolü (admin de personel sayılıyor)
def is_personnel(user):
    return user.is_staff or user.groups.filter(name="Personel").exists()


@login_required
@user_passes_test(is_personnel)
def panel_applications(request):
    applications = Application.objects.order_by("-created_at")
    return render(request, "panel/applications_list.html", {
        "applications": applications
    })


@login_required
@user_passes_test(is_personnel)
def panel_application_approve(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.status = "approved"
    app.save()
    return redirect("panel_applications")


@login_required
@user_passes_test(is_personnel)
def panel_application_reject(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.status = "rejected"
    app.save()
    return redirect("panel_applications")

from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def intern_log_create(request):
    # sadece stajyer grubundaysa izin verelim (yoksa bu satırı kaldır)
    if not request.user.groups.filter(name="Stajyer").exists():
        return redirect("home")  # ya da 403

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Log.objects.create(intern=request.user, content=content)
            return redirect("intern_logs")

    logs = Log.objects.filter(intern=request.user).order_by("-date")
    return render(request, "panel/intern_logs.html", {"logs": logs})

@login_required
@user_passes_test(is_personnel)
def panel_logs_list(request):
    logs = Log.objects.select_related("intern").order_by("-date")
    return render(request, "panel/logs_list.html", {"logs": logs})


@login_required
@user_passes_test(is_personnel)
def panel_log_review(request, pk):
    log = get_object_or_404(Log, pk=pk)

    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        if 0 < score <= 10:
            log.score = score
            log.reviewer = request.user
            log.save()
        return redirect("panel_logs_list")

    return render(request, "panel/log_review.html", {"log": log})

def intern_apply(request):
    """
    3.1 Stajyer Başvuru Ekranı
    """
    if request.method == "POST":
        form = InternApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, "Başvurunuz başarıyla alınmıştır.")
            return render(
                request,
                "internship/apply_success.html",
                {"application": application},
            )
    else:
        form = InternApplicationForm()

    return render(request, "internship/apply.html", {"form": form})


def intern_application_query(request):
    """
    3.2 Talep Sorgulama – TC + Telefon ile başvuru durumunu göster
    """
    result = None

    if request.method == "POST":
        form = ApplicationQueryForm(request.POST)
        if form.is_valid():
            tc_no = form.cleaned_data["tc_no"]
            phone = form.cleaned_data["phone"]

            try:
                result = InternApplication.objects.get(
                    tc_no=tc_no,
                    phone=phone,
                )
            except InternApplication.DoesNotExist:
                messages.error(
                    request,
                    "Bu bilgilerle kayıtlı bir başvuru bulunamadı.",
                )
    else:
        form = ApplicationQueryForm()

    return render(
        request,
        "internship/query.html",
        {"form": form, "result": result},
    )


def intern_daily_log(request):
    """
    3.3 Stajyer Günlük Girişi – TC + Telefon ile başvuruyu bul, günlük kaydet
    """
    application = None

    if request.method == "POST":
        form = DailyLogForm(request.POST)
        if form.is_valid():
            tc_no = form.cleaned_data["tc_no"]
            phone = form.cleaned_data["phone"]

            application = get_object_or_404(
                InternApplication,
                tc_no=tc_no,
                phone=phone,
            )

            log = form.save(commit=False)
            log.application = application
            log.save()
            messages.success(request, "Günlük kaydınız oluşturuldu.")
    else:
        form = DailyLogForm()

    return render(
        request,
        "internship/daily_log.html",
        {"form": form, "application": application},
    )

