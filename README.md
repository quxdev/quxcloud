# Quxcloud => your superpower for devops

## Getting Started

# Setup the application 
Please refer to install.md for setup instructions

# How to use?

# Ensure you have the type of instance you need to create
- Get the instance name from aws - default is t3.micro
- Get the ami_id for the os you want to install - default is set for Ubuntu 24.04 LTS
- key_name: You need the keypair used in AWS to be attached to the instance, this is required for you to ssh into the server using this key
- server_admin: The admin email id you wish to add
- cert_email: The email that will go on the SSL certificates
- security_group_ids: A comma separated list of security group ids you wish to associate with the instance, this is optional and will default to the AWS default security group.

# Create an entry for the Git repo
Create an entry for the git repo you wish to either create or use
- name
- template_owner: quxdev
- template_repo_name: qjango

# Create a django service
A django service is the application that you wish to deploy. It has the following information it needs.
- service: name of the service
- wrapper: name of the wrapper directory you want to setup : /opt/<wrapper>/service
- domain: domain you want to associate with this application
- projdir: project
- service_account: finmachines
- hostname: name of the machine like trishul 
- python_version: python3.12. Its important to match the Ubuntu Release version with the python version it supports (in-built)
- mysql_database: name of the mysql database that needs to be created
- mysql_username: name of the user for mysql
- django_project: name of the django project - generally same as the service
- requirements_file: relative path to the requirements file that will be used to build (requirements/py312_dj5.txt)

# Create a django project
A django project is an instance of the django service, you can have a django project for dev, prod, staging etc for the same service.
- service: The django service you defined earlier
- git_repo: The github repo you defined earlier
- environment: dev or prod or stage
- aws_region: The AWS region you wish to use to create the EC2 instance
- git_branch: The specific branch you want to use to deploy this project

# Deploy the application
Execute the following in the django shell
```python
d_project = DjangoProject.objects.get(service='piper',environment='dev')
d_project.deploy_1()
```
The deploy_1 step will create the git repo if required and will also create the instance if required.
Please note down the public ip address in this step. You could also use an existing instance by updating the public_ip_address in the django project you created earlier.

Create the appropriate A records in you hosting provider using the ip address above. Ensure that you use the same host name to create the A records.

Now execute deploy_2 to complete the process
```python
d_project = DjangoProject.objects.get(service='piper',environment='dev')
d_project.deploy_2()
```

