from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AboutPage,
    ContactInfo,
    HomeServiceCard,
    HomeSlide,
    ManagedPage,
    ManagedPageSection,
    Project,
    Service,
)


admin.site.site_header = "Konumsal Bilgi Sistemleri"
admin.site.site_title = "Konumsal Bilgi Sistemleri"
admin.site.index_title = "Hızlı Yönetim Paneli"


class PublishAdminMixin:
    actions = ["make_active", "make_passive"]

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} kayıt yayına alındı.")

    make_active.short_description = "Seçili kayıtları yayına al"

    def make_passive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} kayıt yayından kaldırıldı.")

    make_passive.short_description = "Seçili kayıtları yayından kaldır"


def image_preview(obj):
    image = getattr(obj, "image", None)
    if image:
        return format_html('<img src="{}" style="height:46px;width:78px;object-fit:cover;border-radius:6px;" />', image.url)
    return "-"


image_preview.short_description = "Görsel"


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("title", "last_updated")
    readonly_fields = ("last_updated",)
    fieldsets = (
        ("Sayfa Başlığı", {"fields": ("title", "hero_title", "hero_subtitle")}),
        ("İçerik", {"fields": ("content",)}),
        ("Sistem", {"fields": ("last_updated",)}),
    )


@admin.register(HomeSlide)
class HomeSlideAdmin(PublishAdminMixin, admin.ModelAdmin):
    list_display = ("order", "title", image_preview, "button_text", "is_active", "updated_at")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "button_url")
    readonly_fields = ("updated_at", image_preview)
    fieldsets = (
        ("Slider İçeriği", {"fields": ("title", "subtitle", "image", image_preview)}),
        ("Butonlar", {"fields": ("button_text", "button_url", "second_button_text", "second_button_url")}),
        ("Yayın Ayarı", {"fields": ("order", "is_active", "updated_at")}),
    )


@admin.register(HomeServiceCard)
class HomeServiceCardAdmin(PublishAdminMixin, admin.ModelAdmin):
    list_display = ("order", "title", image_preview, "link_url", "is_active", "updated_at")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description", "link_url")
    readonly_fields = ("updated_at", image_preview)
    fieldsets = (
        ("Kart İçeriği", {"fields": ("title", "description", "image", image_preview, "link_url")}),
        ("Yayın Ayarı", {"fields": ("order", "is_active", "updated_at")}),
    )


class ManagedPageSectionInline(admin.StackedInline):
    model = ManagedPageSection
    extra = 1
    fields = ("title", "content", "image", "button_text", "button_url", "order", "is_active")


@admin.register(ManagedPage)
class ManagedPageAdmin(PublishAdminMixin, admin.ModelAdmin):
    list_display = ("order", "title", "page_type", "path", "is_active", "updated_at")
    list_display_links = ("title",)
    list_editable = ("order", "is_active")
    list_filter = ("page_type", "is_active")
    search_fields = ("title", "slug", "path", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("updated_at", image_preview)
    inlines = (ManagedPageSectionInline,)
    fieldsets = (
        ("Sayfa Kimliği", {"fields": ("title", "slug", "path", "page_type", "is_active")}),
        ("Üst Alan", {"fields": ("eyebrow", "summary", "hero_image", image_preview)}),
        ("İçerik", {"fields": ("body",)}),
        ("Buton", {"fields": ("primary_button_text", "primary_button_url")}),
        ("Sistem", {"fields": ("order", "updated_at")}),
    )


@admin.register(Service)
class ServiceAdmin(PublishAdminMixin, admin.ModelAdmin):
    list_display = ("order", "title", image_preview, "detail_url", "is_active")
    list_display_links = ("title",)
    list_editable = ("is_active", "order")
    search_fields = ("title", "short_description")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (image_preview,)
    fieldsets = (
        ("Hizmet Bilgisi", {"fields": ("title", "slug", "short_description", "description")}),
        ("Kart ve Link", {"fields": ("image", image_preview, "detail_url")}),
        ("Yayın Ayarı", {"fields": ("order", "is_active")}),
    )


@admin.register(Project)
class ProjectAdmin(PublishAdminMixin, admin.ModelAdmin):
    list_display = ("order", "title", "client", image_preview, "is_active", "is_featured")
    list_display_links = ("title",)
    list_editable = ("is_active", "is_featured", "order")
    search_fields = ("title", "client", "summary")
    list_filter = ("is_active", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (image_preview,)
    fieldsets = (
        ("Proje Bilgisi", {"fields": ("title", "slug", "client", "summary", "description")}),
        ("Kart ve Link", {"fields": ("image", image_preview, "detail_url")}),
        ("Tarih", {"fields": ("start_date", "end_date")}),
        ("Yayın Ayarı", {"fields": ("order", "is_active", "is_featured")}),
    )


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ("company_name", "phone", "email", "updated_at")
    readonly_fields = ("updated_at",)
