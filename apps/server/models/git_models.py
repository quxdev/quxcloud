import os
from django.db import models

import requests
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com"
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.baptiste-preview+json",
}


class GitHubRepository(models.Model):
    name = models.CharField(max_length=255)
    template_owner = models.CharField(max_length=255)
    template_repo_name = models.CharField(max_length=255)
    deploy_key = models.TextField(blank=True, null=True)
    repo_owner = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_owner}:{self.name}"

    @property
    def ssh_url(self):
        return f"git@github.com:{self.repo_owner}/{self.name}.git"

    @property
    def template_url(self):
        return f"https://github.com/{self.template_owner}/{self.template_repo_name}"

    def to_dict(self):
        return {
            "git_repo": self.name,
            "template_owner": self.template_owner,
            "template_repo_name": self.template_repo_name,
            "deploy_key": self.deploy_key,
            "repo_owner": self.repo_owner,
            "full_github_url": self.ssh_url,
        }

    def exists(self):
        g = Github(GITHUB_TOKEN)
        try:
            repo = g.get_repo(f"{self.repo_owner}/{self.name}")
            print(f"Repository {self.name} already exists under {self.repo_owner}.")
            return repo
        except Exception as _:
            print(f"Repository {self.name} does not exist.")
            return None

    def create(self):
        url = (
            f"{GITHUB_API_URL}/repos/{self.template_owner}/"
            f"{self.template_repo_name}/generate"
        )
        payload = {
            "owner": self.repo_owner,
            "name": self.name,
            "private": True,
        }
        response = requests.post(url, json=payload, headers=GITHUB_HEADERS, timeout=30)
        if response.status_code == 201:
            print(
                f"Repository {self.name} created successfully under {self.repo_owner}."
            )
            return response.json()

        print(f"Failed to create repository: {response.status_code} {response.text}")
        return None

    def add_deploy_key(self, key_name, public_key):
        repo = self.exists()
        if repo:
            try:
                # Attempt to add the deploy key
                repo.create_key(title=key_name, key=public_key, read_only=True)
                print(f"Deploy key {key_name} added to repository {repo.name}.")
                return True
            except Exception as e:
                # Check if the exception is due to the key already existing
                if "key already exists" in str(e) or "key is already in use" in str(e):
                    print(
                        f"Deploy key {key_name} already exists or is in use for repository {repo.name}."
                    )
                    return True

                # Raise the exception if it's something else
                raise e
        print(f"Repository {self.name} does not exist.")
        return False
