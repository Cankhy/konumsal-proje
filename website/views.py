from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
import logging

from .models import AboutPage, Service, Project, ContactInfo
from internship.models import ConversationMessage, InternApplication, DailyLog, Announcement, PersonnelProfile

logger = logging.getLogger(__name__)


def home(request):
    featured_projects = Project.objects.filter(is_active=True, is_featured=True)[:3]
    services = Service.objects.filter(is_active=True).order_by("order")[:6]
    return render(
        request,
        "website/home.html",
        {
            "featured_projects": featured_projects,
            "services": services,
        },
    )


def hakkimizda(request):
    about = AboutPage.objects.first()
    return render(request, "website/hakkimizda.html", {"about": about})


def hizmetler(request):
    services = Service.objects.filter(is_active=True).order_by("order", "title")
    return render(request, "website/hizmetler.html", {"services": services})


def projeler(request):
    projects = Project.objects.filter(is_active=True).order_by("order", "title")
    return render(request, "website/projeler.html", {"projects": projects})


def iletisim(request):
    contact = ContactInfo.objects.first()
    return render(request, "website/iletisim.html", {"contact": contact})


def proje_orman(request):
    return render(request, "website/proje_orman.html")


def proje_meop(request):
    return render(request, "website/proje_meop.html")


def proje_hey(request):
    return render(request, "website/proje_hey.html")


def hizmet_cbs(request):
    return render(request, "website/hizmet_cbs.html")


def hizmet_erp(request):
    return render(request, "website/hizmet_erp.html")


def hizmet_siber(request):
    return render(request, "website/hizmet_siber.html")


def hizmet_universite(request):
    return render(request, "website/hizmet_universite.html")


def hizmet_ik(request):
    return render(request, "website/hizmet_ik.html")


def hizmet_veri(request):
    return render(request, "website/hizmet_veri.html")


def hizmet_mobil(request):
    return render(request, "website/hizmet_mobil.html")


def hizmet_edys(request):
    return render(request, "website/hizmet_edys.html")


def hizmet_gorev(request):
    return render(request, "website/hizmet_gorev.html")


def hizmet_aktl(request):
    return render(request, "website/hizmet_aktl.html")


def hizmet_mapgate(request):
    return render(request, "website/hizmet_mapgate.html")


@ensure_csrf_cookie
def login_select(request):
    if request.method == "POST":
        role = request.POST.get("role", "intern")
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request,
                "auth/login_select.html",
                {"error": "Kullanıcı adı veya şifre hatalı.", "selected_role": role},
            )

        if user.is_superuser:
            return render(
                request,
                "auth/login_select.html",
                {"error": "Yönetici hesabı bu ekrandan giriş yapamaz.", "selected_role": role},
            )

        if role == "staff":
            if not is_personnel(user):
                return render(
                    request,
                    "auth/login_select.html",
                    {"error": "Bu hesap personel paneli için yetkili değil.", "selected_role": role},
                )
            login(request, user)
            return redirect("website:personnel_home")

        if is_personnel(user):
            return render(
                request,
                "auth/login_select.html",
                {"error": "Bu hesap stajyer paneli için kullanılamaz.", "selected_role": role},
            )

        login(request, user)
        return redirect("internship:intern_dashboard")

    logout(request)
    return render(request, "auth/login_select.html", {"selected_role": "intern"})


def admin_secret_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_superuser:
            return render(
                request,
                "auth/admin_login.html",
                {"error": "Yönetici bilgileri hatalı."},
            )

        login(request, user)
        return redirect("admin:index")

    logout(request)
    return render(request, "auth/admin_login.html")


def is_personnel(user):
    return user.is_authenticated and user.groups.filter(name="Personel").exists()


@login_required
@user_passes_test(is_personnel)
def personnel_home(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    applications = InternApplication.objects.select_related("supervisor", "user").filter(status="approved")
    if personnel:
        applications = applications.filter(Q(supervisor=personnel) | Q(supervisor__isnull=True))

    assigned_applications = applications.filter(supervisor=personnel) if personnel else applications
    latest_logs = (
        DailyLog.objects.select_related("application", "application__supervisor")
        .prefetch_related("reviews")
        .filter(application__in=assigned_applications)
        .order_by("-date", "-created_at")[:6]
    )

    stats = {
        "total_applications": applications.count(),
        "pending_applications": InternApplication.objects.filter(status="pending").count(),
        "approved_applications": assigned_applications.count(),
        "daily_logs": DailyLog.objects.filter(application__in=assigned_applications).count(),
        "review_pending": DailyLog.objects.filter(application__in=assigned_applications, reviews__isnull=True).count(),
        "unread_messages": ConversationMessage.objects.filter(
            application__in=assigned_applications,
            read_at__isnull=True,
        ).exclude(sender=request.user).count(),
    }
    recent_announcements = Announcement.objects.filter(is_active=True).order_by("-created_at")[:4]
    return render(
        request,
        "auth/personnel_home.html",
        {
            "stats": stats,
            "personnel": personnel,
            "assigned_applications": assigned_applications.annotate(
                log_count=Count("logs"),
                unread_count=Count(
                    "messages",
                    filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=request.user),
                ),
            )[:5],
            "unassigned_applications": applications.filter(supervisor__isnull=True)[:4],
            "latest_logs": latest_logs,
            "recent_announcements": recent_announcements,
        },
    )


class InternLoginView(LoginView):
    template_name = "auth/intern_login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # next varsa önce onu kullanır, yoksa stajyer paneline gider
        return self.get_redirect_url() or reverse_lazy("internship:intern_dashboard")


intern_login_view = InternLoginView.as_view()


class InternPasswordChangeView(PasswordChangeView):
    template_name = "auth/intern_password_change.html"
    success_url = reverse_lazy("website:intern_password_change_done")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                }
            )
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        application = InternApplication.objects.filter(user=self.request.user).first()
        if application and application.must_change_password:
            application.must_change_password = False
            application.save(update_fields=["must_change_password"])
        messages.success(self.request, "Şifreniz başarıyla güncellendi.")
        return response


@login_required
def intern_password_change_done(request):
    return render(request, "auth/intern_password_change_done.html")


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    return render(request, "website/project_detail.html", {"project": project})


def custom_404(request, exception):
    logger.warning("404 page hit", extra={"path": request.path})
    return render(request, "404.html", status=404)


def custom_500(request):
    logger.exception("500 page rendered")
    return render(request, "500.html", status=500)
