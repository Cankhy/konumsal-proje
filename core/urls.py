from django.contrib import admin
from django.urls import path, include
from website import views as website_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Ana site sayfaları
    path("", website_views.home, name="home"),
    path("hakkimizda/", website_views.hakkimizda, name="hakkimizda"),
    path("hizmetler/", website_views.hizmetler, name="hizmetler"),
    path("projeler/", website_views.projeler, name="projeler"),
    path("iletisim/", website_views.iletisim, name="iletisim"),

    # Hizmet detay sayfaları
    path("hizmetler/cografi-bilgi-sistemleri/", website_views.hizmet_cbs, name="hizmet_cbs"),
    path("hizmetler/kurumsal-kaynak-planlama/", website_views.hizmet_erp, name="hizmet_erp"),
    path("hizmetler/siber-guvenlik-sistemleri/", website_views.hizmet_siber, name="hizmet_siber"),
    path("hizmetler/universite-yonetim-sistemi/", website_views.hizmet_universite, name="hizmet_universite"),
    path("hizmetler/veri-sayisallastirma/", website_views.hizmet_veri, name="hizmet_veri"),
    path("hizmetler/mobil-uygulamalar/", website_views.hizmet_mobil, name="hizmet_mobil"),
    path("hizmetler/elektronik-dokuman-yonetim-sistemi/", website_views.hizmet_edys, name="hizmet_edys"),
    path("hizmetler/gorev-yonetim-sistemi/", website_views.hizmet_gorev, name="hizmet_gorev"),

    # Proje detayları
    path("projeler/orman-bilgi-sistemi/", website_views.proje_orman, name="proje_orman"),
    path("projeler/milli-emlak-otomasyon-sistemi/", website_views.proje_meop, name="proje_meop"),
    path("projeler/hava-emisyon-yonetim-hey-portali/", website_views.proje_hey, name="proje_hey"),

    # 🔐 GİRİŞ / ÇIKIŞ
    # 1) Giriş seçimi
    path("giris/", website_views.login_select, name="login_select"),

    # 2) Personel girişi (admin / staff)
    path(
        "giris/personel/",
        auth_views.LoginView.as_view(
            template_name="auth/staff_login.html",
            redirect_authenticated_user=True,
        ),
        name="staff_login",
    ),

    # 3) Stajyer girişi
    path(
        "giris/stajyer/",
        auth_views.LoginView.as_view(
            template_name="auth/intern_login.html",
            redirect_authenticated_user=True,
        ),
        name="intern_login",
    ),

    # Çıkış (şimdilik sadece URL, butonunu sonra nereye koyacağımıza karar veririz)
    path(
        "cikis/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),

    # Staj modülü
    path("staj/", include("internship.urls")),
]
