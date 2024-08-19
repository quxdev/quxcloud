from django.contrib import admin
from .models import Resource, Application, Permission, ApplicationPermission


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "logical_name", "resource_type", "environment", "region")
    search_fields = ("name", "logical_name", "resource_type", "environment", "region")
    list_filter = ("resource_type", "environment", "region")
    ordering = ("resource_type", "name")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("repo_name", "known_as", "url")
    search_fields = ("repo_name", "known_as")
    list_filter = ("repo_name",)
    ordering = ("repo_name",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("permission",)
    search_fields = ("permission",)
    list_filter = ("permission",)
    ordering = ("permission",)


@admin.register(ApplicationPermission)
class ApplicationPermissionAdmin(admin.ModelAdmin):
    list_display = ("application", "resource", "permission")
    search_fields = (
        "application__repo_name",
        "resource__name",
        "permission__permission",
        "resource__environment",
    )
    list_filter = ("application", "resource", "permission")
    ordering = ("application", "resource", "permission")
