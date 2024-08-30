import os
import boto3
from django.db import models


class EC2Instance(models.Model):
    name = models.CharField(max_length=255)
    instance_type = models.CharField(max_length=50, default="t3.micro")
    ami_source = models.CharField(max_length=50, default="Ubuntu 24.04 LTS")
    ami_id = models.CharField(max_length=100, default="ami-0522ab6e1ddcc7055")
    key_name = models.CharField(max_length=255)
    security_group_ids = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=(
            "Comma-separated list of security group IDs."
            "If blank, the default security group will be used."
        ),
    )
    server_admin = models.EmailField()
    cert_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    def to_dict(self):
        return {
            "server_admin": self.server_admin,
            "cert_email": self.cert_email,
        }

    def create_instance(self, region):
        if not self.ami_id:
            print("No AMI ID available, aborting instance creation.")
            return None

        EC2_CLIENT = boto3.client(
            "ec2",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region,  # Use the region specified in the model
        )

        try:
            security_group_ids = (
                self.security_group_ids.split(",") if self.security_group_ids else []
            )
            response = EC2_CLIENT.run_instances(
                ImageId=self.ami_id,
                InstanceType=self.instance_type,
                KeyName=self.key_name,
                SecurityGroupIds=security_group_ids,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": self.name},
                        ],
                    },
                ],
            )

            instance = response["Instances"][0]
            instance_id = instance["InstanceId"]
            print(f"EC2 instance created with Instance ID: {instance_id}")

            # Wait until the instance is running and has an IP assigned
            waiter = EC2_CLIENT.get_waiter("instance_running")
            waiter.wait(InstanceIds=[instance_id])

            # Retrieve the instance's public IP address
            instance_description = EC2_CLIENT.describe_instances(
                InstanceIds=[instance_id]
            )
            public_ip = instance_description["Reservations"][0]["Instances"][0].get(
                "PublicIpAddress"
            )
            public_dns = instance_description["Reservations"][0]["Instances"][0].get(
                "PublicDnsName"
            )

            print(f"Instance ID: {instance_id}")
            print(f"Instance Public IP: {public_ip}")
            print(f"Instance Public DNS: {public_dns}")

            return {
                "instance_id": instance_id,
                "public_ip": public_ip,
                "public_dns": public_dns,
            }
        except Exception as e:
            print(f"Failed to create EC2 instance: {str(e)}")
            return None

    @classmethod
    def populate(cls, data):
        # create a new instance for the given data
        instance = cls.objects.create(**data)
        return instance
