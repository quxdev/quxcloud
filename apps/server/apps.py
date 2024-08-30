from django.apps import AppConfig


class ServerConfig(AppConfig):
    name = "apps.server"
    verbose_name = "Server"

    def ready(self):
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        from . import signals
