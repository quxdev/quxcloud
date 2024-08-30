from django.db import models
import paramiko
import os
from apps.server.models.git_models import GitHubRepository
from apps.server.models.ec2_models import EC2Instance
from apps.server.models.ansible_models import AnsiblePlay
from apps.server.models.static_models import SudoUser, Dotfile, UbuntuPackage


class DjangoService(models.Model):
    service = models.CharField(max_length=255, blank=True, null=True)
    wrapper = models.CharField(max_length=255, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    projdir = models.CharField(max_length=255, blank=True, null=True)
    service_account = models.CharField(max_length=255, blank=True, null=True)
    hostname = models.CharField(
        max_length=255, blank=True, null=True
    )  # Fixed typo from "hostname " to "hostname"
    python_version = models.CharField(max_length=255, blank=True, null=True)
    mysql_database = models.CharField(max_length=255, blank=True, null=True)
    mysql_username = models.CharField(max_length=255, blank=True, null=True)
    django_project = models.CharField(max_length=255, blank=True, null=True)
    requirements_file = models.CharField(max_length=255, blank=True, null=True)

    @property
    def fqdn_service(self):
        return f"{self.service}.{self.domain}"

    @property
    def fqdn(self):
        return f"{self.hostname}.{self.domain}"

    @property
    def code_path(self):
        if self.wrapper:
            return f"/opt/{self.service}/{self.wrapper}"
        return f"/opt/{self.service}"

    @property
    def venv_path(self):
        return f"/opt/{self.service}/venv"

    @property
    def apache_config_file(self):
        return f"{self.code_path}/config/etc/apache2/sites_available/fmapp.conf"

    def __str__(self):
        return f"{self.django_project}" or "Unnamed Django Project"

    def extravars(self):
        """
        Gathers the necessary variables for Ansible plays based on the DjangoProject instance.
        :return: A dictionary of extra variables.
        """
        extravars = {
            "fqdn": self.fqdn,
            "fqdn_service": self.fqdn_service,
            "service": self.service,
            "wrapper": self.wrapper,
            "code_path": self.code_path,
            "venv_path": self.venv_path,
            "site_config_filename": self.apache_config_file,
            "projdir": self.projdir,
            "service_account": self.service_account,
            "domain": self.domain,
            "hostname": self.hostname,
            "virtualenv_python": self.python_version,
            "mysql_database": self.mysql_database,
            "mysql_username": self.mysql_username,
            "requirements": f"{self.code_path}/{self.requirements_file}",
        }
        return extravars

    @classmethod
    def populate_data(cls, data):
        """
        Populates the DjangoProject model based on the given data.
        :param data: A dictionary containing Django project information.
        """
        requirements_file = "requirements/py312_dj5.txt"

        project, created = cls.objects.update_or_create(
            DJANGO_PROJECT=data.get("DJANGO_PROJECT"),
            defaults={
                "service": data.get("service"),
                "wrapper": data.get("wrapper"),
                "projdir": data.get("projdir"),
                "service_account": data.get("service_account"),
                "domain": data.get("domain"),
                "hostname": data.get("hostname"),
                "python_version": data.get("virtualenv_python"),
                "mysql_database": data.get("mysql_database"),
                "mysql_username": data.get("mysql_username"),
                "requirements": requirements_file,
            },
        )
        print(
            f"{'Created' if created else 'Updated'} DjangoProject: {project.django_project}"
        )
        return project


class DjangoProject(models.Model):
    service = models.ForeignKey(DjangoService, on_delete=models.CASCADE)
    ec2_instance = models.ForeignKey(EC2Instance, on_delete=models.CASCADE)
    git_repo = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE)
    environment = models.CharField(max_length=255, default="dev")
    aws_region = models.CharField(max_length=255, default="us-east-1")
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    public_ip_address = models.CharField(max_length=255, blank=True, null=True)
    public_dns_name = models.CharField(max_length=255, blank=True, null=True)
    git_branch = models.CharField(max_length=255, default="main")

    def __str__(self):
        return f"{self.service} - {self.environment}"

    def to_dict(self):
        data = {
            "service": self.service,
            "environment": self.environment,
            "aws_region": self.aws_region,
            "public_ip_address": self.public_ip_address,
            "public_dns_name": self.public_dns_name,
            "git_version": self.git_branch,
        }
        data.update(self.service.extravars())
        data.update(self.ec2_instance.to_dict())
        data.update(self.git_repo.to_dict())
        return data

    def extravars(self):
        users = SudoUser.extravars()
        dotfiles = Dotfile.extravars()
        ubuntu_packages = UbuntuPackage.extravars()

        project_details = self.to_dict()

        extravars = {
            "users": users,
            "dotfiles": dotfiles,
            "ubuntu_packages": ubuntu_packages,
            **project_details,
        }
        print(extravars)
        return extravars

    def get_public_key(self, user):

        if self.public_ip_address is None:
            print("No public IP address available.")
            return None

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.public_ip_address,
            username="ubuntu",
            key_filename=os.getenv("PRIVATE_KEY_FILE_PATH"),
        )
        print(f"Connected to {self.public_ip_address}")

        _, stdout, _ = ssh.exec_command(f"sudo cat /home/{user}/.ssh/id_ed25519.pub")
        print(stdout)
        public_key = stdout.read().decode().strip()

        print(f"Public Key: {public_key}")

        ssh.close()

        return public_key

    def deploy_all_plays(self):
        """
        Deploys the Django project to the EC2 instance.
        """
        for play in AnsiblePlay.objects.filter(enabled=True).order_by("order"):
            self.deploy_play(
                self.public_ip_address, play.name, extravars=self.extravars()
            )

    def deploy_play(self, instance_ip_address, play_name, extravars):
        """
        Runs a single play by name.
        :param play_name: The name of the play to run.
        :param extravars: A dictionary of extra variables to pass to the playbook.
        """

        play = AnsiblePlay.objects.get(name=play_name)
        runner = play.run_play(instance_ip_address, extravars=extravars)
        return runner

    def deploy_1(self):
        # 1. create a new EC2 instance if not already created
        if not self.public_ip_address:
            instance = self.ec2_instance.create_instance(self.aws_region)
            print(f"Instance created: {instance}")
            # save instance details
            self.instance_id = instance["instance_id"] if instance else None
            self.public_ip_address = instance["public_ip"] if instance else None
            self.public_dns_name = instance["public_dns"] if instance else None
            self.save()
        else:
            print("**** Instance already exists ****")
            print(f"Instance ID: {self.instance_id}")
            print(f"Public IP Address: {self.public_ip_address}")
            print(f"Public DNS Name: {self.public_dns_name}")
            print("**** Instance already exists ****")
        # 2. create a new GitHub repository if required
        if not self.git_repo.exists():
            self.git_repo.create()
            print(f"Repository created: {self.git_repo}")
        else:
            print(f"Repository already exists: {self.git_repo}")

    def deploy_2(self):
        if not self.public_ip_address:
            print("No instance available.")
            return

        if not self.git_repo.exists():
            print("No repository available.")
            return

        extra_vars = self.extravars()
        print(extra_vars)
        plays = AnsiblePlay.objects.filter(enabled=True).order_by("order")
        plays_basic = [play.name for play in plays if play.order < 5]
        print(plays_basic)
        # 3. deploy the basic plays
        for play in plays_basic:
            self.deploy_play(self.public_ip_address, play, extra_vars)

        finmachines_deploy_key = self.get_public_key("finmachines")
        print(f"FinMachines Deploy Key: {finmachines_deploy_key}")

        # 4. Add the deploy key to the GitHub repository
        self.git_repo.add_deploy_key(self.service.fqdn_service, finmachines_deploy_key)

        # 5. deploy the remaining plays
        remaining_plays = [play.name for play in plays if play.order >= 5]
        for play in remaining_plays:
            self.deploy_play(self.public_ip_address, play, extra_vars)
