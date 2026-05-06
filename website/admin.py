from django.contrib import admin
from .models import AboutPage, Service, Project, ContactInfo


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("title", "last_updated")
    readonly_fields = ("last_updated",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("title", "short_description")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "is_active", "is_featured", "order")
    list_editable = ("is_active", "is_featured", "order")
    search_fields = ("title", "client", "summary")
    list_filter = ("is_active", "is_featured")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ("company_name", "phone", "email", "updated_at")
    readonly_fields = ("updated_at",)
