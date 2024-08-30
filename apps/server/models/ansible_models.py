import os
from django.conf import settings

from django.db import models
import ansible_runner


class AnsiblePlay(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    yml_file = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def run_all_enabled_plays(cls, instance_ip, extravars=None):
        """
        Runs all enabled plays in the correct order using ansible-runner.
        :param extravars: A dictionary of extra variables to pass to each playbook.
        """
        plays = cls.objects.filter(enabled=True).order_by("order")
        for play in plays:
            print(f"Running play: {play.name}")
            result = play.run_play(instance_ip, extravars=extravars)
            if result.status != "successful":
                print(f"Play {play.name} failed with status: {result.status}")
                break  # Stop execution if a play fails

            print(f"Play {play.name} completed successfully.")

    def run_play(self, instance_ip, extravars=None):
        """
        Runs the play using ansible-runner with the provided extra variables.
        :param extravars: A dictionary of extra variables to pass to the playbook.
        """

        envvars = {
            "ANSIBLE_PRIVATE_KEY_FILE": os.getenv("PRIVATE_KEY_FILE_PATH"),
            "ANSIBLE_REMOTE_USER": "ubuntu",
        }
        inventory_content = f"{instance_ip}"

        runner_private_dir = os.path.join(
            settings.BASE_DIR, "apps", "server", "ansible_playbooks"
        )
        playbook_path = os.path.join(
            runner_private_dir,
            "project",
            "tasks",
            str(self.yml_file),
        )
        artifacts_dir = os.path.join(settings.BASE_DIR, "data", "artifacts")
        print(playbook_path)
        result = ansible_runner.run(
            private_data_dir=runner_private_dir,
            playbook=playbook_path,
            inventory=inventory_content,
            extravars=extravars,
            envvars=envvars,
            artifact_dir=artifacts_dir,
        )
        return result

    @classmethod
    def populate(cls, data):
        """
        Populates the AnsiblePlay table with data from a list of dictionaries.
        :param data: A list of dictionaries containing AnsiblePlay data.
        """
        for item in data:
            cls.objects.create(**item)


def populate_plays():
    plays = [
        {
            "name": "Ubuntu",
            "description": "setup host name, install packages, install apache2 and enable wsgi and ssl",
            "order": 0,
            "enabled": True,
            "yml_file": "ubuntu.yml",
        },
        {
            "name": "Nodejs",
            "description": "setup nodejs",
            "order": 1,
            "enabled": False,
            "yml_file": "nodejs.yml",
        },
        {
            "name": "Certs",
            "description": "setup ssl certs",
            "order": 2,
            "enabled": True,
            "yml_file": "certs.yml",
        },
        {
            "name": "Sudoers",
            "description": "Setup sudoers",
            "order": 3,
            "enabled": True,
            "yml_file": "sudoer.yml",
        },
        {
            "name": "User",
            "description": "setup users",
            "order": 4,
            "enabled": True,
            "yml_file": "user.yml",
        },
        {
            "name": "Gitrepo",
            "description": "Setup git repo",
            "order": 5,
            "enabled": True,
            "yml_file": "gitrepo.yml",
        },
        {
            "name": "MYSQL",
            "description": "setup mysql",
            "order": 6,
            "enabled": True,
            "yml_file": "mysql.yml",
        },
        {
            "name": "Supervisor",
            "description": "setup supervisor",
            "order": 7,
            "enabled": True,
            "yml_file": "supervisor.yml",
        },
        {
            "name": "Apache",
            "description": "setup apache2",
            "order": 8,
            "enabled": True,
            "yml_file": "apache2.yml",
        },
    ]
    AnsiblePlay.populate(plays)
