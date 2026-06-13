"""Development settings for Tavern."""

from .base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])  # noqa: F405

DATABASE_ENGINE = env("DATABASE_ENGINE", default="sqlite")  # noqa: F405

if DATABASE_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("MYSQL_DATABASE", default="tavern"),  # noqa: F405
            "USER": env("MYSQL_USER", default="tavern"),  # noqa: F405
            "PASSWORD": env("MYSQL_PASSWORD", default="tavern_dev_password"),  # noqa: F405
            "HOST": env("MYSQL_HOST", default="127.0.0.1"),  # noqa: F405
            "PORT": env("MYSQL_PORT", default="3306"),  # noqa: F405
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
