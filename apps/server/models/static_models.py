from django.db import models


class SudoUser(models.Model):
    login = models.CharField(max_length=255)
    key = models.URLField(blank=True, null=True)  # Optional URL field for auth keys
    github = models.CharField(max_length=255, blank=True, null=True)
    sudo = models.BooleanField(default=False)
    dotfiles = models.BooleanField(default=False)
    dotfile_force = models.BooleanField(default=False)
    create_ed25519 = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.login}"

    def to_dict(self):
        """
        Gathers the necessary variables for Ansible plays based on the SudoUser instance.
        :return: A dictionary of extra variables.
        """
        return {
            "login": self.login,
            "key": self.key,
            "github": self.github,
            "sudo": self.sudo,
            "dotfiles": self.dotfiles,
            "dotfile_force": self.dotfile_force,
            "create_ed25519": self.create_ed25519,
        }

    @classmethod
    def extravars(cls):
        """
        Gathers the necessary variables for Ansible plays based on the SudoUser instance.
        :return: A dictionary of extra variables.
        """
        extravars = [x.to_dict() for x in cls.objects.all()]
        return extravars

    @classmethod
    def populate_data(cls, data):
        """
        Populates the SudoUser model based on the given data.
        :param data: A list of dictionaries containing sudo user information.
        """
        for entry in data:
            user, created = cls.objects.update_or_create(
                login=entry.get("login"),
                defaults={
                    "key": entry.get("key", ""),
                    "github": entry.get("github", ""),
                    "sudo": entry.get("sudo", False),
                    "dotfiles": entry.get("dotfiles", False),
                    "dotfile_force": entry.get("dotfile_force", False),
                    "create_ed25519": entry.get("create_ed25519", False),
                },
            )
            print(f"{'Created' if created else 'Updated'} SudoUser: {user.login}")


class Dotfile(models.Model):
    file = models.CharField(max_length=255)  # Name of the dotfile

    def __str__(self):
        return f"{self.file}"

    @classmethod
    def populate_data(cls, data):
        """
        Populates the Dotfile model based on the given data.
        :param data: A list of dictionaries containing dotfile information.
        """
        for entry in data:
            dotfile, created = cls.objects.update_or_create(file=entry.get("file"))
            print(f"{'Created' if created else 'Updated'} Dotfile: {dotfile.file}")

    @classmethod
    def extravars(cls):
        """
        Gathers the necessary variables for Ansible plays based on the Dotfile instance.
        :return: A dictionary of extra variables.
        """
        return [x.file for x in cls.objects.all()]


class UbuntuPackage(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Name of the Ubuntu package

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def extravars(cls):
        """
        Gathers the necessary variables for Ansible plays based on the UbuntuPackage instance.
        :return: A dictionary of extra variables.
        """
        return [x.name for x in cls.objects.all()]

    @classmethod
    def populate_data(cls, packages):
        """
        Populates the UbuntuPackage model with a list of package names.
        :param packages: A list of package names.
        """
        for package_name in packages:
            package, created = cls.objects.update_or_create(name=package_name)
            print(
                f"{'Created' if created else 'Updated'} UbuntuPackage: {package.name}"
            )
