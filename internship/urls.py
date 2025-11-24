from django.urls import path
from . import views, api

app_name = "internship"

urlpatterns = [
    # 3.1 Başvuru ekranı
    path("basvuru/", views.application_create_view, name="application_create"),

    # 3.2 Talep sorgulama
    path("sorgu/", views.application_query_view, name="application_query"),

    # 3.3 Günlük & review (basic HTML for now)
    path("gunluk/ekle/", views.intern_log_create_view, name="log_create"),
    path("gunluklarim/", views.intern_log_list_view, name="log_list"),

    # 4.x Yönetim paneli (basic)
    path("panel/login/", views.panel_login_view, name="panel_login"),
    path("panel/", views.dashboard_view, name="dashboard"),
    path("panel/basvurular/", views.application_list_view, name="application_list"),

    # API endpointleri
    path("api/apply/", api.apply_api_view, name="api_apply"),  # POST /staj/api/apply/
    path(
        "api/requests/<str:tc_kimlik>/<str:phone>/",
        api.application_detail_api_view,
        name="api_request_detail",
    ),
    path("api/logs/", api.log_create_api_view, name="api_logs"),          # POST
    path("api/reviews/", api.review_create_api_view, name="api_reviews"), # POST
    path("api/login/", api.jwt_login_view, name="api_login"),             # JWT login

    
]
# internship/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("panel/basvurular/", views.panel_applications, name="panel_applications"),
    path("panel/basvurular/<int:pk>/onayla/", views.panel_application_approve, name="panel_application_approve"),
    path("panel/basvurular/<int:pk>/reddet/", views.panel_application_reject, name="panel_application_reject"),
    path("panel/gunluklerim/", views.intern_log_create, name="intern_logs"),
     path("panel/gunlukler/", views.panel_logs_list, name="panel_logs_list"),
    path("panel/gunlukler/<int:pk>/degerlendir/", views.panel_log_review, name="panel_log_review"),
    
]

# internship/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import api

urlpatterns = [
    path(
        "giris/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html",   # aynı login sayfasını kullanıyoruz
            redirect_authenticated_user=True
        ),
        name="stajyer_login",
    ),

    # Stajyer başvuru
    path("basvuru/", views.intern_apply, name="intern_apply"),

    # Başvuru sorgulama
    path(
        "basvuru-sorgu/",
        views.intern_application_query,
        name="intern_query",
    ),

    # Günlük girişi
    path(
        "gunluk/",
        views.intern_daily_log,
        name="intern_daily_log",
    ),
]

urlpatterns += [
    path("api/apply/", api.apply_api, name="api_apply"),
    path("api/requests/<str:tc_no>/<str:phone>/", api.requests_api, name="api_requests"),
]