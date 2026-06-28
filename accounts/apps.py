from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    # Import signals when Django starts the application.
    # Without this, the signal handlers will never be registered.
    # Register signal handlers when the app is loaded.
    def ready(self):
        import accounts.signals