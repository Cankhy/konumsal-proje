from django.contrib import admin
from django.urls import path
from website import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('hakkimizda/', views.hakkimizda, name='hakkimizda'),
    path('hizmetler/', views.hizmetler, name='hizmetler'),

    # --- HİZMET DETAY SAYFALARI ---
    path('hizmetler/cografi-bilgi-sistemleri/', views.hizmet_cbs, name='hizmet_cbs'),
    path('hizmetler/kurumsal-kaynak-planlama/', views.hizmet_erp, name='hizmet_erp'),
    path('hizmetler/siber-guvenlik-sistemleri/', views.hizmet_siber, name='hizmet_siber'),
    path('hizmetler/universite-yonetim-sistemi/', views.hizmet_universite, name='hizmet_universite'),
    path('hizmetler/insan-kaynaklari-yonetim-sistemi/', views.hizmet_ik, name='hizmet_ik'),
    path('hizmetler/veri-sayisallastirma/', views.hizmet_veri, name='hizmet_veri'),
    path('hizmetler/mobil-uygulamalar/', views.hizmet_mobil, name='hizmet_mobil'),
    path('hizmetler/elektronik-dokuman-yonetim-sistemi/', views.hizmet_edys, name='hizmet_edys'),
    path('hizmetler/gorev-yonetim-sistemi/', views.hizmet_gorev, name='hizmet_gorev'),

    # --- DİĞER SAYFALAR ---
    path('projeler/', views.projeler, name='projeler'),
    path('iletisim/', views.iletisim, name='iletisim'),

    path('projeler/orman-bilgi-sistemi/', views.proje_orman, name='proje_orman'),
    path('projeler/milli-emlak-otomasyon-sistemi/', views.proje_meop, name='proje_meop'),
    path('projeler/hava-emisyon-yonetim-hey-portali/', views.proje_hey, name='proje_hey'),
]
