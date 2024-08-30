from apps.server.models.static_models import Dotfile, SudoUser, UbuntuPackage


def populate_static_defaults():
    # Example data for SudoUser
    sudo_users_data = [
        {
            "login": "vishal",
            "key": "https://vishalapte.com/auth_keys",
            "github": "vishalapte",
            "sudo": True,
            "dotfiles": True,
            "dotfile_force": False,
            "create_ed25519": True,
        },
        {
            "login": "finmachines",
            "sudo": True,
            "dotfiles": True,
            "dotfile_force": False,
            "create_ed25519": True,
        },
        {
            "login": "parag",
            "github": "sathayep",
            "sudo": True,
            "dotfiles": True,
            "dotfile_force": False,
            "create_ed25519": True,
        },
        {
            "login": "pitripathi",
            "github": "pushpendra-tripathi",
            "sudo": True,
            "dotfiles": True,
            "dotfile_force": False,
            "create_ed25519": True,
        },
    ]

    # Example data for Dotfile
    dotfiles_data = [
        {"file": "bash_login"},
        {"file": "bash_aliases"},
        {"file": "qux_python"},
    ]

    # Example data for UbuntuPackage
    ubuntu_packages_data = [
        "software-properties-common",
        "landscape-common",
        "update-notifier-common",
        "cron",
        "net-tools",
        "ufw",
        "acl",
        "mailutils",
        "postfix",
        "tree",
        "apache2",
        "certbot",
        "libsasl2-2",
        "libsasl2-modules",
        "libssl-dev",
        "libffi-dev",
        "liblapack-dev",
        "gfortran",
        "letsencrypt",
        "python3",
        "python3-dev",
        "python3-pip",
        "python3-venv",
        "python3-virtualenv",
        "python3-mysqldb",
        "python3-scipy",
        "python3-numpy",
        "python3-pandas",
        "python3-ipython",
        "memcached",
        "libapache2-mod-wsgi-py3",
        "mysql-server",
        "libmysqlclient-dev",
        "default-libmysqlclient-dev",
        "python3-mysql.connector",
        "python-celery-common",
        "libgraphviz-dev",
        "supervisor",
        "redis",
        "pkg-config",
    ]

    SudoUser.populate_data(sudo_users_data)
    Dotfile.populate_data(dotfiles_data)
    UbuntuPackage.populate_data(ubuntu_packages_data)
