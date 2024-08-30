import os
import boto3
from dotenv import load_dotenv
from .models import EC2InstanceConfiguration

# Load environment variables from .env file
load_dotenv()


class EC2InstanceManager:
    def __init__(self, config: EC2InstanceConfiguration):
        self.config = config
        self.ec2_client = boto3.client(
            "ec2",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=self.config.region,  # Use the region specified in the model
        )
        self.ami_id = self.get_ami_id()
        self.security_group_ids = self.get_security_group_ids()

    def get_ami_id(self):
        # Search for the latest Ubuntu 22.04 LTS AMI
        filters = [
            {
                "Name": "name",
                "Values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
            },
            {
                "Name": "owner-id",
                "Values": ["099720109477"],
            },  # Canonical's AWS account ID
            {"Name": "state", "Values": ["available"]},
        ]

        response = self.ec2_client.describe_images(
            Filters=filters,
            Owners=["099720109477"],  # Canonical's AWS account ID
            MaxResults=100,  # Fetch up to 100 results (adjust if needed)
        )

        images = response.get("Images", [])
        if images:
            # Sort the images by CreationDate to get the latest one
            latest_image = sorted(
                images, key=lambda x: x["CreationDate"], reverse=True
            )[0]
            return latest_image["ImageId"]

        print("No Ubuntu 22.04 LTS AMI found.")
        return None

    def get_default_security_group(self):
        try:
            response = self.ec2_client.describe_security_groups(
                Filters=[{"Name": "group-name", "Values": ["default"]}]
            )
            default_sg = response["SecurityGroups"][0]["GroupId"]
            print(f"Default security group ID: {default_sg}")
            return default_sg
        except Exception as e:
            print(f"Failed to retrieve the default security group: {str(e)}")
            return None

    def get_security_group_ids(self):
        security_group_list = self.config.get_security_group_list()
        if not security_group_list:
            return [self.get_default_security_group()]
        return security_group_list

    def create_instance(self):
        if not self.ami_id:
            print("No AMI ID available, aborting instance creation.")
            return None

        try:
            response = self.ec2_client.run_instances(
                ImageId=self.ami_id,
                InstanceType=self.config.instance_type,
                KeyName=self.config.key_name,
                SecurityGroupIds=self.security_group_ids,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": self.config.name},
                        ],
                    },
                ],
            )

            instance = response["Instances"][0]
            instance_id = instance["InstanceId"]
            print(f"EC2 instance created with Instance ID: {instance_id}")

            # Wait until the instance is running and has an IP assigned
            waiter = self.ec2_client.get_waiter("instance_running")
            waiter.wait(InstanceIds=[instance_id])

            # Retrieve the instance's public IP address
            instance_description = self.ec2_client.describe_instances(
                InstanceIds=[instance_id]
            )
            public_ip = instance_description["Reservations"][0]["Instances"][0].get(
                "PublicIpAddress"
            )
            public_dns = instance_description["Reservations"][0]["Instances"][0].get(
                "PublicDnsName"
            )

            # Save the instance ID and IP in the configuration
            self.config.instance_id = instance_id
            self.config.public_ip_address = public_ip
            self.config.public_dns_name = public_dns
            self.config.hostname = (
                self.config.name
            )  # Use the instance name as the hostname
            self.config.save()

            print(f"Instance Public IP: {public_ip}")
            print(f"Instance Public DNS: {public_dns}")

            return instance_id
        except Exception as e:
            print(f"Failed to create EC2 instance: {str(e)}")
            return None


def create_instance(name):
    # Assume you have an EC2InstanceConfiguration object stored in `config`
    config = EC2InstanceConfiguration.objects.get(name=name)

    # Create an instance manager with the configuration
    ec2_manager = EC2InstanceManager(config)

    # Create the EC2 instance
    instance_id = ec2_manager.create_instance()

    print(f"Instance ID: {instance_id}")
