from django.urls import path
from . import views, api

app_name = "internship"

urlpatterns = [
    # STAJ PORTALI ANA SAYFA (/staj/)
    path("", views.intern_portal, name="intern_portal"),

    # Başvuru
    path("basvuru/", views.intern_apply, name="intern_apply"),
    path("basvuru-sorgu/", views.intern_application_query, name="intern_query"),

    # Günlük (stajyer form ekranı - public veya login'e bağlı senin view'a göre)
    path("gunluk/", views.intern_daily_log, name="intern_daily_log"),

    # =========================
    # STAJYER PANELİ (login zorunlu)
    # =========================
    path("stajyer/panel/", views.intern_dashboard_view, name="intern_dashboard"),
    path("stajyer/basvuru/", views.intern_application_detail_view, name="intern_application_detail"),
    path("stajyer/gunlukler/", views.intern_daily_logs_view, name="intern_daily_logs"),
    path("stajyer/belgeler/", views.intern_documents_view, name="intern_documents"),
    path("stajyer/mesajlar/", views.intern_conversation_view, name="intern_conversation"),

    # =========================
    # PERSONEL PANELİ (login zorunlu)
    # =========================
    path("panel/basvurular/", views.panel_applications, name="panel_applications"),
    path("panel/basvurular/<int:pk>/onayla/", views.panel_application_approve, name="panel_application_approve"),
    path("panel/basvurular/<int:pk>/reddet/", views.panel_application_reject, name="panel_application_reject"),

    path("panel/gunlukler/", views.panel_logs_list, name="panel_logs_list"),
    path("panel/gunlukler/<int:pk>/degerlendir/", views.panel_log_review, name="panel_log_review"),
    path("panel/eslesme/<int:pk>/mesajlar/", views.panel_conversation, name="panel_conversation"),

    # Eğer stajyer "günlük ekle" ekranın login'e bağlıysa bunu panel altına koy
    path("panel/gunluk-ekle/", views.intern_log_create, name="intern_logs"),

    # =========================
    # API
    # =========================
    path("api/apply/", api.apply_api, name="api_apply"),
    path("api/requests/<str:tc_no>/<str:phone>/", api.requests_api, name="api_requests"),
]
