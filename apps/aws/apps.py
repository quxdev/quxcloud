from django.apps import AppConfig


class GizmoConfig(AppConfig):
    name = "apps.aws"
    verbose_name = "AWS"

    def ready(self):
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        from . import signals
