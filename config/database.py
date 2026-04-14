import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


DEFAULT_DATABASE_TIMEOUT = 20.0
DEFAULT_DATABASE_ENCRYPTION_REQUIRED = False
DEFAULT_DATABASE_CIPHER_PAGE_SIZE = 4096
DEFAULT_DATABASE_KDF_ITER = 256000
DEFAULT_DATABASE_CIPHER_COMPATIBILITY = 4


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _env_int(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def build_default_database_config(base_dir: Path):
    database_name = os.getenv("DATABASE_NAME", str(base_dir / "db.sqlite3"))
    encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY", "").strip()
    encryption_required = _env_flag(
        "DATABASE_ENCRYPTION_REQUIRED",
        default=DEFAULT_DATABASE_ENCRYPTION_REQUIRED,
    )

    if encryption_required and not encryption_key:
        raise ImproperlyConfigured(
            "DATABASE_ENCRYPTION_REQUIRED is enabled but DATABASE_ENCRYPTION_KEY is not set."
        )

    options = {
        "timeout": _env_float("DATABASE_TIMEOUT", DEFAULT_DATABASE_TIMEOUT),
    }

    if encryption_key:
        engine = "config.db.backends.sqlcipher"
        options["passphrase"] = encryption_key

        options["cipher_page_size"] = _env_int(
            "DATABASE_CIPHER_PAGE_SIZE",
            DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
        )

        options["kdf_iter"] = _env_int("DATABASE_KDF_ITER", DEFAULT_DATABASE_KDF_ITER)

        options["cipher_compatibility"] = _env_int(
            "DATABASE_CIPHER_COMPATIBILITY",
            DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
        )
    else:
        engine = "django.db.backends.sqlite3"

    database_config = {
        "ENGINE": engine,
        "NAME": database_name,
    }
    database_config["OPTIONS"] = options

    return {"default": database_config}
