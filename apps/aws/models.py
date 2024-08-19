import os
import json
from django.conf import settings
from django.db import models

from qux.models import QuxModel


# Define a mapping of permissions to AWS actions based on resource types
PERMISSION_ACTIONS_MAP = {
    "s3": {
        "read": ["s3:GetObject", "s3:ListBucket"],
        "write": ["s3:PutObject", "s3:DeleteObject"],
    },
    "sns": {
        "send": ["sns:Publish"],
    },
    "iam": {
        "iamrolepass": ["iam:PassRole"],
    },
    # Add more resource types and permissions as needed
}


class Resource(QuxModel):
    ENVIRONMENT_CHOICES = [
        ("dev", "Development"),
        ("prod", "Production"),
        ("stage", "Staging"),
    ]

    SLUG_PREFIX = "aws"
    slug = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255)
    logical_name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True)
    environment = models.CharField(max_length=100, choices=ENVIRONMENT_CHOICES)

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        unique_together = ("name", "logical_name", "resource_type", "environment")

    def __str__(self):
        return f"{self.resource_type}: {self.name}-({self.logical_name}-{self.environment})"


class Application(QuxModel):
    SLUG_PREFIX = "aws"
    slug = models.CharField(max_length=16, unique=True)
    repo_name = models.CharField(max_length=255, unique=True)
    known_as = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=200)

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return f"{self.known_as}: ({self.repo_name})"

    def generate_role(self, environment):
        """
        Generate a role with permissions for the application in the given environment.

        Args:
            environment (str): The environment (e.g., 'dev', 'prod', 'stage').

        Returns:
            str: Path to the JSON file containing the role with permissions.
        """
        # Generate role name
        role_name = f"E9_{self.repo_name}_{environment}"

        # Fetch application permissions for the given environment
        app_permissions = ApplicationPermission.objects.filter(
            application=self, resource__environment=environment
        )

        # Create permissions structure
        permissions = []
        for app_permission in app_permissions:
            resource_type = app_permission.resource.resource_type.lower()
            permission = app_permission.permission.permission.lower()

            # Get the AWS actions based on the resource type and permission
            actions = PERMISSION_ACTIONS_MAP.get(resource_type, {}).get(permission, [])

            if not actions:
                print(
                    f"Warning: No actions found for resource type '{resource_type}'"
                    f"with permission '{permission}'."
                )
                continue

            resource_arn = app_permission.resource.name

            permission_entry = {
                "Effect": "Allow",
                "Action": actions,
                "Resource": resource_arn,
            }
            permissions.append(permission_entry)

        if not permissions:
            raise ValueError(
                f"No valid permissions generated for {self.repo_name} in {environment}."
            )

        # Role structure with inline policy
        role_data = {
            "RoleName": role_name,
            "InlinePolicy": {
                "PolicyName": f"{role_name}_policy",
                "Permissions": permissions,
            },
        }

        # Save to JSON file
        roles_dir = os.path.join(settings.DATA_DIR, "roles")
        os.makedirs(roles_dir, exist_ok=True)
        json_file_path = os.path.join(roles_dir, f"{role_name}.json")
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(role_data, json_file, indent=4)

        print(f"Role with permissions saved to {json_file_path}")
        return json_file_path


class Permission(QuxModel):
    SLUG_PREFIX = "aws"
    slug = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return f"{self.name}"


class ApplicationPermission(QuxModel):
    SLUG_PREFIX = "aws"
    slug = models.CharField(max_length=16, unique=True)
    application = models.ForeignKey("Application", on_delete=models.DO_NOTHING)
    resource = models.ForeignKey("Resource", on_delete=models.DO_NOTHING)
    permission = models.ForeignKey("Permission", on_delete=models.DO_NOTHING)

    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Application Permission"
        verbose_name_plural = "Application Permissions"
        unique_together = ("application", "resource", "permission")

    def __str__(self):
        return f"{self.application} - {self.resource} - {self.permission}"
