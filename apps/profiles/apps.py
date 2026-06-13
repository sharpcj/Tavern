"""Django app configuration for profiles."""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    verbose_name = "Profiles"
