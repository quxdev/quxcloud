from datetime import datetime
import boto3
from apps.aws.aws_models import (
    IAMRole,
    IAMPolicy,
    IAMInlinePolicy,
    EC2Instance,
    S3Bucket,
    LambdaFunction,
    SQSQueue,
)


def populate_iam_roles_and_policies(region_name):
    # Initialize boto3 IAM client
    client = boto3.client("iam", region_name=region_name)

    # Get list of all IAM roles
    roles = client.list_roles()

    for role_data in roles["Roles"]:
        role, _ = IAMRole.objects.update_or_create(
            role_name=role_data["RoleName"],
            defaults={
                "role_id": role_data["RoleId"],
                "arn": role_data["Arn"],
                "create_date": role_data["CreateDate"],
            },
        )

        # Fetch and attach managed policies to the role
        attached_policies = client.list_attached_role_policies(RoleName=role.role_name)
        for policy in attached_policies["AttachedPolicies"]:
            policy_details = client.get_policy(PolicyArn=policy["PolicyArn"])
            policy_version = client.get_policy_version(
                PolicyArn=policy["PolicyArn"],
                VersionId=policy_details["Policy"]["DefaultVersionId"],
            )
            iam_policy, _ = IAMPolicy.objects.update_or_create(
                policy_name=policy["PolicyName"],
                defaults={
                    "policy_id": policy_details["Policy"]["PolicyId"],
                    "arn": policy_details["Policy"]["Arn"],
                    "create_date": policy_details["Policy"]["CreateDate"],
                    "policy_document": policy_version["PolicyVersion"]["Document"],
                },
            )
            # Only add the policy if it's attached to the current role
            role.policies.add(iam_policy)
            print(
                f"Attached policy: {iam_policy.policy_name} to role: {role.role_name}"
            )

    print(f"Populated IAM roles and policies for region: {region_name}")


def populate_iam_inline_policies(region_name):
    client = boto3.client("iam", region_name=region_name)

    # Iterate over all roles in the database
    for role in IAMRole.objects.all():
        inline_policies = client.list_role_policies(RoleName=role.role_name)

        for policy_name in inline_policies["PolicyNames"]:
            policy = client.get_role_policy(
                RoleName=role.role_name, PolicyName=policy_name
            )
            IAMInlinePolicy.objects.update_or_create(
                role=role,
                policy_name=policy_name,
                defaults={"policy_document": policy["PolicyDocument"]},
            )

    print(f"Populated IAM inline policies for region: {region_name}")


def populate_ec2_instances(region_name):
    client = boto3.client("ec2", region_name=region_name)

    instances = client.describe_instances()

    for reservation in instances["Reservations"]:
        for instance_data in reservation["Instances"]:
            EC2Instance.objects.update_or_create(
                instance_id=instance_data["InstanceId"],
                defaults={
                    "name": next(
                        (
                            tag["Value"]
                            for tag in instance_data.get("Tags", [])
                            if tag["Key"] == "Name"
                        ),
                        None,
                    ),
                    "instance_type": instance_data["InstanceType"],
                    "region": region_name,
                    "availability_zone": instance_data["Placement"]["AvailabilityZone"],
                    "public_ip": instance_data.get("PublicIpAddress"),
                    "private_ip": instance_data.get("PrivateIpAddress"),
                    "state": instance_data["State"]["Name"],
                    "launch_time": instance_data["LaunchTime"],
                    "iam_role": instance_data.get("IamInstanceProfile", {}).get("Arn"),
                },
            )

    print(f"Populated EC2 instances for region: {region_name}")


def populate_s3_buckets(region_name):
    client = boto3.client("s3", region_name=region_name)

    buckets = client.list_buckets()

    for bucket_data in buckets["Buckets"]:
        bucket_location = client.get_bucket_location(Bucket=bucket_data["Name"])
        bucket_region = bucket_location["LocationConstraint"] or "us-east-1"
        if bucket_region == region_name:
            S3Bucket.objects.update_or_create(
                name=bucket_data["Name"],
                defaults={
                    "region": bucket_region,
                    "creation_date": bucket_data["CreationDate"],
                },
            )

    print(f"Populated S3 buckets for region: {region_name}")


def populate_lambda_functions(region_name):
    client = boto3.client("lambda", region_name=region_name)

    functions = client.list_functions()

    for function_data in functions["Functions"]:
        LambdaFunction.objects.update_or_create(
            function_name=function_data["FunctionName"],
            defaults={
                "function_arn": function_data["FunctionArn"],
                "runtime": function_data["Runtime"],
                "handler": function_data["Handler"],
                "role": function_data["Role"],
                "code_size": function_data["CodeSize"],
                "description": function_data.get("Description", ""),
                "timeout": function_data["Timeout"],
                "memory_size": function_data["MemorySize"],
                "last_modified": function_data["LastModified"],
                "region": region_name,
            },
        )

    print(f"Populated Lambda functions for region: {region_name}")


def populate_sqs_queues(region_name):
    client = boto3.client("sqs", region_name=region_name)

    queues = client.list_queues()

    if "QueueUrls" in queues:
        for queue_url in queues["QueueUrls"]:
            queue_attributes = client.get_queue_attributes(
                QueueUrl=queue_url, AttributeNames=["All"]
            )["Attributes"]

            # Convert Unix timestamp to datetime object
            created_timestamp = datetime.utcfromtimestamp(
                float(queue_attributes["CreatedTimestamp"])
            )

            SQSQueue.objects.update_or_create(
                queue_name=queue_attributes["QueueArn"].split(":")[-1],
                defaults={
                    "queue_url": queue_url,
                    "region": region_name,
                    "arn": queue_attributes["QueueArn"],
                    "created_timestamp": created_timestamp,
                    "visibility_timeout": queue_attributes["VisibilityTimeout"],
                    "maximum_message_size": queue_attributes["MaximumMessageSize"],
                    "message_retention_period": queue_attributes[
                        "MessageRetentionPeriod"
                    ],
                },
            )

    print(f"Populated SQS queues for region: {region_name}")


def populate_aws_resources(region_name):
    populate_iam_roles_and_policies(region_name)
    populate_iam_inline_policies(region_name)
    populate_ec2_instances(region_name)
    populate_s3_buckets(region_name)
    populate_lambda_functions(region_name)
    populate_sqs_queues(region_name)
