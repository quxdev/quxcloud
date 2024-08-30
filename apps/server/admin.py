from django.contrib import admin
from .models import (
    AnsiblePlay,
    GitHubRepository,
    EC2Instance,
    DjangoService,
    DjangoProject,
)


@admin.register(AnsiblePlay)
class AnsiblePlayAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "enabled", "yml_file")
    list_filter = ("enabled",)
    search_fields = ("name", "description")
    ordering = ("order",)


@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "repo_owner", "template_owner", "created_at", "updated_at")
    search_fields = ("name", "repo_owner", "template_owner")
    list_filter = ("repo_owner", "template_owner")
    ordering = ("-created_at",)


@admin.register(EC2Instance)
class EC2InstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "instance_type", "ami_source", "server_admin", "created_at")
    search_fields = ("name", "ami_source", "server_admin")
    list_filter = ("instance_type", "ami_source", "created_at")
    ordering = ("-created_at",)


@admin.register(DjangoService)
class DjangoServiceAdmin(admin.ModelAdmin):
    list_display = ("service", "domain", "hostname", "python_version")
    search_fields = ("service", "domain", "hostname", "django_project")
    list_filter = ("python_version",)
    ordering = ("service",)


@admin.register(DjangoProject)
class DjangoProjectAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "environment",
        "ec2_instance",
        "git_repo",
        "aws_region",
        "public_ip_address",
    )
    search_fields = (
        "environment",
        "aws_region",
        "public_ip_address",
        "public_dns_name",
    )
    list_filter = ("environment", "aws_region")
    ordering = ("service", "environment")


# Optionally, you can customize the admin site title and header
admin.site.site_header = "Project Administration"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Admin Portal"
