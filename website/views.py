from decimal import Decimal

from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
import logging

from .models import AboutPage, ContactInfo, HomeServiceCard, HomeSlide, ManagedPage, Project, Service
from internship.forms import PersonnelLeaveRequestForm, log_form_errors
from internship.models import (
    Announcement,
    ConversationMessage,
    DailyLog,
    InternApplication,
    PersonnelLeaveRequest,
    PersonnelProfile,
)

logger = logging.getLogger(__name__)


def render_managed_or_template(request, template_name, context=None):
    context = context or {}
    page = (
        ManagedPage.objects.prefetch_related("sections")
        .filter(path=request.path, is_active=True)
        .first()
    )
    if page:
        context["page"] = page
        context["sections"] = page.sections.filter(is_active=True)
        return render(request, "website/managed_page.html", context)
    return render(request, template_name, context)


def home(request):
    featured_projects = Project.objects.filter(is_active=True, is_featured=True)[:3]
    services = Service.objects.filter(is_active=True).order_by("order")[:6]
    home_slides = HomeSlide.objects.filter(is_active=True).order_by("order", "title")
    home_service_cards = HomeServiceCard.objects.filter(is_active=True).order_by("order", "title")
    return render(
        request,
        "website/home.html",
        {
            "featured_projects": featured_projects,
            "services": services,
            "home_slides": home_slides,
            "home_service_cards": home_service_cards,
        },
    )


def hakkimizda(request):
    about = AboutPage.objects.first()
    return render_managed_or_template(request, "website/hakkimizda.html", {"about": about})


def hizmetler(request):
    services = Service.objects.filter(is_active=True).order_by("order", "title")
    return render_managed_or_template(request, "website/hizmetler.html", {"services": services})


def projeler(request):
    projects = Project.objects.filter(is_active=True).order_by("order", "title")
    return render_managed_or_template(request, "website/projeler.html", {"projects": projects})


def iletisim(request):
    contact = ContactInfo.objects.first()
    return render_managed_or_template(request, "website/iletisim.html", {"contact": contact})


def proje_orman(request):
    return render_managed_or_template(request, "website/proje_orman.html")


def proje_meop(request):
    return render_managed_or_template(request, "website/proje_meop.html")


def proje_hey(request):
    return render_managed_or_template(request, "website/proje_hey.html")


def hizmet_cbs(request):
    return render_managed_or_template(request, "website/hizmet_cbs.html")


def hizmet_erp(request):
    return render_managed_or_template(request, "website/hizmet_erp.html")


def hizmet_siber(request):
    return render_managed_or_template(request, "website/hizmet_siber.html")


def hizmet_universite(request):
    return render_managed_or_template(request, "website/hizmet_universite.html")


def hizmet_ik(request):
    return render_managed_or_template(request, "website/hizmet_ik.html")


def hizmet_veri(request):
    return render_managed_or_template(request, "website/hizmet_veri.html")


def hizmet_mobil(request):
    return render_managed_or_template(request, "website/hizmet_mobil.html")


def hizmet_edys(request):
    return render_managed_or_template(request, "website/hizmet_edys.html")


def hizmet_gorev(request):
    return render_managed_or_template(request, "website/hizmet_gorev.html")


def hizmet_aktl(request):
    return render_managed_or_template(request, "website/hizmet_aktl.html")


def hizmet_mapgate(request):
    return render_managed_or_template(request, "website/hizmet_mapgate.html")


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


def _is_stajyer(user):
    return user.is_authenticated and user.groups.filter(name="Stajyer").exists()


def _validate_avatar_file(uploaded_file):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if uploaded_file.content_type not in allowed_types:
        raise ValidationError("Profil fotoğrafı JPG, PNG veya WEBP olmalıdır.")
    if uploaded_file.size > 3 * 1024 * 1024:
        raise ValidationError("Profil fotoğrafı en fazla 3 MB olabilir.")


def _personnel_leave_summary(personnel):
    entitlement = Decimal(str(getattr(personnel, "leave_entitlement_days", 56) or 56))
    approved_annual = (
        personnel.leave_requests.filter(
            status=PersonnelLeaveRequest.Status.APPROVED,
            leave_type=PersonnelLeaveRequest.LeaveType.ANNUAL,
        )
        .values_list("duration_value", flat=True)
    )
    used = sum((Decimal(str(value)) for value in approved_annual), Decimal("0"))
    remaining = entitlement - used
    if remaining < 0:
        remaining = Decimal("0")
    pending = personnel.leave_requests.filter(status=PersonnelLeaveRequest.Status.PENDING).count()
    return {
        "entitlement": entitlement,
        "used": used,
        "remaining": remaining,
        "pending": pending,
    }


def _leave_type_impacts_allowance(leave_type):
    return leave_type == PersonnelLeaveRequest.LeaveType.ANNUAL


@login_required
@require_POST
def profile_avatar_upload(request):
    avatar = request.FILES.get("profile_avatar")
    if not avatar:
        messages.error(request, "Profil fotoğrafı seçmelisiniz.")
        return redirect(request.POST.get("next") or "website:home")

    try:
        _validate_avatar_file(avatar)
    except ValidationError as exc:
        messages.error(request, exc.message)
        return redirect(request.POST.get("next") or "website:home")

    if is_personnel(request.user):
        profile = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
        if not profile:
            messages.error(request, "Aktif personel profili bulunamadı.")
            return redirect("website:personnel_home")
        profile.profile_avatar = avatar
        profile.save(update_fields=["profile_avatar"])
    elif _is_stajyer(request.user):
        application = InternApplication.objects.filter(user=request.user).first()
        if not application:
            messages.error(request, "Aktif stajyer başvurusu bulunamadı.")
            return redirect("internship:intern_dashboard")
        application.profile_avatar = avatar
        application.save(update_fields=["profile_avatar"])
    else:
        messages.error(request, "Profil fotoğrafı yalnızca stajyer ve personel hesapları için yüklenebilir.")
        return redirect(request.POST.get("next") or "website:home")

    messages.success(request, "Profil fotoğrafı güncellendi.")
    return redirect(request.POST.get("next") or "website:home")


@login_required
@user_passes_test(is_personnel)
def personnel_home(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    leave_summary = _personnel_leave_summary(personnel) if personnel else {"pending": 0}
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
        "pending_leave_requests": leave_summary["pending"],
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
            "leave_summary": leave_summary,
        },
    )


@login_required
@user_passes_test(is_personnel)
def personnel_leave_requests(request):
    personnel = PersonnelProfile.objects.filter(user=request.user, is_active=True).first()
    if not personnel:
        messages.error(request, "Aktif personel profili bulunamadi.")
        return redirect("website:personnel_home")

    edit_request = None
    edit_pk = request.GET.get("edit")
    if edit_pk and edit_pk.isdigit():
        edit_request = get_object_or_404(
            PersonnelLeaveRequest,
            pk=int(edit_pk),
            personnel=personnel,
            status=PersonnelLeaveRequest.Status.PENDING,
        )

    if request.method == "POST":
        action = request.POST.get("leave_action", "save")

        if action == "delete":
            leave_request = get_object_or_404(
                PersonnelLeaveRequest,
                pk=request.POST.get("leave_id"),
                personnel=personnel,
                status=PersonnelLeaveRequest.Status.PENDING,
            )
            leave_request.delete()
            messages.success(request, "Izin talebi silindi.")
            return redirect("website:personnel_leave_requests")

        instance = None
        leave_id = request.POST.get("leave_id")
        if leave_id and leave_id.isdigit():
            instance = get_object_or_404(
                PersonnelLeaveRequest,
                pk=int(leave_id),
                personnel=personnel,
                status=PersonnelLeaveRequest.Status.PENDING,
            )
            edit_request = instance

        form = PersonnelLeaveRequestForm(request.POST, instance=instance)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.personnel = personnel
            leave_request.full_name = f"{personnel.first_name} {personnel.last_name}".strip() or request.user.get_username()
            leave_request.identity_number = personnel.identity_number or ""
            leave_request.job_title = personnel.title or ""
            leave_request.duration_unit = form.cleaned_data["duration_unit"]
            if leave_request.status not in {
                PersonnelLeaveRequest.Status.APPROVED,
                PersonnelLeaveRequest.Status.REJECTED,
            }:
                leave_request.status = PersonnelLeaveRequest.Status.PENDING
            leave_request.save()
            messages.success(
                request,
                "Izin talebi guncellendi." if instance else "Izin talebi kaydedildi.",
            )
            return redirect("website:personnel_leave_requests")

        log_form_errors(
            "PersonnelLeaveRequestForm",
            request.path,
            {key: value for key, value in request.POST.items()},
            form.errors.get_json_data(),
        )
    else:
        initial = {
            "start_date": None,
            "end_date": None,
            "return_date": None,
        }
        form = PersonnelLeaveRequestForm(instance=edit_request, initial=initial if not edit_request else None)

    leave_requests_qs = PersonnelLeaveRequest.objects.filter(personnel=personnel).order_by("-start_date", "-created_at")
    rows = []
    used_annual = Decimal("0")
    entitlement = Decimal(str(personnel.leave_entitlement_days or 56))
    for leave_request in leave_requests_qs.order_by("start_date", "created_at"):
        row_used = used_annual
        if _leave_type_impacts_allowance(leave_request.leave_type) and leave_request.status == PersonnelLeaveRequest.Status.APPROVED:
            row_used += Decimal(str(leave_request.duration_value))
            used_annual = row_used
        row_remaining = entitlement - row_used
        rows.append(
            {
                "request": leave_request,
                "used": row_used,
                "remaining": row_remaining if row_remaining > 0 else Decimal("0"),
                "entitlement": entitlement,
            }
        )
    rows.reverse()

    paginator = Paginator(rows, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    leave_summary = _personnel_leave_summary(personnel)

    return render(
        request,
        "auth/personnel_leave.html",
        {
            "personnel": personnel,
            "form": form,
            "edit_request": edit_request,
            "page_obj": page_obj,
            "leave_summary": leave_summary,
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


LEGAL_PAGES = {
    "kalite-politikasi": {
        "title": "Kalite Politikamız",
        "kicker": "KURUMSAL",
        "summary": "Kaliteli, sürdürülebilir ve güvenilir teslim yaklaşımımızı özetler.",
        "sections": [
            "Müşteri ihtiyaçlarını doğru anlayan, ölçülebilir çıktılar üreten ve sürdürülebilir destek sağlayan bir hizmet anlayışıyla çalışırız.",
            "Yazılım, coğrafi bilgi sistemleri ve kurumsal çözümlerde dokümantasyon, test ve operasyon disiplinini proje yaşam döngüsünün parçası kabul ederiz.",
            "Sürekli iyileştirme, ekip içi bilgi paylaşımı ve güvenli teslim süreçleri kalite yaklaşımımızın temelidir.",
        ],
    },
    "gizlilik-sozlesmesi": {
        "title": "Gizlilik Sözleşmesi",
        "kicker": "KURUMSAL",
        "summary": "Siteyi kullanan ziyaretçiler ve başvuru sahipleri için temel gizlilik çerçevesi.",
        "sections": [
            "Tarafımıza iletilen kişisel veriler yalnızca hizmet sunumu, başvuru değerlendirmesi, iletişim ve yasal yükümlülüklerin yerine getirilmesi amacıyla işlenir.",
            "Veriler yetkisiz erişime karşı teknik ve idari tedbirlerle korunur; ihtiyaç dışı üçüncü taraflarla paylaşılmaz.",
            "Mevzuatın gerektirdiği saklama süreleri dolduğunda veriler silinir, anonimleştirilir veya güvenli şekilde arşivden kaldırılır.",
        ],
    },
    "kullanim-kosullari": {
        "title": "Kullanım Koşulları",
        "kicker": "KURUMSAL",
        "summary": "Web sitesi ve başvuru kanallarının kullanımına ilişkin temel kurallar.",
        "sections": [
            "Ziyaretçiler bu siteyi hukuka uygun amaçlarla kullanmayı kabul eder.",
            "Başvuru, giriş ve mesajlaşma alanlarında paylaşılan bilgilerin doğru ve güncel tutulması kullanıcı sorumluluğundadır.",
            "Sistemin güvenliğini zedeleyebilecek otomasyon, kötüye kullanım veya yetkisiz erişim girişimleri engellenir ve kayıt altına alınabilir.",
        ],
    },
    "cerez-politikasi": {
        "title": "Kişisel Veriler ve Çerez Politikası",
        "kicker": "KVKK",
        "summary": "Çerez, oturum ve temel kişisel veri işleme süreçlerimizin kısa özeti.",
        "sections": [
            "Bu sitede oturumun korunması, güvenli giriş ve temel kullanıcı deneyimi için gerekli çerezler kullanılabilir.",
            "Başvuru ve panel alanlarında girilen bilgiler yalnızca ilgili süreçlerin yürütülmesi amacıyla işlenir.",
            "Tarayıcı ayarlarınız üzerinden çerez tercihlerini yönetebilirsiniz; ancak bazı zorunlu çerezlerin kapatılması giriş ve oturum akışını etkileyebilir.",
        ],
    },
    "kvkk-bilgilendirme": {
        "title": "KVKK Bilgilendirme Metni",
        "kicker": "KVKK",
        "summary": "6698 sayılı Kanun kapsamında veri işleme amaçlarımız ve haklarınız.",
        "sections": [
            "Kimlik, iletişim, eğitim ve başvuru verileri; başvuru değerlendirmesi, staj süreci yönetimi, iletişim ve yasal yükümlülüklerin yerine getirilmesi amacıyla işlenebilir.",
            "Veri sahipleri, mevzuat kapsamındaki erişim, düzeltme, silme ve itiraz haklarını ilgili iletişim kanallarımız üzerinden kullanabilir.",
            "Başvurular ve kullanıcı hesaplarıyla ilişkili kayıtlar yalnızca yetkili ekipler tarafından erişilebilir şekilde korunur.",
        ],
    },
}


LEGAL_PAGES = {
    "kalite-politikasi": {
        "title": "Kalite Politikamız",
        "kicker": "KURUMSAL",
        "summary": "Kalite, bilgi güvenliği ve müşteri memnuniyeti odaklı yönetim yaklaşımımızı ortaya koyar.",
        "blocks": [
            {
                "heading": "Genel Çerçeve",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; ISO/IEC 27001:2013 Bilgi Güvenliği Yönetim Sistemi (BGYS) ve ISO/IEC 9001:2015 Kalite Yönetim Sistemi (KYS) standartları doğrultusunda kurulan sistemlerin ana temasını kalite, güvenlik ve sürdürülebilirlik oluşturmaktadır.",
                ],
                "items": [
                    "Müşteri memnuniyetinin artması",
                    "Pazar payının artması",
                    "Kârın artması",
                    "Çalışan memnuniyetinin artması",
                    "Maliyetlerin azalması",
                    "Yüksek rekabet gücü",
                ],
            },
            {
                "heading": "Temel Yaklaşımımız",
                "paragraphs": [
                    "Kalite ve risk yönetimini güvence altına almak, kalite yönetimi süreç performansını ölçmek ve bilgi güvenliği ile müşteri memnuniyetine ilişkin konularda üçüncü taraflarla olan ilişkilerin düzenlenmesini sağlamak temel hedeflerimiz arasındadır.",
                    "Bu doğrultuda KYS politikalarımızın amacı; kuruluş genelinde kalite anlayışını güçlendirmek, süreçleri ölçülebilir ve sürdürülebilir hale getirmek ve tüm faaliyetlerde sürekli iyileştirme kültürünü yaygınlaştırmaktır.",
                ],
            },
            {
                "heading": "KYS Politikalarımızın Amaçları",
                "items": [
                    "Kuruluşta kalite anlayışının gelişimini sağlamak",
                    "Kârın, verimliliğin ve pazar payının artmasını desteklemek",
                    "Etkin bir yönetim yapısı kurmak",
                    "Maliyetlerin azalmasını sağlamak",
                    "Çalışanların tatminini artırmak",
                    "Kuruluş içi iletişimi iyileştirmek",
                    "Tüm faaliyetlerde geniş izleme ve kontrol sağlamak",
                    "İadelerin azalmasını sağlamak",
                    "Müşteri şikayetlerini azaltmak ve memnuniyeti artırmak",
                    "Ulusal ve uluslararası düzeyde uygulanabilirliği sağlamak",
                    "Kalite Yönetim Sistemleri (KYS) kurmak ve işletmek",
                    "Kalite Güvenliği Yönetimi eğitimlerini tüm personele vererek bilinç oluşturmak",
                    "Kalite Yönetimi konusunda periyodik değerlendirmeler yaparak mevcut riskleri tespit etmek, aksiyon planlarını gözden geçirmek ve takibini yapmak",
                    "Sözleşmelerden doğabilecek her türlü anlaşmazlık ve çıkar çatışmasını engellemek",
                    "Bilgiye erişilebilirlik ve bilgi sistemleri için iş gereksinimlerini karşılamak",
                ],
            },
        ],
    },
    "gizlilik-sozlesmesi": {
        "title": "Gizlilik Sözleşmesi",
        "kicker": "KURUMSAL",
        "summary": "Kişisel verilerin kullanımına ilişkin temel gizlilik yaklaşımımızı açıklar.",
        "blocks": [
            {
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel bilgilerinizin gizliliğine saygı duyar. Kişisel bilgiler, 6698 sayılı Kişisel Verilerin Korunması Kanunu’na tabidir.",
                    "Bu doğrultuda, internet sitesinde verdiğiniz tüm kişisel bilgiler yalnızca size hizmet sunmak amacıyla ve Kanun’a uygun şekilde kullanılmakta olup hiçbir şekilde üçüncü taraf kurum ve kuruluşlarla paylaşılmamaktadır.",
                    "Konumsal Bilgi Sistemleri, internet sitesi üzerinden kişisel bilgi toplama ve kullanımını asgari düzeyde tutmakta; toplanan kişisel bilgileri yalnızca işlemlerin gerçekleştirilebilmesi için kullanmaktadır.",
                ],
            },
        ],
    },
    "kullanim-kosullari": {
        "title": "Kullanım Koşulları",
        "kicker": "KURUMSAL",
        "summary": "İnternet sitesinin kullanımına ilişkin genel kuralları ve sorumluluk çerçevesini belirtir.",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini ziyaret etmekle veya kullanmakla, aşağıda yer alan koşulları kabul etmiş sayılırsınız. Konumsal Bilgi Sistemleri, bu sayfada yer alan koşullarda dilediği zaman önceden haber vermeksizin değişiklik yapma hakkına sahiptir.",
                ],
            },
            {
                "heading": "Fikri Mülkiyet Hakları",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini sadece kişisel kullanımınız için ziyaret etme, görüntüleme ve internet sitesinin sayfalarını sadece kişisel kullanımınız için kopyalama hakkına ve yetkisine sahip olduğunuzu kabul etmektesiniz.",
                    "Konumsal Bilgi Sistemleri internet sitesinde bulunan tüm görsel ve yazılı materyaller Konumsal Bilgi Sistemleri mülkiyetindedir ve Türk ve uluslararası telif hakkı kanunlarıyla korunmaktadır.",
                    "Önceden izin alınmaksızın internet sitesindeki bilgilerin ya da internet sitesine ilişkin her tür veri tabanı, yazılım ve görsel materyalin ticari amaçlarla kısmen ya da tamamen kopyalanması, değiştirilmesi, yayımlanması ve dağıtılması yasaktır. Aksi tespit edildiği durumlarda Konumsal Bilgi Sistemleri gerekli hukuki işlemleri başlatma hakkını saklı tutar.",
                ],
            },
            {
                "heading": "Sorumluluğun Sınırlandırılması",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, internet sitesine girilmesi, internet sitesinde yayımlanan bilgilerin ve diğer verilerin kullanılması sebebiyle, sözleşmenin ihlali, haksız fiil ya da başkaca sebeplere binaen doğabilecek doğrudan ya da dolaylı hiçbir zarardan sorumlu değildir.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde yer alan bilgilerin güncel ve geçerli tutulması için azami gayreti sarf etmektedir. Ürün ve hizmetlere ilişkin tüm yükümlülükler, bunların tabi oldukları sözleşmelerde belirlenmiş olup internet sitesinde bulunan hiçbir ifade söz konusu sözleşmeleri değiştiriyor olarak yorumlanamaz.",
                    "Konumsal Bilgi Sistemleri, internet sitesindeki malzemelerin, yazılımın veya hizmetlerin doğruluğunu ve eksiksizliğini garanti etmez. Ayrıca internet sitesindeki verilerde, hizmetlerde, ürünlerde ve fiyatlarda önceden bildirimde bulunmaksızın değişiklik yapma hakkını saklı tutar.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde bulunan fonksiyonların veya hizmetlerin kesintisiz ya da hatasız olacağını, sorunlu yönlerin giderileceğini ve internet sitesinin veya bu internet sitesini erişilebilir kılan sunucunun virüs ya da başka zararlı unsurlardan arınmış olduğunu garanti etmemektedir. Mevzuatın izin verdiği ölçüde, internet sitesinin veya bağlantılı teknik hizmetlerin sunulmasından ya da sunulamamasından kaynaklanan zararlardan sorumluluk kabul edilmez.",
                ],
            },
            {
                "heading": "Diğer İnternet Sitelerine Erişim",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesi içerisinden üçüncü şahıslara ait internet sitelerine bağlantılar verilebilir. Bu sitelere bağlandığınızda ilgili internet sitesinin kullanım koşullarına tabi olursunuz.",
                    "Konumsal Bilgi Sistemleri, bu internet sitelerinde yayımlanan içerikten veya gizlilik koşullarından ve bu internet sitelerinin kullanımından dolayı oluşabilecek doğrudan ve/veya dolaylı zararlardan sorumlu tutulamaz.",
                ],
            },
        ],
    },
    "cerez-politikasi": {
        "title": "Kişisel Veriler ve Çerez Politikası",
        "kicker": "KVKK",
        "summary": "Çerez kullanımı ve temel kişisel veri işleme süreçlerine ilişkin bilgilendirmeyi içerir.",
        "blocks": [
            {
                "heading": "Çerez (“Cookie”) Uyarısı",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri web sayfası deneyiminizi en iyi şekilde optimize etmek ve kullanıcı deneyiminizi geliştirebilmek için çerez kullanıyoruz.",
                    "Çerez kullanılmasını tercih etmezseniz tarayıcınızın ayarlarından çerezleri silebilir ya da engelleyebilirsiniz. Ancak bunun internet sitemizi kullanımınızı etkileyebileceğini hatırlatmak isteriz.",
                    "Tarayıcınızdan çerez ayarlarınızı değiştirmediğiniz sürece bu sitede çerez kullanımını kabul ettiğiniz varsayılacaktır. Toplanan verilerle ilgili bilgilere Gizlilik Politikamızdan ulaşabilirsiniz.",
                ],
            },
            {
                "heading": "Çerez Nedir ve Neden Kullanılmaktadır?",
                "paragraphs": [
                    "Çerezler, ziyaret ettiğiniz internet siteleri tarafından tarayıcılar aracılığıyla cihazınıza veya ağ sunucusuna depolanan küçük metin dosyalarıdır.",
                    "İnternet sitemizde çerez kullanılmasının başlıca amaçları aşağıda sıralanmaktadır:",
                ],
                "items": [
                    "İnternet sitesinin işlevselliğini ve performansını artırmak yoluyla sizlere sunulan hizmetleri geliştirmek",
                    "İnternet sitesini iyileştirmek, yeni özellikler sunmak ve sunulan özellikleri tercihlere göre kişiselleştirmek",
                    "İnternet sitesinin, sizin ve şirketimizin hukuki ve ticari güvenliğini sağlamak",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerez Türleri",
                "paragraphs": [
                    "Oturum çerezleri, ziyaretçilerimizin internet sitesini ziyaretleri süresince kullanılan ve tarayıcı kapatıldıktan sonra silinen geçici çerezlerdir.",
                    "Bu tür çerezlerin kullanılmasının temel amacı, ziyaret süresince internet sitesinin düzgün bir biçimde çalışmasını sağlamaktır. Örneğin birden fazla sayfadan oluşan çevrimiçi formların doldurulmasına yardımcı olur.",
                    "Kalıcı çerezler ise internet sitesinin işlevselliğini artırmak, ziyaretçilere daha hızlı ve iyi bir hizmet sunmak amacıyla kullanılır.",
                    "Bu çerezler tercihlerinizi hatırlamak için kullanılır ve tarayıcılar vasıtasıyla cihazınızda depolanır. Kalıcı çerezlerin bazı türleri, internet sitesini kullanım amacınız gibi hususlar göz önünde bulundurularak size özel öneriler sunulması için de kullanılabilir.",
                    "Aynı cihazla internet sitemizi tekrar ziyaret etmeniz durumunda, cihazınızda internet sitemiz tarafından oluşturulmuş bir çerez bulunup bulunmadığı kontrol edilir; böylece siteyi daha önce ziyaret ettiğiniz anlaşılır ve size sunulacak içerik buna göre belirlenir.",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerezler",
                "paragraphs": [
                    "Otantikasyon çerezleri, ziyaretçilerin şifrelerini kullanarak internet sitesine giriş yapmaları durumunda devreye girer. Bu çerezler sayesinde kullanıcının her sayfada yeniden şifre girmesi önlenir.",
                    "Analitik çerezler ise internet sitesini ziyaret edenlerin sayısı, görüntülenen sayfalar, ziyaret saatleri ve sayfa kaydırma hareketleri gibi analitik sonuçların üretilmesini sağlar.",
                ],
            },
        ],
    },
    "kvkk-bilgilendirme": {
        "title": "KVKK Bilgilendirme Metni",
        "kicker": "KVKK",
        "summary": "6698 sayılı Kanun kapsamında kişisel verilerin işlenmesine ilişkin aydınlatma metnidir.",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; 6698 sayılı Kişisel Verilerin Korunması Kanunu (“KVKK”) ve ilgili mevzuat kapsamında kişisel verilerinizin işlenmesi, saklanması ve aktarılmasına ilişkin sizleri bilgilendirmek amacıyla işbu aydınlatma metnini hazırladık.",
                    "Bu metin; çalışanlarımızı, çalışan adaylarımızı, stajyer adaylarımızı, ziyaretçilerimizi, hissedar/ortaklarımızı, tedarikçilerimizi, ürün ve hizmet alan kişileri ve potansiyel müşterilerimizi kapsar.",
                    "Kişisel verilerin güvenliği hususuna verdiğimiz önem doğrultusunda, bünyemizde bulunan her türlü kişisel veri KVKK’ya uygun şekilde işlenmekte, saklanmakta ve aktarılmaktadır.",
                    "Kimliğinizi belirli veya belirlenebilir kılan her türlü bilginiz kişisel veri olarak veri sorumlusu sıfatıyla Konumsal Bilgi Sistemleri tarafından işlenebilir. Kişisel verilerin işlenmesi; elde edilmesi, kaydedilmesi, depolanması, muhafaza edilmesi, değiştirilmesi, yeniden düzenlenmesi, açıklanması, aktarılması, devralınması, elde edilebilir hale getirilmesi, sınıflandırılması veya kullanılmasının engellenmesi gibi tüm işlemleri kapsar.",
                ],
            },
            {
                "heading": "İşlenen Kişisel Veri Kategorileri",
                "items": [
                    "Çalışanlarımızın kimlik, iletişim, özlük, mesleki deneyim, sağlık ve adli sicil raporu bilgileri, görsel kayıtları (vesikalık fotoğraf), kapı giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri ve şifre bilgileri",
                    "Çalışan adaylarımızın kimlik (ad-soyad) ve özgeçmiş bilgileri (okul, iletişim bilgileri, diploma bilgileri)",
                    "Stajyerlerimizin kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri), giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri ve şifre bilgileri",
                    "Ziyaretçilerimizin kimlik (ad-soyad) bilgileri",
                    "Çevrimiçi ziyaretçilerimizin ad-soyad, e-posta, telefon numarası ve işyeri bilgileri",
                    "Hissedar/ortaklarımızın kimlik, özgeçmiş, fatura, bilanço ve finansal performans bilgileri",
                    "Tedarikçilerimizin kimlik ve iletişim bilgileri (adres, telefon numarası, e-posta, IBAN vb.)",
                    "Ürün ve hizmet alan kişilerin kimlik, iletişim ve çağrı merkezi kayıtları",
                    "Potansiyel müşterilerimizin kimlik ve iletişim bilgileri",
                ],
            },
            {
                "heading": "Kişisel Verilerin İşlenme Amaçları",
                "paragraphs": [
                    "Kişisel verilerinizin kullanımı sırasında özel hayatın gizliliği ile temel hak ve özgürlüklerin korunması temel prensibimizdir. Kişisel veriler aşağıdaki amaçlarla işlenebilir:",
                ],
                "items": [
                    "Çalışan verileri; iş akdi ve mevzuat kaynaklı yükümlülüklerin yerine getirilmesi, insan kaynakları süreçlerinin planlanması, hukuk işlerinin takibi, çalışan memnuniyeti ve bağlılığı süreçleri, yan haklar ve menfaatler, eğitim faaliyetleri, denetim/etik faaliyetleri, satın alma süreçleri, pazarlama süreçleri, finans ve muhasebe işleri ile bilgi güvenliği süreçlerinin yürütülmesi amacıyla",
                    "Çalışan adayı verileri; insan kaynakları süreçlerinin planlanması ile çalışan adayı / stajyer / öğrenci seçme ve yerleştirme süreçlerinin yürütülmesi amacıyla",
                    "Stajyer verileri; çalışan adayı / stajyer / öğrenci seçme ve yerleştirme süreçleri ile bilgi güvenliği süreçlerinin yürütülmesi amacıyla",
                    "Ziyaretçi verileri; ziyaretçi kaydı oluşturulması ve takibi amacıyla",
                    "Hissedar/ortak verileri; mal ve hizmet satın alım süreçleri, pazarlama süreçleri, sözleşme süreçleri ve finans-muhasebe işlerinin yürütülmesi amacıyla",
                    "Tedarikçi verileri; finans ve muhasebe işlerinin yürütülmesi amacıyla",
                    "Ürün ve hizmet alan kişi verileri; sözleşme sürecinin yürütülmesi ve müşteri memnuniyetine yönelik aktivitelerin yürütülmesi amacıyla",
                    "Potansiyel müşteri verileri; ürün ve hizmetlerin pazarlama süreçlerinin yürütülmesi amacıyla",
                ],
                "paragraphs_after": [
                    "Yukarıda sayılan amaçlar kapsamında gerçekleştirilen kişisel veri işleme faaliyetinin, KVKK’da öngörülen hukuka uygunluk sebeplerinden herhangi birine dayanmaması halinde ilgili işleme süreci için açık rızanız alınmaktadır.",
                ],
            },
            {
                "heading": "Toplama Yöntemleri ve Hukuki Sebepler",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel verilerinizi şirketimizle iletişime geçmeniz ve/veya hukuki ilişkinizin kurulması esnasında ve ilişkinin devamı süresince; sizlerden, ortaklıklardan, grup şirketlerinden, iştiraklerden, iş birliği yaptığımız veya sözleşme ilişkimizin bulunduğu çözüm ortaklarından, üçüncü kişilerden ve yasal mercilerden; çağrı merkezi, internet, mobil uygulamalar, sosyal medya, kamuya açık mecralar, eğitimler, organizasyonlar ve benzeri etkinlikler aracılığıyla toplayabilir.",
                    "Bu toplama ve işleme faaliyetleri, Kanun’un 5, 6 ve 8. maddelerinde öngörülen çerçevede yürütülmektedir.",
                ],
                "items": [
                    "Çalışan verileri; çalışanlarla sözleşme imzalanması ve veri sorumlusunun meşru menfaatleri kapsamında",
                    "Çalışan adayı verileri; veri sorumlusunun meşru menfaatleri ve kanunlarda öngörülmesi kapsamında",
                    "Stajyer verileri; veri sorumlusunun meşru menfaatleri kapsamında",
                    "Ziyaretçi verileri; hukuki yükümlülüğün yerine getirilmesi kapsamında",
                    "Hissedar/ortak verileri; hukuki yükümlülüğün yerine getirilmesi kapsamında",
                    "Tedarikçi verileri; veri sorumlusunun meşru menfaatleri kapsamında",
                    "Ürün ve hizmet alan kişi verileri; sözleşmenin kurulması/ifası ve veri sorumlusunun meşru menfaatleri kapsamında",
                    "Potansiyel müşteri verileri; veri sorumlusunun meşru menfaatleri kapsamında",
                ],
            },
            {
                "heading": "Üçüncü Kişilere ve Yurt Dışına Aktarım",
                "paragraphs": [
                    "Kişisel verileriniz; yasal düzenlemelerin öngördüğü kapsamda, faaliyetlerin mevzuata uygun yürütülmesi, hukuk işlerinin takibi, yetkili kişi, kurum ve kuruluşlara bilgi verilmesi, iş akdi ve mevzuat yükümlülüklerinin yerine getirilmesi, iş faaliyetlerinin yürütülmesi/denetimi ve iş sağlığı/güvenliği faaliyetlerinin yürütülmesi amaçlarıyla yurt içindeki yetkili kamu kurum ve kuruluşlarına aktarılabilir.",
                    "Ayrıca, yasal düzenlemelerin öngördüğü kapsamda faaliyetlerin mevzuata uygun yürütülmesi ve yetkili kişi, kurum ve kuruluşlara bilgi verilmesi amaçlarıyla yurt içindeki gerçek kişiler veya özel hukuk tüzel kişilerine aktarım yapılabilir.",
                    "Konumsal Bilgi Sistemleri olarak kişisel verilerinizi yurt dışına aktarmamaktayız.",
                ],
            },
            {
                "heading": "Saklama Süresi",
                "items": [
                    "Kanunda veya ilgili mevzuatta verinin saklanması için bir süre belirlenmişse, söz konusu veri en az bu süre kadar saklanır.",
                    "Olası bir mahkeme talebi, yetkili idari merci talebi veya tarafı olunabilecek bir ihtilaf ihtimali gözetilerek, mevzuatta öngörülen sürelere 6 ay ila 1 yıl arası ek süre ilave edilerek saklama süresi belirlenebilir.",
                    "Saklama süresi sonunda veriler silinir, yok edilir veya anonim hale getirilir.",
                    "Mevzuatta belirlenmiş saklama süresi dolmadan önce silme talebinde bulunulması halinde talep yerine getirilemeyebilir.",
                    "Mevzuatta saklama süresi öngörülmeyen ve işleme amacı sona ermiş veriler için silme talebinde bulunulması halinde veri derhal veya en geç 6 ay içinde silinir.",
                ],
            },
            {
                "heading": "Haklarınız",
                "paragraphs": [
                    "KVKK kapsamında kişisel verilerinize ilişkin aşağıdaki haklara sahipsiniz:",
                ],
                "items": [
                    "Kişisel verilerinizin işlenip işlenmediğini öğrenme",
                    "Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme",
                    "Kişisel verilerin işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme",
                    "Yurt içinde veya yurt dışında kişisel verilerinizin aktarıldığı üçüncü kişileri bilme",
                    "Kişisel verilerinizin eksik veya yanlış işlenmiş olması halinde bunların düzeltilmesini isteme",
                    "KVKK’da öngörülen şartlar çerçevesinde kişisel verilerinizin silinmesini veya yok edilmesini isteme",
                    "Düzeltme, silme veya yok etme taleplerinizin, verilerin aktarıldığı üçüncü kişilere bildirilmesini isteme",
                    "Kişisel verilerin kanuna aykırı işlenmesi sebebiyle zarara uğramanız halinde zararın giderilmesini talep etme",
                ],
            },
            {
                "heading": "Başvuru Usulü",
                "paragraphs": [
                    "Kişisel verileriniz ile ilgili başvuru ve taleplerinizi aşağıdaki yöntemlerle iletebilirsiniz:",
                ],
                "items": [
                    "Islak imzalı dilekçe ve kimlik fotokopisi ile Konumsal Bilgi Sistemleri, Üniversiteler Mah. Cyberpark Tepe Binası Zemin Kat No:19-31 Bilkent 06800 Çankaya/ANKARA adresine göndererek",
                    "Geçerli bir kimlik belgesi ile birlikte Konumsal Bilgi Sistemleri’ne bizzat başvurarak",
                    "Kayıtlı elektronik posta adresi ve güvenli elektronik imza ya da mobil imza kullanarak bilgi@konumsal.com.tr adresine göndererek",
                ],
                "paragraphs_after": [
                    "Veri Sorumlusuna Başvuru Usul ve Esasları Hakkında Tebliğ uyarınca başvuruda isim, soy isim, başvuru yazılı ise imza, T.C. kimlik numarası (yabancılar için pasaport numarası), tebligata esas yerleşim yeri veya iş yeri adresi, varsa bildirime esas elektronik posta adresi, telefon numarası ve faks numarası ile talep konusuna dair bilgilerin bulunması zorunludur.",
                    "Başvurunun açık ve anlaşılır olması, talep edilen hususun net şekilde belirtilmesi ve gerekli bilgi-belgelerin eklenmesi gerekir. Başkası adına yapılacak başvurularda özel vekâletname ibraz edilmelidir. Yetkisiz üçüncü kişilerin başkası adına yaptığı talepler değerlendirmeye alınmaz.",
                ],
            },
            {
                "heading": "Başvuruların Cevaplanma Süresi",
                "paragraphs": [
                    "Kişisel verilerinize ilişkin hak talepleriniz, bize ulaştığı tarihten itibaren en geç 30 gün içinde değerlendirilerek cevaplandırılır. Başvurunun olumsuz değerlendirilmesi halinde gerekçeli ret sebepleri, bildirilen adrese elektronik posta veya posta yolu dahil seçilen iletişim yöntemi ile iletilir.",
                ],
            },
            {
                "heading": "Açık Rıza",
                "paragraphs": [
                    "Web sitemiz üzerinden tarafımıza sağlamış olduğunuz kişisel verilerinizin Kanun’a ve işbu 6698 sayılı Kişisel Verilerin Korunması Kanunu’na uygun şekilde ve belirtilen amaçlarla işlenebileceğini kabul etmektesiniz.",
                    "Ayrıca, Kanun kapsamında yapılması gereken aydınlatma yükümlülüğünün yerine getirildiğini, metni okuduğunuzu, anladığınızı, hak ve yükümlülüklerinizin bilincinde olduğunuzu beyan etmiş sayılırsınız.",
                ],
            },
        ],
    },
}


LEGAL_PAGES = {
    "kalite-politikasi": {
        "title": "Kalite Politikamız",
        "blocks": [
            {
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; ISO/IEC 27001:2013 Bilgi Güvenliği Yönetim Sistemi (BGYS), ISO/IEC 9001:2015 Kalite Yönetim Sistemi (KYS) standartlarından kurulan sistemlerin ana teması",
                ],
                "items": [
                    "Müşteri memnuniyetinin artması",
                    "Pazar payının artması",
                    "Karın artması",
                    "Çalışan memnuniyetinin artması",
                    "Maliyetlerin azalması",
                    "Yüksek rekabet gücü",
                ],
            },
            {
                "paragraphs": [
                    "Kalite ve risk yönetimini güvence altına almak, kalite yönetimi süreç performansını ölçmek ve bilgi güvenliği ve müşteri memnuniyeti ile ilgili konularda üçüncü taraflarla olan ilişkilerin düzenlenmesini sağlamaktır.",
                    "Bu doğrultuda KYS Politikalarımızın amacı KYS kapsamında;",
                ],
                "items": [
                    "Kuruluşta kalite anlayışının gelişimini",
                    "Kârın, verimliliğin ve pazar payının artmasını",
                    "Etkin bir yönetimi",
                    "Maliyetin azalmasını",
                    "Çalışanların tatminini",
                    "Kuruluş içi iletişimde iyileşmeyi",
                    "Tüm faaliyetlerde geniş izleme ve kontrolü",
                    "İadelerin azalmasını",
                    "Müşteri şikayetinin azalması, memnuniyetin artmasını",
                    "Ulusal ve uluslararası düzeyde uygulanabilirliği sağlamak",
                    "Kalite Yönetim Sistemleri (KYS) kurmak ve işletmek",
                    "Kalite Güvenliği Yönetimi eğitimlerini tüm personele vererek bilinçlendirmeyi sağlamak",
                    "Kalite Yönetimi konusunda periyodik olarak değerlendirmeler yaparak mevcut riskleri tespit etmek. Değerlendirmeler sonucunda, aksiyon planlarını gözden geçirmek ve takibini yapmak",
                    "Sözleşmelerden doğabilecek her türlü anlaşmazlık ve çıkar çatışmasını engellemek",
                    "Bilgiye erişilebilirlik ve bilgi sistemleri için iş gereksinimlerini karşılamaktır",
                ],
            },
        ],
    },
    "gizlilik-sozlesmesi": {
        "title": "Gizlilik Sözleşmesi",
        "blocks": [
            {
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel bilgilerinizin gizliliğine saygı duyar. Kişisel bilgiler, 6698 sayılı Kişisel Verilerin Korunması Kanunu’na tabidir. Bu doğrultuda, internet sitesinde verdiğiniz tüm kişisel bilgiler, yalnızca size hizmet amaçlı ve Kanun’a uygun olarak kullanılmakta ve hiçbir şekilde üçüncü taraf kurum ve kuruluşlarla paylaşılmamaktadır. Konumsal Bilgi Sistemleri, internet sitesinden kişisel bilgi toplama ve kullanımını asgari düzeyde tutmakta ve toplanan kişisel bilgileri sadece işlemlerin gerçekleşebilmesi için kullanmaktadır.",
                ],
            },
        ],
    },
    "kullanim-kosullari": {
        "title": "Kullanım Koşulları",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini ziyaret etmekle veya kullanmakla, aşağıda yer alan koşulları kabul etmiş sayılırsınız. Konumsal Bilgi Sistemleri, bu sayfada yer alan koşullarda dilediği zaman önceden haber vermeksizin değişiklik yapma hakkına sahiptir.",
                ],
            },
            {
                "heading": "Fikri Mülkiyet Hakları",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini sadece kişisel kullanımınız için ziyaret etme, görüntüleme ve internet sitesinin sayfalarını sadece kişisel kullanımınız için kopyalama hakkına ve yetkisine sahip olduğunuzu kabul etmektesiniz. Konumsal Bilgi Sistemleri internet sitesinde bulunan tüm görsel ve yazılı materyal Konumsal Bilgi Sistemleri mülkiyetindedir ve Türk ve uluslararası telif hakkı kanunlarıyla korunmaktadır. Önceden izin alınmaksızın internet sitesindeki bilgilerin ya da internet sitesine ilişkin her tür veri tabanı, yazılım, görsel materyalin ticari amaçlarla kısmen ya da tamamen kopyalanması, değiştirilmesi, yayımlanması ve dağıtımı engellenmiştir. Aksi tespit edildiği durumlarda Konumsal Bilgi Sistemleri gerekli hukuki işlemleri başlatma hakkını saklı tutar.",
                ],
            },
            {
                "heading": "Sorumluluğun Sınırlandırılması",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, internet sitesine girilmesi, internet sitesinde yayımlanan bilgilerin ve diğer verilerin kullanılması sebebiyle, sözleşmenin ihlali, haksız fiil ya da başkaca sebeplere binaen, cezai tazminatlar da dahil olmak üzere doğabilecek doğrudan ya da dolaylı hiçbir zarardan sorumlu değildir.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde yer alan bilgilerin güncel ve geçerli tutulması için azami gayreti sarf etmektedir. Konumsal Bilgi Sistemleri’nin ürünlerine ve hizmetlerine ilişkin tüm yükümlülükleri, bunların tabi oldukları sözleşmelerde belirlenmiş olup, internet sitesinde bulunan hiçbir şey söz konusu sözleşmeleri değiştiriyor olarak yorumlanamaz. Konumsal Bilgi Sistemleri; ayrıca, internet sitesindeki malzemelerin, yazılımın veya hizmetlerin doğruluğunu ve eksiksiz olduğunu garanti etmez. Konumsal Bilgi Sistemleri internet sitesindeki verilerde ve hizmetlerde veya ürünlerde ve fiyatlarında önceden bildirimde bulunmaksızın değişiklikler yapma hakkını saklı tutar.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde bulunan fonksiyonların veya hizmetlerin kesintisiz ya da hatadan arınmış olacağının, sorunlu yanlarının giderileceğinin ve internet sitesinin veya bu internet sitesini erişilebilir kılan sunucunun virüslerden veya başka zararlı unsurlardan arınmış olduğunun garantisini vermemektedir. Mevzuat’ın müsaade ettiği ölçüde Konumsal Bilgi Sistemleri’nin, internet sitesinin veya herhangi bir bağlantılı hizmet veya teknik hizmetin yerine getirilmesinden veya getirilmemesinden kaynaklanan zararlardan hiçbir sorumluluğu bulunmamaktadır.",
                ],
            },
            {
                "heading": "Diğer İnternet Sitelerine Erişim",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesi içerisinden üçüncü şahıslara ait internet sitelerine bağlantılar yerleştirebilir. Bu üçüncü şahıs internet sitelerine bağlandığınızda, ilgili internet sitesinin kullanım koşullarına tabi sayılırsınız. Konumsal Bilgi Sistemleri, bu internet sitelerinde yayımlanan içerikten veya gizlilik koşullarından ve bu internet sitelerinin kullanımından dolayı oluşabilecek doğrudan ve/veya dolaylı hiçbir zarardan hiçbir şekilde sorumlu tutulamaz.",
                ],
            },
        ],
    },
    "cerez-politikasi": {
        "title": "Kişisel Veriler ve Çerez Politikası",
        "blocks": [
            {
                "heading": "ÇEREZ (“COOKIE”) UYARISI",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri web sayfası deneyiminizi en iyi şekilde optimize etmek ve kullanıcı deneyiminizi geliştirebilmek için Cookie kullanıyoruz. Cookie kullanılmasını tercih etmezseniz tarayıcınızın ayarlarından Cookie’leri silebilir ya da engelleyebilirsiniz. Ancak bunun internet sitemizi kullanımınızı etkileyebileceğini hatırlatmak isteriz. Tarayıcınızdan Cookie ayarlarınızı değiştirmediğiniz sürece bu sitede çerez kullanımını kabul ettiğinizi varsayacağız. Toplanan verilerle ilgili bilgilere Gizlilik Politikası’mızdan ulaşabilirsiniz.",
                ],
            },
            {
                "heading": "İNTERNET SİTESİNDE KULLANILAN ÇEREZLER Çerez Nedir ve Neden Kullanılmaktadır?",
                "paragraphs": [
                    "Çerezler, ziyaret ettiğiniz internet siteleri tarafından tarayıcılar aracılığıyla cihazınıza veya ağ sunucusuna depolanan küçük metin dosyalarıdır.",
                    "İnternet Sitemizde çerez kullanılmasının başlıca amaçları aşağıda sıralanmaktadır:",
                ],
                "items": [
                    "İnternet sitesinin işlevselliğini ve performansını arttırmak yoluyla sizlere sunulan hizmetleri geliştirmek,",
                    "İnternet Sitesini iyileştirmek ve İnternet Sitesi üzerinden yeni özellikler sunmak ve sunulan özellikleri sizlerin tercihlerine göre kişiselleştirmek;",
                    "İnternet Sitesinin, sizin ve Şirketimizin hukuki ve ticari güvenliğinin teminini sağlamak.",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerez Türleri",
                "paragraphs": [
                    "Oturum Çerezleri (Session Cookies)",
                    "Oturum çerezleri ziyaretçilerimizin İnternet Sitesini ziyaretleri süresince kullanılan, tarayıcı kapatıldıktan sonra silinen geçici çerezlerdir.",
                    "Bu tür çerezlerin kullanılmasının temel amacı ziyaretiniz süresince İnternet Sitesinin düzgün bir biçimde çalışmasının teminini sağlamaktır.",
                    "Örneğin; birden fazla sayfadan oluşan çevrimiçi formları doldurmanızın sağlanmaktadır.",
                    "Kalıcı Çerezler (Persistent Cookies)",
                    "Kalıcı çerezler İnternet Sitesinin işlevselliğini artırmak, ziyaretçilerimize daha hızlı ve iyi bir hizmet sunmak amacıyla kullanılan çerez türleridir.",
                    "Bu tür çerezler tercihlerinizi hatırlamak için kullanılır ve tarayıcılar vasıtasıyla cihazınızda depolanır.",
                    "Kalıcı çerezlerin bazı türleri; İnternet Sitesini kullanım amacınız gibi hususlar göz önünde bulundurarak sizlere özel öneriler sunulması için kullanılabilmektedir.",
                    "Kalıcı çerezler sayesinde İnternet Sitemizi aynı cihazla tekrardan ziyaret etmeniz durumunda, cihazınızda İnternet Sitemiz tarafından oluşturulmuş bir çerez olup olmadığı kontrol edilir ve var ise, sizin siteyi daha önce ziyaret ettiğiniz anlaşılır ve size iletilecek içerik bu doğrultuda belirlenir ve böylelikle sizlere daha iyi bir hizmet sunulur.",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerezler",
                "paragraphs": [
                    "Otantikasyon Çerezleri(Authentication Cookies)",
                    "Ziyaretçiler, şifrelerini kullanarak internet sitesine giriş yapmaları durumunda, bu tür çerezler ile, ziyaretçinin internet sitesinde ziyaret ettiği her bir sayfada site kullanıcısı olduğu belirlenerek, kullanıcının her sayfada şifresini yeniden girmesi önlenir.",
                    "Analitik Çerezler (Analytical Cookies)",
                    "Analitik çerezler ile internet sitesini ziyaret edenlerin sayıları, internet sitesinde görüntülenen sayfaların tespiti, internet sitesi ziyaret saatleri, internet sitesi sayfaları kaydırma hareketleri gibi analitik sonuçların üretimini sağlayan çerezlerdir.",
                ],
            },
        ],
    },
    "kvkk-bilgilendirme": {
        "title": "KVKK Bilgilendirme Metni",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; 6698 sayılı Kişisel Verilerin Korunması Kanunu (“KVKK”) ve ilgili mevzuat ve yasal düzenlemelerden kaynaklanan faaliyetleri çerçevesinde kişisel verilerinizin işlenmesi, saklanması ve aktarılmasına ilişkin siz",
                ],
                "items": [
                    "Çalışanlarımızı",
                    "Çalışan Adaylarımızı,",
                    "Stajyer Adaylarımızı,",
                    "Ziyaretçilerimizi,",
                    "Hissedar/ Ortaklarımızı,",
                    "Tedarikçilerimizi",
                    "Ürün ve hizmet alan kişileri",
                    "Potansiyel Müşterilerimizi",
                ],
            },
            {
                "paragraphs": [
                    "bilgilendirmek amacıyla işbu aydınlatma metnini hazırladık. Konumsal Bilgi Sistemleri olarak, kişisel verilerin güvenliği hususuna verdiğimiz önem doğrultusunda sizi bilgilendirmek istiyoruz.",
                    "Bünyemizde barındırdığımız her türlü kişisel veri 6698 sayılı Kişisel Verilerin Korunması Kanunu’na uygun olarak işlenmekte, saklanmakta ve aktarılmaktadır. Kişisel verilerinizin tarafımızla paylaşılması halinde, kimliğinizi belirli veya belirlenebilir kılan her türlü bilginiz, Kişisel Veri olarak aşağıdaki kapsamda, Veri Sorumlusu sıfatıyla Konumsal Bilgi Sistemleri tarafından işlenecektir. “Kişisel Verilerinizin işlenmesi” ise bu verilerin elde edilmesi, kaydedilmesi, depolanması, muhafaza edilmesi, değiştirilmesi, yeniden düzenlenmesi, açıklanması, aktarılması, devralınması, elde edilebilir hale getirilmesi, sınıflandırılması ya da kullanılmasının engellenmesi gibi veriler üzerinde gerçekleştirilen her türlü işlemi ifade etmektedir. Konumsal Bilgi Sistemleri olarak kişisel verilerinizin güvenliğine en üst düzeyde önem vererek, sizlere sunduğumuz tüm ürün ve hizmetlerimizde kişisel verilerinizin güvenliğinin ön planda olduğu bilinciyle faaliyetlerimize devam ettiğimizi belirtmek isteriz. Aşağıdaki tabloda hangi kişisel verileri tuttuğumuz belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın kimlik, iletişim, özlük, mesleki deneyim, sağlık ve adli sicil raporu bilgileri, görsel kayıtları (vesikalık fotoğraf), kapı giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri, şifre bilgileri",
                    "Çalışan Adaylarımızın kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri),",
                    "Stajyerlerimizin kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri), giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri, şifre bilgileri",
                    "Ziyaretçilerimizin kimlik (ad-soyad) bilgileri",
                    "Çevrimçi ziyaretçilerimizin ad/soyad, e-posta, telefon no ve işyeri bilgileri",
                    "Hissedar/ Ortaklarımızın kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri gibi), fatura bilgileri, bilanço bilgileri, finansal performans bilgileri",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) bilgileri",
                    "Ürün ve Hizmet Alan kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta IBAN bilgileri gibi), çağrı merkezi kayıtları",
                    "Potansiyel Müşterilerimizin kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta gibi) bilgileri tutulmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerin İşlenme Amaçları Nelerdir?",
                "paragraphs": [
                    "Kişisel verilerinizin Konumsal Bilgi Sistemleri hizmet verdiği işlemler için kullanılması, özel hayatınızın gizliliği ve temel hak ve özgürlüklerinizin korunması temel prensibimizdir. Aşağıda Konumsal Bilgi Sistemleri’nin kişisel verileri hangi amaçla işlediği belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın yukarda belirtilen kişisel verileri, Çalışanlar İçin İş Akdi ve Mevzuat Kaynaklı Yükümlülüklerin Yerine Getirilmesi, İnsan Kaynakları Süreçlerinin Planlanması, Hukuk İşlerinin Takibi Ve Yürütülmesi, Çalışan Memnuniyeti Ve Bağlılığı Süreçlerinin Yürütülmesi, Çalışanlar İçin Yan Haklar Ve Menfaatleri Süreçlerinin Yürütülmesi, Eğitim Faaliyetlerinin Yürütülmesi, Denetim / Etik Faaliyetlerinin Yürütülmesi, Mal / Hizmet Satın Alım Süreçlerinin Yürütülmesi, Ürün ve Hizmetlerin Pazarlama Süreçlerinin Yürütülmesi, Finans ve Muhasebe İşlerinin Yürütülmesi ve Bilgi Güvenliği Süreçlerinin Yürütülmesi amacıyla işlenir.",
                    "Çalışan Adaylarımızın yukarda belirtilen kişisel verileri insan kaynakları süreçlerinin planlanması ve Çalışan Adayı / Stajyer / Öğrenci Seçme Ve Yerleştirme Süreçlerinin Yürütülmesi amacıyla tutulur.",
                    "Stajyerlerimizin yukarda belirtilen kişisel verileri Çalışan Adayı / Stajyer / Öğrenci Seçme Ve Yerleştirme Süreçlerinin Yürütülmesi ve Bilgi Güvenliği Süreçlerinin Yürütülmesi amacıyla işlenir.",
                    "Ziyaretçilerimizin kimlik bilgileri (ad-soyad) Ziyaretçi Kaydı Oluşturulması ve Takibi oluşturulması amacıyla işlenir.",
                    "Hissedar/ Ortaklarımızın yukarda belirtilen kişisel verileri, Mal Hizmet Satın Alım Süreçlerinin Yürütülmesi, Ürün ve hizmetlerin pazarlama süreçlerinin yürütülmesi, Sözleşme Sürecinin yürütülmesi, Finans ve Muhasebe İşlerinin Yürütülmesi amacıyla işlenir.",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) Finans Ve Muhasebe İşlerinin Yürütülmesi amacıyla işlenir.",
                    "Ürün ve Hizmet Alan kişilerin yukarda belirtilen kişisel verileri, Sözleşme sürecinin yürütülmesi ve Müşteri Memnuniyetine Yönelik Aktivitelerin Yürütülmesi amacıyla işlenir.",
                    "Potansiyel Müşterilerimizin kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta gibi) Ürün ve Hizmetlerin pazarlama süreçlerinin yürütülmesi amacıyla işlenir.",
                    "Yukarıda sayılan amaçlar kapsamında gerçekleştirilen kişisel veri işleme faaliyetinin, KVKK kapsamında öngörülen ilgili kişinin açık rızasının varlığı dışındaki hukuka uygunluk nedenlerinden herhangi birini karşılamaması halinde, ilgili işleme sürecine yönelik olarak Konumsal Bilgi Sistemleri tarafından ilgilinin açık rızası alınmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizin Tutulma Yöntemleri ve Hukuki Sebepleri Nelerdir?",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel verilerinizi Şirketimizle iletişime geçmeniz ve/veya hukuki ilişkinizin kurulması esnasında ve söz konusu ilişkinin devamı süresince sizlerden, ortaklıklar, grup şirketleri, iştirakler, işbirliği yaptığımız ya da sözleşme ilişkimizin bulunduğu çözüm ortakları, dâhil olmak üzere üçüncü kişilerden ve yasal mercilerden olmak kaydıyla çağrı merkezi, internet, mobil uygulamalar, sosyal medya ve diğer kamuya açık mecralar veya düzenlenen eğitimler, organizasyonlar ve benzeri etkinlikler aracılığıyla yukarıda yer verilen amaç ve hizmetlerin Kanun’un 5, 6 ve 8. madde hükümlerinde öngörülen çerçevede verilebilmesi amacı ile toplanmaktadır. Kişisel verilerinizin tutulma nedenlerinin hukuki sebepleri ayrıntılı olarak aşağıda belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın yukarda belirtilen kişisel verileri, çalışanlarla sözleşme imzalanması ve veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır.",
                    "Çalışan Adaylarımızın yukarda belirtilen kişisel verileri, veri sorumlusunun meşru menfaatleri ve kanunlarda öngörülmesi amacıyla toplanmaktadır .",
                    "Stajyerlerimizin yukarda belirtilen kişisel verileri veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır .",
                    "Ziyaretçilerimizin kimlik (ad-soyad) hukuki yükümlülüğün yerine getirilmesi amacıyla toplanır.",
                    "Hissedar/ Ortaklarımızın yukarda belirtilen kişisel verileri hukuki yükümlülüğün yerine getirilmesi amacıyla toplanmaktadır.",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır.",
                    "Ürün ve Hizmet Alan kişilerin yukarda belirtilen kişisel verileri, müşterilerimizle sözleşme imzalanması ve veri sorumlusu olarak firmamızın meşru menfaatleri doğrultusunda toplanmaktadır.",
                    "Potansiyel Müşterilerimizin yukarda belirtilen kişisel veriler, veri sorumlusu olarak firmamızın meşru menfaatleri doğrultusunda toplanmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizi Üçüncü Bir Kişiye Aktarıyor Muyuz?",
                "paragraphs": [
                    "Kişisel verileriniz,",
                ],
                "items": [
                    "Yasal düzenlemenin öngördüğü kapsamda, faaliyetlerin mevzuata uygun yürütülmesi, hukuk işlerinin takibi ve yürütülmesi, yetkili kişi, kurum ve kuruluşlara bilgi verilmesi, çalışanlar için iş akdi ve mevzuattan kaynaklı yükümlülüklerin yerine getirilmesi, iş faaliyetlerinin yürütülmesi/denetimi ve iş sağlığı/güvenliği faaliyetlerinin yürütülmesi amaçlarıyla yurt içindeki Yetkili Kamu Kurum ve Kuruluşlarına, ve",
                    "Yasal düzenlemenin öngördüğü kapsamda, faaliyetlerin mevzuata uygun yürütülmesi ve yetkili kişi, kurum ve kuruluşlara bilgi verilmesi amaçlarıyla yurt içindeki Gerçek Kişiler veya Özel Hukuk Tüzel Kişileri ’ne aktarılabilecektir.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizi Yurt Dışına Aktarıyor Muyuz?",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak, kişisel verilerinizi yurt dışına aktarmamaktayız.",
                ],
            },
            {
                "heading": "Kişisel Verileriniz Ne Kadar Süre ile Saklanır?",
                "paragraphs": [
                    "Kişisel verilerinizin saklama süresi aşağıdaki şekildedir:",
                ],
                "items": [
                    "Kanunda veya ilgili mevzuatta verinin saklanması için bir süre belirlenmişse söz konusu veri en az bu süre kadar saklanmak zorundadır. Olası bir mahkeme talebinin veya kanunla yetkili kılınmış bir idari merciinin ilgili veriye ilişkin talebinin tarafımıza geç ulaşması veya tarafı olabileceğimiz bir ihtilafın meydana gelmesi gibi ihtimaller gözetilmek suretiyle, verilerinizin saklanması için mevzuatta öngörülen sürelere 6 ay ila 1 yıl arası bir süre eklenerek verilerin saklama süresi belirlenmekte ve belirlenen sürenin sonunda söz konusu veriler silinmektedir.",
                    "Saklama süresi mevzuatta belirlenmiş verilerinizin öngörülen sürelerden önce silinmesini talep etmeniz halinde söz konusu talebiniz gerçekleştirilemeyecektir.",
                    "Saklama süresine ilişkin mevzuatta bir süre öngörülmeyen ve işleme amacı olmayan verileriniz silinmesine dair talepte bulunmanız halinde ise derhal veya en geç 6 ay içerisinde silinir.",
                ],
            },
            {
                "heading": "Kişisel Verileriniz İle İlgili Olarak Kullanabileceğiniz Haklarınız Nelerdir?",
                "paragraphs": [
                    "Kişisel verilerinize ilişkin;",
                ],
                "items": [
                    "Kişisel verilerinizin işlenip işlenmediğini öğrenme,",
                    "Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme,",
                    "Kişisel verilerin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme,",
                    "Yurt içinde veya yurt dışında kişisel verilerinizin aktarıldığı üçüncü kişileri bilme,",
                    "Kişisel verilerinizin eksik veya yanlış işlenmiş olması halinde bunların düzeltilmesini isteme,",
                    "KVKK mevzuatında öngörülen şartlar çerçevesinde kişisel verilerinizin silinmesini veya yok edilmesini isteme,",
                    "Eksik veya yanlış verilerin düzeltilmesi ile kişisel verilerinizin silinmesi veya yok edilmesini talep ettiğinizde, bu durumun kişisel verilerinizi aktardığımız üçüncü kişilere bildirilmesini isteme,",
                    "Kişisel verilerin kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız halinde bu zararın giderilmesini talep etme haklarına sahipsiniz.",
                ],
            },
            {
                "heading": "Haklarınızı Nasıl Kullanabilirsiniz?",
                "paragraphs": [
                    "Kişisel verileriniz ile ilgili başvuru ve taleplerinizi ;",
                ],
                "items": [
                    "Islak imzalı ve kimlik fotokopisi ile Konumsal Bilgi Sistemleri Üniversiteler Mah. Cyberpark Tepe Binası Zemin Kat No:19-31 Bilkent 06800 Çankaya/ANKARA adresine göndererek,",
                    "Geçerli bir kimlik belgesi ile birlikte Konumsal Bilgi Sistemleri’ne bizzat başvurarak,",
                    "Kayıtlı elektronik posta adresi ve güvenli elektronik imza ya da mobil imza kullanmak suretiyle bilgi@konumsal.com.tr kayıtlı elektronik posta adresimize göndererek,",
                    "Konumsal Bilgi Sistemleri’ne iletebilirsiniz.",
                ],
                "paragraphs_after": [
                    "Veri Sorumlusuna Başvuru Usul ve Esasları Hakkında Tebliğ uyarınca, İlgili Kişi’nin, başvurusunda isim, soy isim, başvuru yazılı ise imza, T.C. kimlik numarası, (başvuruda bulunan kişinin yabancı olması halinde pasaport numarası), tebligata esas yerleşim yeri veya iş yeri adresi, varsa bildirime esas elektronik posta adresi, telefon numarası ve faks numarası ile talep konusuna dair bilgilerin bulunması zorunludur.",
                    "İlgili Kişi, yukarıda belirtilen hakları kullanmak için yapacağı ve kullanmayı talep ettiği hakka ilişkin açıklamaları içeren başvuruda talep edilen hususu açık ve anlaşılır şekilde belirtmelidir. Başvuruya ilişkin bilgi ve belgelerin başvuruya eklenmesi gerekmektedir.",
                    "Talep konusunun başvuranın şahsı ile ilgili olması gerekmekle birlikte, başkası adına hareket ediliyor ise başvuruyu yapanın bu konuda özel olarak yetkili olması ve bu yetkinin belgelendirilmesi (özel vekâletname) gerekmektedir. Ayrıca başvurunun kimlik ve adres bilgilerini içermesi ve başvuruya kimliği doğrulayıcı belgelerin eklenmesi gerekmektedir.",
                    "Yetkisiz üçüncü kişilerin başkası adına yaptığı talepler değerlendirmeye alınmayacaktır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizin İşlenmesine İlişkin Talepleriniz Ne Kadar Sürede Cevaplanır?",
                "paragraphs": [
                    "Kişisel verilerinize ilişkin hak talepleriniz değerlendirilerek, bize ulaştığı tarihten itibaren en geç 30 gün içerisinde cevaplanır. Başvurunuzun olumsuz değerlendirilmesi halinde gerekçeli ret sebepleri ilgili başvuruda belirttiğiniz adrese elektronik posta veya posta yolu başta olmak üzere seçilen usullerinden biri ile gönderilir.",
                ],
            },
            {
                "heading": "Açık Rıza",
                "paragraphs": [
                    "Web sitemiz üzerinden tarafımıza sağlamış olduğunuz kişisel verilerinizin Kanun’a ve işbu 6698 Sayılı Kişisel Verilerin Korunması Kanunu’ne uygun bir şekilde ve belirtilen amaçlarla işlenebileceğini bilmekte, kabul etmekte ve ayrıca işbu 6698 Sayılı Kişisel Verilerin Korunması Kanunu ile Kanun kapsamında yapılması gereken aydınlatma yükümlülüğü yerine getirildiğini, Sözleşme’yi okuduğunuzu, anladığınızı, haklarınızın ve yükümlülüklerinin bilincinde olduğunuzu beyan etmektesiniz.",
                ],
            },
        ],
    },
}


LEGAL_PAGES = {
    "kalite-politikasi": {
        "title": "Kalite Politikamız",
        "blocks": [
            {
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; ISO/IEC 27001:2013 Bilgi Güvenliği Yönetim Sistemi (BGYS), ISO/IEC 9001:2015 Kalite Yönetim Sistemi (KYS) standartlarından kurulan sistemlerin ana teması",
                ],
                "items": [
                    "Müşteri memnuniyetinin artması",
                    "Pazar payının artması",
                    "Karın artması",
                    "Çalışan memnuniyetinin artması",
                    "Maliyetlerin azalması",
                    "Yüksek rekabet gücü",
                ],
            },
            {
                "paragraphs": [
                    "Kalite ve risk yönetimini güvence altına almak, kalite yönetimi süreç performansını ölçmek ve bilgi güvenliği ve müşteri memnuniyeti ile ilgili konularda üçüncü taraflarla olan ilişkilerin düzenlenmesini sağlamaktır.",
                    "Bu doğrultuda KYS Politikalarımızın amacı KYS kapsamında;",
                ],
                "items": [
                    "Kuruluşta kalite anlayışının gelişimini",
                    "Kârın, verimliliğin ve pazar payının artmasını",
                    "Etkin bir yönetimi",
                    "Maliyetin azalmasını",
                    "Çalışanların tatminini",
                    "Kuruluş içi iletişimde iyileşmeyi",
                    "Tüm faaliyetlerde geniş izleme ve kontrolü",
                    "İadelerin azalmasını",
                    "Müşteri şikayetinin azalması, memnuniyetin artmasını",
                    "Ulusal ve uluslararası düzeyde uygulanabilirliği sağlamak",
                    "Kalite Yönetim Sistemleri (KYS) kurmak ve işletmek",
                    "Kalite Güvenliği Yönetimi eğitimlerini tüm personele vererek bilinçlendirmeyi sağlamak",
                    "Kalite Yönetimi konusunda periyodik olarak değerlendirmeler yaparak mevcut riskleri tespit etmek. Değerlendirmeler sonucunda, aksiyon planlarını gözden geçirmek ve takibini yapmak",
                    "Sözleşmelerden doğabilecek her türlü anlaşmazlık ve çıkar çatışmasını engellemek",
                    "Bilgiye erişilebilirlik ve bilgi sistemleri için iş gereksinimlerini karşılamaktır",
                ],
            },
        ],
    },
    "gizlilik-sozlesmesi": {
        "title": "Gizlilik Sözleşmesi",
        "blocks": [
            {
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel bilgilerinizin gizliliğine saygı duyar. Kişisel bilgiler, 6698 sayılı Kişisel Verilerin Korunması Kanunu’na tabidir. Bu doğrultuda, internet sitesinde verdiğiniz tüm kişisel bilgiler, yalnızca size hizmet amaçlı ve Kanun’a uygun olarak kullanılmakta ve hiçbir şekilde üçüncü taraf kurum ve kuruluşlarla paylaşılmamaktadır. Konumsal Bilgi Sistemleri, internet sitesinden kişisel bilgi toplama ve kullanımını asgari düzeyde tutmakta ve toplanan kişisel bilgileri sadece işlemlerin gerçekleşebilmesi için kullanmaktadır.",
                ],
            },
        ],
    },
    "kullanim-kosullari": {
        "title": "Kullanım Koşulları",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini ziyaret etmekle veya kullanmakla, aşağıda yer alan koşulları kabul etmiş sayılırsınız. Konumsal Bilgi Sistemleri, bu sayfada yer alan koşullarda dilediği zaman önceden haber vermeksizin değişiklik yapma hakkına sahiptir.",
                ],
            },
            {
                "heading": "Fikri Mülkiyet Hakları",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesini sadece kişisel kullanımınız için ziyaret etme, görüntüleme ve internet sitesinin sayfalarını sadece kişisel kullanımınız için kopyalama hakkına ve yetkisine sahip olduğunuzu kabul etmektesiniz. Konumsal Bilgi Sistemleri internet sitesinde bulunan tüm görsel ve yazılı materyal Konumsal Bilgi Sistemleri mülkiyetindedir ve Türk ve uluslararası telif hakkı kanunlarıyla korunmaktadır. Önceden izin alınmaksızın internet sitesindeki bilgilerin ya da internet sitesine ilişkin her tür veri tabanı, yazılım, görsel materyalin ticari amaçlarla kısmen ya da tamamen kopyalanması, değiştirilmesi, yayımlanması ve dağıtımı engellenmiştir. Aksi tespit edildiği durumlarda Konumsal Bilgi Sistemleri gerekli hukuki işlemleri başlatma hakkını saklı tutar.",
                ],
            },
            {
                "heading": "Sorumluluğun Sınırlandırılması",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, internet sitesine girilmesi, internet sitesinde yayımlanan bilgilerin ve diğer verilerin kullanılması sebebiyle, sözleşmenin ihlali, haksız fiil ya da başkaca sebeplere binaen, cezai tazminatlar da dahil olmak üzere doğabilecek doğrudan ya da dolaylı hiçbir zarardan sorumlu değildir.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde yer alan bilgilerin güncel ve geçerli tutulması için azami gayreti sarf etmektedir. Konumsal Bilgi Sistemleri’nin ürünlerine ve hizmetlerine ilişkin tüm yükümlülükleri, bunların tabi oldukları sözleşmelerde belirlenmiş olup, internet sitesinde bulunan hiçbir şey söz konusu sözleşmeleri değiştiriyor olarak yorumlanamaz. Konumsal Bilgi Sistemleri; ayrıca, internet sitesindeki malzemelerin, yazılımın veya hizmetlerin doğruluğunu ve eksiksiz olduğunu garanti etmez. Konumsal Bilgi Sistemleri internet sitesindeki verilerde ve hizmetlerde veya ürünlerde ve fiyatlarında önceden bildirimde bulunmaksızın değişiklikler yapma hakkını saklı tutar.",
                    "Konumsal Bilgi Sistemleri, internet sitesinde bulunan fonksiyonların veya hizmetlerin kesintisiz ya da hatadan arınmış olacağının, sorunlu yanlarının giderileceğinin ve internet sitesinin veya bu internet sitesini erişilebilir kılan sunucunun virüslerden veya başka zararlı unsurlardan arınmış olduğunun garantisini vermemektedir. Mevzuat’ın müsaade ettiği ölçüde Konumsal Bilgi Sistemleri’nin, internet sitesinin veya herhangi bir bağlantılı hizmet veya teknik hizmetin yerine getirilmesinden veya getirilmemesinden kaynaklanan zararlardan hiçbir sorumluluğu bulunmamaktadır.",
                ],
            },
            {
                "heading": "Diğer İnternet Sitelerine Erişim",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri internet sitesi içerisinden üçüncü şahıslara ait internet sitelerine bağlantılar yerleştirebilir. Bu üçüncü şahıs internet sitelerine bağlandığınızda, ilgili internet sitesinin kullanım koşullarına tabi sayılırsınız. Konumsal Bilgi Sistemleri, bu internet sitelerinde yayımlanan içerikten veya gizlilik koşullarından ve bu internet sitelerinin kullanımından dolayı oluşabilecek doğrudan ve/veya dolaylı hiçbir zarardan hiçbir şekilde sorumlu tutulamaz.",
                ],
            },
        ],
    },
    "cerez-politikasi": {
        "title": "Kişisel Veriler ve Çerez Politikası",
        "blocks": [
            {
                "heading": "ÇEREZ (“COOKIE”) UYARISI",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri web sayfası deneyiminizi en iyi şekilde optimize etmek ve kullanıcı deneyiminizi geliştirebilmek için Cookie kullanıyoruz. Cookie kullanılmasını tercih etmezseniz tarayıcınızın ayarlarından Cookie’leri silebilir ya da engelleyebilirsiniz. Ancak bunun internet sitemizi kullanımınızı etkileyebileceğini hatırlatmak isteriz. Tarayıcınızdan Cookie ayarlarınızı değiştirmediğiniz sürece bu sitede çerez kullanımını kabul ettiğinizi varsayacağız. Toplanan verilerle ilgili bilgilere Gizlilik Politikası’mızdan ulaşabilirsiniz.",
                ],
            },
            {
                "heading": "İNTERNET SİTESİNDE KULLANILAN ÇEREZLER Çerez Nedir ve Neden Kullanılmaktadır?",
                "paragraphs": [
                    "Çerezler, ziyaret ettiğiniz internet siteleri tarafından tarayıcılar aracılığıyla cihazınıza veya ağ sunucusuna depolanan küçük metin dosyalarıdır.",
                    "İnternet Sitemizde çerez kullanılmasının başlıca amaçları aşağıda sıralanmaktadır:",
                ],
                "items": [
                    "İnternet sitesinin işlevselliğini ve performansını arttırmak yoluyla sizlere sunulan hizmetleri geliştirmek,",
                    "İnternet Sitesini iyileştirmek ve İnternet Sitesi üzerinden yeni özellikler sunmak ve sunulan özellikleri sizlerin tercihlerine göre kişiselleştirmek;",
                    "İnternet Sitesinin, sizin ve Şirketimizin hukuki ve ticari güvenliğinin teminini sağlamak.",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerez Türleri",
                "paragraphs": [
                    "Oturum Çerezleri (Session Cookies)",
                    "Oturum çerezleri ziyaretçilerimizin İnternet Sitesini ziyaretleri süresince kullanılan, tarayıcı kapatıldıktan sonra silinen geçici çerezlerdir.",
                    "Bu tür çerezlerin kullanılmasının temel amacı ziyaretiniz süresince İnternet Sitesinin düzgün bir biçimde çalışmasının teminini sağlamaktır.",
                    "Örneğin; birden fazla sayfadan oluşan çevrimiçi formları doldurmanızın sağlanmaktadır.",
                    "Kalıcı Çerezler (Persistent Cookies)",
                    "Kalıcı çerezler İnternet Sitesinin işlevselliğini artırmak, ziyaretçilerimize daha hızlı ve iyi bir hizmet sunmak amacıyla kullanılan çerez türleridir.",
                    "Bu tür çerezler tercihlerinizi hatırlamak için kullanılır ve tarayıcılar vasıtasıyla cihazınızda depolanır.",
                    "Kalıcı çerezlerin bazı türleri; İnternet Sitesini kullanım amacınız gibi hususlar göz önünde bulundurarak sizlere özel öneriler sunulması için kullanılabilmektedir.",
                    "Kalıcı çerezler sayesinde İnternet Sitemizi aynı cihazla tekrardan ziyaret etmeniz durumunda, cihazınızda İnternet Sitemiz tarafından oluşturulmuş bir çerez olup olmadığı kontrol edilir ve var ise, sizin siteyi daha önce ziyaret ettiğiniz anlaşılır ve size iletilecek içerik bu doğrultuda belirlenir ve böylelikle sizlere daha iyi bir hizmet sunulur.",
                ],
            },
            {
                "heading": "İnternet Sitemizde Kullanılan Çerezler",
                "paragraphs": [
                    "Otantikasyon Çerezleri(Authentication Cookies)",
                    "Ziyaretçiler, şifrelerini kullanarak internet sitesine giriş yapmaları durumunda, bu tür çerezler ile, ziyaretçinin internet sitesinde ziyaret ettiği her bir sayfada site kullanıcısı olduğu belirlenerek, kullanıcının her sayfada şifresini yeniden girmesi önlenir.",
                    "Analitik Çerezler (Analytical Cookies)",
                    "Analitik çerezler ile internet sitesini ziyaret edenlerin sayıları, internet sitesinde görüntülenen sayfaların tespiti, internet sitesi ziyaret saatleri, internet sitesi sayfaları kaydırma hareketleri gibi analitik sonuçların üretimini sağlayan çerezlerdir.",
                ],
            },
        ],
    },
    "kvkk-bilgilendirme": {
        "title": "KVKK Bilgilendirme Metni",
        "blocks": [
            {
                "heading": "Genel",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak; 6698 sayılı Kişisel Verilerin Korunması Kanunu (“KVKK”) ve ilgili mevzuat ve yasal düzenlemelerden kaynaklanan faaliyetleri çerçevesinde kişisel verilerinizin işlenmesi, saklanması ve aktarılmasına ilişkin siz",
                ],
                "items": [
                    "Çalışanlarımızı",
                    "Çalışan Adaylarımızı,",
                    "Stajyer Adaylarımızı,",
                    "Ziyaretçilerimizi,",
                    "Hissedar/ Ortaklarımızı,",
                    "Tedarikçilerimizi",
                    "Ürün ve hizmet alan kişileri",
                    "Potansiyel Müşterilerimizi",
                ],
            },
            {
                "paragraphs": [
                    "bilgilendirmek amacıyla işbu aydınlatma metnini hazırladık. Konumsal Bilgi Sistemleri olarak, kişisel verilerin güvenliği hususuna verdiğimiz önem doğrultusunda sizi bilgilendirmek istiyoruz.",
                    "Bünyemizde barındırdığımız her türlü kişisel veri 6698 sayılı Kişisel Verilerin Korunması Kanunu’na uygun olarak işlenmekte, saklanmakta ve aktarılmaktadır. Kişisel verilerinizin tarafımızla paylaşılması halinde, kimliğinizi belirli veya belirlenebilir kılan her türlü bilginiz, Kişisel Veri olarak aşağıdaki kapsamda, Veri Sorumlusu sıfatıyla Konumsal Bilgi Sistemleri tarafından işlenecektir. “Kişisel Verilerinizin işlenmesi” ise bu verilerin elde edilmesi, kaydedilmesi, depolanması, muhafaza edilmesi, değiştirilmesi, yeniden düzenlenmesi, açıklanması, aktarılması, devralınması, elde edilebilir hale getirilmesi, sınıflandırılması ya da kullanılmasının engellenmesi gibi veriler üzerinde gerçekleştirilen her türlü işlemi ifade etmektedir. Konumsal Bilgi Sistemleri olarak kişisel verilerinizin güvenliğine en üst düzeyde önem vererek, sizlere sunduğumuz tüm ürün ve hizmetlerimizde kişisel verilerinizin güvenliğinin ön planda olduğu bilinciyle faaliyetlerimize devam ettiğimizi belirtmek isteriz. Aşağıdaki tabloda hangi kişisel verileri tuttuğumuz belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın kimlik, iletişim, özlük, mesleki deneyim, sağlık ve adli sicil raporu bilgileri, görsel kayıtları (vesikalık fotoğraf), kapı giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri, şifre bilgileri",
                    "Çalışan Adaylarımızın kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri),",
                    "Stajyerlerimizin kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri), giriş çıkış kayıtları, internet sitesi giriş çıkış bilgileri, IP adres bilgileri, şifre bilgileri",
                    "Ziyaretçilerimizin kimlik (ad-soyad) bilgileri",
                    "Çevrimçi ziyaretçilerimizin ad/soyad, e-posta, telefon no ve işyeri bilgileri",
                    "Hissedar/ Ortaklarımızın kimlik (ad-soyad), özgeçmiş (okul, iletişim bilgileri, diploma bilgileri gibi), fatura bilgileri, bilanço bilgileri, finansal performans bilgileri",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) bilgileri",
                    "Ürün ve Hizmet Alan kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta IBAN bilgileri gibi), çağrı merkezi kayıtları",
                    "Potansiyel Müşterilerimizin kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta gibi) bilgileri tutulmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerin İşlenme Amaçları Nelerdir?",
                "paragraphs": [
                    "Kişisel verilerinizin Konumsal Bilgi Sistemleri hizmet verdiği işlemler için kullanılması, özel hayatınızın gizliliği ve temel hak ve özgürlüklerinizin korunması temel prensibimizdir. Aşağıda Konumsal Bilgi Sistemleri’nin kişisel verileri hangi amaçla işlediği belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın yukarda belirtilen kişisel verileri, Çalışanlar İçin İş Akdi ve Mevzuat Kaynaklı Yükümlülüklerin Yerine Getirilmesi, İnsan Kaynakları Süreçlerinin Planlanması, Hukuk İşlerinin Takibi Ve Yürütülmesi, Çalışan Memnuniyeti Ve Bağlılığı Süreçlerinin Yürütülmesi, Çalışanlar İçin Yan Haklar Ve Menfaatleri Süreçlerinin Yürütülmesi, Eğitim Faaliyetlerinin Yürütülmesi, Denetim / Etik Faaliyetlerinin Yürütülmesi, Mal / Hizmet Satın Alım Süreçlerinin Yürütülmesi, Ürün ve Hizmetlerin Pazarlama Süreçlerinin Yürütülmesi, Finans ve Muhasebe İşlerinin Yürütülmesi ve Bilgi Güvenliği Süreçlerinin Yürütülmesi amacıyla işlenir.",
                    "Çalışan Adaylarımızın yukarda belirtilen kişisel verileri insan kaynakları süreçlerinin planlanması ve Çalışan Adayı / Stajyer / Öğrenci Seçme Ve Yerleştirme Süreçlerinin Yürütülmesi amacıyla tutulur.",
                    "Stajyerlerimizin yukarda belirtilen kişisel verileri Çalışan Adayı / Stajyer / Öğrenci Seçme Ve Yerleştirme Süreçlerinin Yürütülmesi ve Bilgi Güvenliği Süreçlerinin Yürütülmesi amacıyla işlenir.",
                    "Ziyaretçilerimizin kimlik bilgileri (ad-soyad) Ziyaretçi Kaydı Oluşturulması ve Takibi oluşturulması amacıyla işlenir.",
                    "Hissedar/ Ortaklarımızın yukarda belirtilen kişisel verileri, Mal Hizmet Satın Alım Süreçlerinin Yürütülmesi, Ürün ve hizmetlerin pazarlama süreçlerinin yürütülmesi, Sözleşme Sürecinin yürütülmesi, Finans ve Muhasebe İşlerinin Yürütülmesi amacıyla işlenir.",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) Finans Ve Muhasebe İşlerinin Yürütülmesi amacıyla işlenir.",
                    "Ürün ve Hizmet Alan kişilerin yukarda belirtilen kişisel verileri, Sözleşme sürecinin yürütülmesi ve Müşteri Memnuniyetine Yönelik Aktivitelerin Yürütülmesi amacıyla işlenir.",
                    "Potansiyel Müşterilerimizin kişilerin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta gibi) Ürün ve Hizmetlerin pazarlama süreçlerinin yürütülmesi amacıyla işlenir.",
                    "Yukarıda sayılan amaçlar kapsamında gerçekleştirilen kişisel veri işleme faaliyetinin, KVKK kapsamında öngörülen ilgili kişinin açık rızasının varlığı dışındaki hukuka uygunluk nedenlerinden herhangi birini karşılamaması halinde, ilgili işleme sürecine yönelik olarak Konumsal Bilgi Sistemleri tarafından ilgilinin açık rızası alınmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizin Tutulma Yöntemleri ve Hukuki Sebepleri Nelerdir?",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri, kişisel verilerinizi Şirketimizle iletişime geçmeniz ve/veya hukuki ilişkinizin kurulması esnasında ve söz konusu ilişkinin devamı süresince sizlerden, ortaklıklar, grup şirketleri, iştirakler, işbirliği yaptığımız ya da sözleşme ilişkimizin bulunduğu çözüm ortakları, dâhil olmak üzere üçüncü kişilerden ve yasal mercilerden olmak kaydıyla çağrı merkezi, internet, mobil uygulamalar, sosyal medya ve diğer kamuya açık mecralar veya düzenlenen eğitimler, organizasyonlar ve benzeri etkinlikler aracılığıyla yukarıda yer verilen amaç ve hizmetlerin Kanun’un 5, 6 ve 8. madde hükümlerinde öngörülen çerçevede verilebilmesi amacı ile toplanmaktadır. Kişisel verilerinizin tutulma nedenlerinin hukuki sebepleri ayrıntılı olarak aşağıda belirtilmiştir.",
                ],
                "items": [
                    "Çalışanlarımızın yukarda belirtilen kişisel verileri, çalışanlarla sözleşme imzalanması ve veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır.",
                    "Çalışan Adaylarımızın yukarda belirtilen kişisel verileri, veri sorumlusunun meşru menfaatleri ve kanunlarda öngörülmesi amacıyla toplanmaktadır .",
                    "Stajyerlerimizin yukarda belirtilen kişisel verileri veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır .",
                    "Ziyaretçilerimizin kimlik (ad-soyad) hukuki yükümlülüğün yerine getirilmesi amacıyla toplanır.",
                    "Hissedar/ Ortaklarımızın yukarda belirtilen kişisel verileri hukuki yükümlülüğün yerine getirilmesi amacıyla toplanmaktadır.",
                    "Tedarikçilerimizin kimlik (ad-soyad), iletişim (adres, telefon no, e-posta, IBAN bilgileri gibi) veri sorumlusunun meşru menfaatleri amacıyla toplanmaktadır.",
                    "Ürün ve Hizmet Alan kişilerin yukarda belirtilen kişisel verileri, müşterilerimizle sözleşme imzalanması ve veri sorumlusu olarak firmamızın meşru menfaatleri doğrultusunda toplanmaktadır.",
                    "Potansiyel Müşterilerimizin yukarda belirtilen kişisel veriler, veri sorumlusu olarak firmamızın meşru menfaatleri doğrultusunda toplanmaktadır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizi Üçüncü Bir Kişiye Aktarıyor Muyuz?",
                "paragraphs": [
                    "Kişisel verileriniz,",
                ],
                "items": [
                    "Yasal düzenlemenin öngördüğü kapsamda, faaliyetlerin mevzuata uygun yürütülmesi, hukuk işlerinin takibi ve yürütülmesi, yetkili kişi, kurum ve kuruluşlara bilgi verilmesi, çalışanlar için iş akdi ve mevzuattan kaynaklı yükümlülüklerin yerine getirilmesi, iş faaliyetlerinin yürütülmesi/denetimi ve iş sağlığı/güvenliği faaliyetlerinin yürütülmesi amaçlarıyla yurt içindeki Yetkili Kamu Kurum ve Kuruluşlarına, ve",
                    "Yasal düzenlemenin öngördüğü kapsamda, faaliyetlerin mevzuata uygun yürütülmesi ve yetkili kişi, kurum ve kuruluşlara bilgi verilmesi amaçlarıyla yurt içindeki Gerçek Kişiler veya Özel Hukuk Tüzel Kişileri ’ne aktarılabilecektir.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizi Yurt Dışına Aktarıyor Muyuz?",
                "paragraphs": [
                    "Konumsal Bilgi Sistemleri olarak, kişisel verilerinizi yurt dışına aktarmamaktayız.",
                ],
            },
            {
                "heading": "Kişisel Verileriniz Ne Kadar Süre ile Saklanır?",
                "paragraphs": [
                    "Kişisel verilerinizin saklama süresi aşağıdaki şekildedir:",
                ],
                "items": [
                    "Kanunda veya ilgili mevzuatta verinin saklanması için bir süre belirlenmişse söz konusu veri en az bu süre kadar saklanmak zorundadır. Olası bir mahkeme talebinin veya kanunla yetkili kılınmış bir idari merciinin ilgili veriye ilişkin talebinin tarafımıza geç ulaşması veya tarafı olabileceğimiz bir ihtilafın meydana gelmesi gibi ihtimaller gözetilmek suretiyle, verilerinizin saklanması için mevzuatta öngörülen sürelere 6 ay ila 1 yıl arası bir süre eklenerek verilerin saklama süresi belirlenmekte ve belirlenen sürenin sonunda söz konusu veriler silinmektedir.",
                    "Saklama süresi mevzuatta belirlenmiş verilerinizin öngörülen sürelerden önce silinmesini talep etmeniz halinde söz konusu talebiniz gerçekleştirilemeyecektir.",
                    "Saklama süresine ilişkin mevzuatta bir süre öngörülmeyen ve işleme amacı olmayan verileriniz silinmesine dair talepte bulunmanız halinde ise derhal veya en geç 6 ay içerisinde silinir.",
                ],
            },
            {
                "heading": "Kişisel Verileriniz İle İlgili Olarak Kullanabileceğiniz Haklarınız Nelerdir?",
                "paragraphs": [
                    "Kişisel verilerinize ilişkin;",
                ],
                "items": [
                    "Kişisel verilerinizin işlenip işlenmediğini öğrenme,",
                    "Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme,",
                    "Kişisel verilerin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme,",
                    "Yurt içinde veya yurt dışında kişisel verilerinizin aktarıldığı üçüncü kişileri bilme,",
                    "Kişisel verilerinizin eksik veya yanlış işlenmiş olması halinde bunların düzeltilmesini isteme,",
                    "KVKK mevzuatında öngörülen şartlar çerçevesinde kişisel verilerinizin silinmesini veya yok edilmesini isteme,",
                    "Eksik veya yanlış verilerin düzeltilmesi ile kişisel verilerinizin silinmesi veya yok edilmesini talep ettiğinizde, bu durumun kişisel verilerinizi aktardığımız üçüncü kişilere bildirilmesini isteme,",
                    "Kişisel verilerin kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız halinde bu zararın giderilmesini talep etme haklarına sahipsiniz.",
                ],
            },
            {
                "heading": "Haklarınızı Nasıl Kullanabilirsiniz?",
                "paragraphs": [
                    "Kişisel verileriniz ile ilgili başvuru ve taleplerinizi ;",
                ],
                "items": [
                    "Islak imzalı ve kimlik fotokopisi ile Konumsal Bilgi Sistemleri Üniversiteler Mah. Cyberpark Tepe Binası Zemin Kat No:19-31 Bilkent 06800 Çankaya/ANKARA adresine göndererek,",
                    "Geçerli bir kimlik belgesi ile birlikte Konumsal Bilgi Sistemleri’ne bizzat başvurarak,",
                    "Kayıtlı elektronik posta adresi ve güvenli elektronik imza ya da mobil imza kullanmak suretiyle bilgi@konumsal.com.tr kayıtlı elektronik posta adresimize göndererek,",
                    "Konumsal Bilgi Sistemleri’ne iletebilirsiniz.",
                ],
                "paragraphs_after": [
                    "Veri Sorumlusuna Başvuru Usul ve Esasları Hakkında Tebliğ uyarınca, İlgili Kişi’nin, başvurusunda isim, soy isim, başvuru yazılı ise imza, T.C. kimlik numarası, (başvuruda bulunan kişinin yabancı olması halinde pasaport numarası), tebligata esas yerleşim yeri veya iş yeri adresi, varsa bildirime esas elektronik posta adresi, telefon numarası ve faks numarası ile talep konusuna dair bilgilerin bulunması zorunludur.",
                    "İlgili Kişi, yukarıda belirtilen hakları kullanmak için yapacağı ve kullanmayı talep ettiği hakka ilişkin açıklamaları içeren başvuruda talep edilen hususu açık ve anlaşılır şekilde belirtmelidir. Başvuruya ilişkin bilgi ve belgelerin başvuruya eklenmesi gerekmektedir.",
                    "Talep konusunun başvuranın şahsı ile ilgili olması gerekmekle birlikte, başkası adına hareket ediliyor ise başvuruyu yapanın bu konuda özel olarak yetkili olması ve bu yetkinin belgelendirilmesi (özel vekâletname) gerekmektedir. Ayrıca başvurunun kimlik ve adres bilgilerini içermesi ve başvuruya kimliği doğrulayıcı belgelerin eklenmesi gerekmektedir.",
                    "Yetkisiz üçüncü kişilerin başkası adına yaptığı talepler değerlendirmeye alınmayacaktır.",
                ],
            },
            {
                "heading": "Kişisel Verilerinizin İşlenmesine İlişkin Talepleriniz Ne Kadar Sürede Cevaplanır?",
                "paragraphs": [
                    "Kişisel verilerinize ilişkin hak talepleriniz değerlendirilerek, bize ulaştığı tarihten itibaren en geç 30 gün içerisinde cevaplanır. Başvurunuzun olumsuz değerlendirilmesi halinde gerekçeli ret sebepleri ilgili başvuruda belirttiğiniz adrese elektronik posta veya posta yolu başta olmak üzere seçilen usullerinden biri ile gönderilir.",
                ],
            },
            {
                "heading": "Açık Rıza",
                "paragraphs": [
                    "Web sitemiz üzerinden tarafımıza sağlamış olduğunuz kişisel verilerinizin Kanun’a ve işbu 6698 Sayılı Kişisel Verilerin Korunması Kanunu’ne uygun bir şekilde ve belirtilen amaçlarla işlenebileceğini bilmekte, kabul etmekte ve ayrıca işbu 6698 Sayılı Kişisel Verilerin Korunması Kanunu ile Kanun kapsamında yapılması gereken aydınlatma yükümlülüğü yerine getirildiğini, Sözleşme’yi okuduğunuzu, anladığınızı, haklarınızın ve yükümlülüklerinin bilincinde olduğunuzu beyan etmektesiniz.",
                ],
            },
        ],
    },
}


def legal_page(request, slug):
    page = LEGAL_PAGES.get(slug)
    if not page:
        return custom_404(request, None)
    return render(request, "website/legal_page.html", {"page": page})


def custom_404(request, exception):
    logger.warning("404 page hit", extra={"path": request.path})
    return render(request, "404.html", status=404)


def custom_500(request):
    logger.exception("500 page rendered")
    return render(request, "500.html", status=500)
