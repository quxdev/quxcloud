import os
import json
import boto3
import time
from django.conf import settings
from django.db import models

from qux.models import QuxModel


# Define a mapping of permissions to AWS actions based on resource types
PERMISSION_ACTIONS_MAP = {
    "s3": {
        "read": ["s3:GetObject", "s3:ListBucket"],
        "write": ["s3:PutObject", "s3:DeleteObject", "s3:GetObject", "s3:ListBucket"],
    },
    "ses": {
        "send": ["ses:SendEmail", "ses:SendRawEmail", "ses:SendTemplatedEmail"],
    },
    "iam": {
        "passrole": ["iam:PassRole"],
    },
    "lambda": {
        "all": [
            "lambda:CreateFunction",
            "lambda:UpdateFunctionCode",
            "lambda:UpdateFunctionConfiguration",
            "lambda:DeleteFunction",
            "lambda:GetFunction",
            "lambda:ListFunctions",
            "lambda:InvokeFunction",
        ],
    },
    "cloudformation": {
        "all": [
            "cloudformation:CreateStack",
            "cloudformation:UpdateStack",
            "cloudformation:DeleteStack",
            "cloudformation:DescribeStacks",
            "cloudformation:GetTemplate",
            "cloudformation:ListStackResources",
        ]
    },
    "logs": {
        "write": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    },
    "sqs": {"all": "sqs:*"},
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
            permission = app_permission.permission.name.lower()

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
            print(
                f"No valid permissions generated for {self.repo_name} in {environment}."
            )
            return None

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

    def attach_role(self, json_file_name, ec2_instance_id, region):
        """
        Creates an IAM role with inline permissions from a JSON file and attaches it to an EC2 instance.

        :param json_file_name: Path to the JSON file containing the IAM role and inline policy details.
        :param ec2_instance_id: ID of the EC2 instance to which the IAM role will be attached.
        :param region: AWS region where the EC2 instance is located (default is 'us-west-2').
        """
        # Initialize the boto3 clients for IAM and EC2
        iam_client = boto3.client("iam", region_name=region)
        ec2_client = boto3.client("ec2", region_name=region)

        # Read the JSON policy file
        try:
            with open(json_file_name, "r", encoding="utf-8") as f:
                policy_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: The file '{json_file_name}' does not exist.")
            return
        except json.JSONDecodeError:
            print(f"Error: The file '{json_file_name}' is not a valid JSON file.")
            return

        # Extract information from the JSON file
        role_name = policy_data["RoleName"]
        policy_name = policy_data["InlinePolicy"]["PolicyName"]
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": policy_data["InlinePolicy"]["Permissions"],
        }

        # Trust policy JSON for EC2
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        # Step 1: Create IAM Role
        try:
            iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Role for EC2 with inline permissions for {role_name}",
            )
            print(f"IAM Role '{role_name}' created successfully.")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"IAM Role '{role_name}' already exists.")

        # Step 2: Attach Inline Policy to IAM Role
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy),
            )
            print(
                f"Inline policy '{policy_name}' attached to IAM Role '{role_name}' successfully."
            )
        except Exception as e:
            print(f"Failed to attach inline policy to IAM Role: {e}")
            return

        # Step 3: Create an Instance Profile
        try:
            iam_client.create_instance_profile(InstanceProfileName=role_name)
            print(f"IAM Instance Profile '{role_name}' created successfully.")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"IAM Instance Profile '{role_name}' already exists.")

        # Wait for the Instance Profile to be created
        time.sleep(5)  # Wait 5 seconds to ensure the instance profile is available

        # Step 4: Add the IAM Role to the Instance Profile
        try:
            iam_client.add_role_to_instance_profile(
                InstanceProfileName=role_name, RoleName=role_name
            )
            print(
                f"IAM Role '{role_name}' added to Instance Profile '{role_name}' successfully."
            )
        except iam_client.exceptions.LimitExceededException:
            print(f"Cannot add more roles to the Instance Profile '{role_name}'.")
        except Exception as e:
            print(f"Failed to add IAM Role to Instance Profile: {e}")
            return

        # Step 5: Attach IAM Instance Profile to EC2 Instance
        try:
            ec2_client.associate_iam_instance_profile(
                IamInstanceProfile={"Name": role_name}, InstanceId=ec2_instance_id
            )
            print(
                f"IAM Instance Profile '{role_name}' attached to EC2 Instance '{ec2_instance_id}' successfully."
            )
        except ec2_client.exceptions.ClientError as e:
            print(f"Error attaching IAM Instance Profile to EC2 Instance: {e}")

        # Example usage
        # create_iam_role_and_attach("your_policy.json", "i-0abc123def456ghi7")

    def create_role_and_attach(self, ec2_instance_id, region, env):
        json_file_path = self.generate_role(env)
        if json_file_path:
            self.attach_role(json_file_path, ec2_instance_id, region)


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
