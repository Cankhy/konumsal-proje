from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from website import views as website_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Website app
    path("", include(("website.urls", "website"), namespace="website")),

    # Login / logout
    path("giris/personel/", auth_views.LoginView.as_view(template_name="auth/staff_login.html"), name="staff_login"),
    path("cikis/", auth_views.LogoutView.as_view(next_page="website:home"), name="logout"),

    # Internship app
    path("staj/", include(("internship.urls", "internship"), namespace="internship")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
