from django.db import models
import boto3


class EC2Instance(models.Model):
    instance_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    instance_type = models.CharField(max_length=20)
    region = models.CharField(max_length=20)
    availability_zone = models.CharField(max_length=20)
    public_ip = models.GenericIPAddressField(blank=True, null=True)
    private_ip = models.GenericIPAddressField(blank=True, null=True)
    state = models.CharField(max_length=20)
    launch_time = models.DateTimeField()
    iam_role = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name}" or f"{self.instance_id}"


class S3Bucket(models.Model):
    name = models.CharField(max_length=255, unique=True)
    region = models.CharField(max_length=20)
    creation_date = models.DateTimeField()

    def __str__(self):
        return f"{self.name}"


class IAMPolicy(models.Model):
    policy_name = models.CharField(max_length=255, unique=True)
    policy_id = models.CharField(max_length=128, unique=True)
    arn = models.CharField(max_length=255)
    create_date = models.DateTimeField()
    policy_document = models.JSONField()

    def __str__(self):
        return f"{self.policy_name}"


class IAMInlinePolicy(models.Model):
    role = models.ForeignKey(
        "IAMRole", related_name="inline_policies", on_delete=models.CASCADE
    )
    policy_name = models.CharField(max_length=255)
    policy_document = models.JSONField()

    def __str__(self):
        return f"{self.role.role_name} - {self.policy_name}"


class IAMRole(models.Model):
    role_name = models.CharField(max_length=255, unique=True)
    role_id = models.CharField(max_length=128, unique=True)
    arn = models.CharField(max_length=255)
    create_date = models.DateTimeField()
    policies = models.ManyToManyField("IAMPolicy", related_name="roles")
    # Inline policies are linked through a ForeignKey in IAMInlinePolicy

    def __str__(self):
        return f"{self.role_name}"

    def sync_inline_policies(self, region):
        client = boto3.client("iam", region_name=region)
        policies = client.list_role_policies(RoleName=self.role_name)
        for policy_name in policies["PolicyNames"]:
            policy = client.get_role_policy(
                RoleName=self.role_name, PolicyName=policy_name
            )
            IAMInlinePolicy.objects.update_or_create(
                role=self,
                policy_name=policy_name,
                defaults={"policy_document": policy["PolicyDocument"]},
            )

    def attach_inline_policy(self, policy_name, policy_document, region):
        client = boto3.client("iam", region_name=region)
        client.put_role_policy(
            RoleName=self.role_name,
            PolicyName=policy_name,
            PolicyDocument=policy_document,
        )
        IAMInlinePolicy.objects.create(
            role=self, policy_name=policy_name, policy_document=policy_document
        )

    def delete_inline_policy(self, policy_name, region):
        client = boto3.client("iam", region_name=region)
        client.delete_role_policy(RoleName=self.role_name, PolicyName=policy_name)
        IAMInlinePolicy.objects.filter(role=self, policy_name=policy_name).delete()


class IAMPermission(models.Model):
    action = models.CharField(max_length=255)
    resource = models.CharField(max_length=255)

    def __str__(self):
        return f"Action: {self.action}, Resource: {self.resource}"


class LambdaFunction(models.Model):
    function_name = models.CharField(max_length=255, unique=True)
    function_arn = models.CharField(max_length=255, unique=True)
    runtime = models.CharField(max_length=64)
    handler = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    code_size = models.BigIntegerField()
    description = models.TextField(blank=True, null=True)
    timeout = models.IntegerField()
    memory_size = models.IntegerField()
    last_modified = models.DateTimeField()
    region = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.function_name}"


class SQSQueue(models.Model):
    queue_name = models.CharField(max_length=255, unique=True)
    queue_url = models.URLField(max_length=1024, unique=True)
    region = models.CharField(max_length=64)
    arn = models.CharField(max_length=255, unique=True)
    created_timestamp = models.DateTimeField()
    visibility_timeout = models.IntegerField()
    maximum_message_size = models.IntegerField()
    message_retention_period = models.IntegerField()

    def __str__(self):
        return f"{self.queue_name}"
