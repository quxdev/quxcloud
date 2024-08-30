# Qjango - A Qux Django Template

## Getting Started

```shell
account="quxdev"
repo="quxcloud"

git clone https://github.com/${account}/${repo}.git
cd ${repo}

# Update submodules
git submodule update --init

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
# Upgrade pip and install packages
pip install --upgrade pip
pip install -r requirements/project.txt

# Migrate models to db.sqlite3
python manage.py migrate

# Load fixtures
python manage.py loaddata apps/aws/fixtures/*.json
python manage.py loaddata apps/server/fixtures/*.json

# Configure project/.env
dotenv="project/.env"
if [ ! -f dotenv ]; then
    touch ${dotenv}
    secret=$(python manage.py generate_secret_key)
    echo "DJANGO_SECRET_KEY=\"${secret}\"" >> ${dotenv}
    echo "DJANGO_DEBUG=true" >> ${dotenv}
    echo "BOOTSTRAP=bs5" >> ${dotenv}
    echo "DJANGO_ALLOWED_HOSTS=\"localhost\"" >> ${dotenv}
    echo "GITHUB_TOKEN=\"your github token\"" >> ${dotenv}
    echo "PRIVATE_KEY_FILE_PATH=\"your private key file full path\"" >> ${dotenv}
fi

# Runserver and test
python manage.py runserver

