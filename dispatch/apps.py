from django.apps import AppConfig


class DispatchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dispatch"
    def ready(self):
        # import signals to register model hooks
        try:
            import dispatch.signals  # noqa: F401
        except Exception:
            pass
