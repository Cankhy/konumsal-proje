from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('hakkimizda/', views.hakkimizda, name='hakkimizda'),
    path('hizmetler/cografi-bilgi-sistemleri/', views.hizmet_cbs, name='hizmet_cbs'),
    path('hizmetler/kurumsal-kaynak-planlama/', views.hizmet_erp, name='hizmet_erp'),
    path('hizmetler/siber-guvenlik-sistemleri/', views.hizmet_siber, name='hizmet_siber'),
    path('hizmetler/universite-yonetim-sistemi/', views.hizmet_universite, name='hizmet_universite'),
    path('hizmetler/veri-sayisallastirma/', views.hizmet_veri, name='hizmet_veri'),
    path('hizmetler/mobil-uygulamalar/', views.hizmet_mobil, name='hizmet_mobil'),
    path('hizmetler/elektronik-dokuman-yonetim-sistemi/', views.hizmet_edys, name='hizmet_edys'),
    path('hizmetler/gorev-yonetim-sistemi/', views.hizmet_gorev, name='hizmet_gorev'),
    path('projeler/', views.projeler, name='projeler'),
    path('blog/', views.blog, name='blog'),
    path('iletisim/', views.iletisim, name='iletisim'),
    path('projeler/orman-bilgi-sistemi/', views.proje_orman, name='proje_orman'),
    path('projeler/milli-emlak-otomasyon-sistemi/', views.proje_meop, name='proje_meop'),
    path('projeler/hava-emisyon-yonetim-hey-portali/', views.proje_hey, name='proje_hey'),
    path("admin/", admin.site.urls),
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
    path('staj/', include('internship.urls')),

    path('login/', auth_views.LoginView.as_view(
        template_name='website/auth/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),

    # Giriş
    path("giris/", auth_views.LoginView.as_view(
        template_name="website/login.html"
    ), name="login"),

    # Çıkış
    path("cikis/", auth_views.LogoutView.as_view(
        next_page="home"   # anasayfa url name'in neyse onu yaz
    ), name="logout"),
    
]
