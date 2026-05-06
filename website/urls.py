from django.urls import path
from . import views

app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("hakkimizda/", views.hakkimizda, name="hakkimizda"),
    path("hizmetler/", views.hizmetler, name="hizmetler"),
    path("iletisim/", views.iletisim, name="iletisim"),
    path("projeler/", views.projeler, name="projeler"),

    path("hizmetler/cografi-bilgi-sistemleri/", views.hizmet_cbs, name="hizmet_cbs"),
    path("hizmetler/kurumsal-kaynak-planlama/", views.hizmet_erp, name="hizmet_erp"),
    path("hizmetler/siber-guvenlik-sistemleri/", views.hizmet_siber, name="hizmet_siber"),
    path("hizmetler/universite-yonetim-sistemi/", views.hizmet_universite, name="hizmet_universite"),
    path("hizmetler/veri-sayisallastirma/", views.hizmet_veri, name="hizmet_veri"),
    path("hizmetler/mobil-uygulamalar/", views.hizmet_mobil, name="hizmet_mobil"),
    path("hizmetler/elektronik-dokuman-yonetim-sistemi/", views.hizmet_edys, name="hizmet_edys"),
    path("hizmetler/gorev-yonetim-sistemi/", views.hizmet_gorev, name="hizmet_gorev"),
    path("hizmetler/acik-kaynak-teknolojileri-laboratuvari/", views.hizmet_aktl, name="hizmet_aktl"),
    path("hizmetler/cografi-veri-servis-yonetim-sistemi-mapgate/", views.hizmet_mapgate, name="hizmet_mapgate"),

    path("projeler/orman-bilgi-sistemi/", views.proje_orman, name="proje_orman"),
    path("projeler/milli-emlak-otomasyon-sistemi/", views.proje_meop, name="proje_meop"),
    path("projeler/hava-emisyon-yonetim-hey-portali/", views.proje_hey, name="proje_hey"),

    path("giris-sec/", views.login_select, name="login_select"),
    path("yonetim-giris-kbs/", views.admin_secret_login, name="admin_secret_login"),
    path("personel/", views.personnel_home, name="personnel_home"),
    path("stajyer-giris/", views.intern_login_view, name="intern_login"),
    path("stajyer/sifre-degistir/", views.InternPasswordChangeView.as_view(), name="intern_password_change"),
    path("stajyer/sifre-degistir/basarili/", views.intern_password_change_done, name="intern_password_change_done"),
]
