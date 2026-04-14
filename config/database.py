import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name):
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return int(value)


def build_default_database_config(base_dir: Path):
    database_name = os.getenv("DATABASE_NAME", str(base_dir / "db.sqlite3"))
    encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY", "").strip()
    encryption_required = _env_flag("DATABASE_ENCRYPTION_REQUIRED", default=False)

    if encryption_required and not encryption_key:
        raise ImproperlyConfigured(
            "DATABASE_ENCRYPTION_REQUIRED is enabled but DATABASE_ENCRYPTION_KEY is not set."
        )

    options = {}
    timeout = os.getenv("DATABASE_TIMEOUT")
    if timeout:
        options["timeout"] = float(timeout)

    if encryption_key:
        engine = "config.db.backends.sqlcipher"
        options["passphrase"] = encryption_key

        cipher_page_size = _env_int("DATABASE_CIPHER_PAGE_SIZE")
        if cipher_page_size:
            options["cipher_page_size"] = cipher_page_size

        kdf_iter = _env_int("DATABASE_KDF_ITER")
        if kdf_iter:
            options["kdf_iter"] = kdf_iter

        cipher_compatibility = _env_int("DATABASE_CIPHER_COMPATIBILITY")
        if cipher_compatibility:
            options["cipher_compatibility"] = cipher_compatibility
    else:
        engine = "django.db.backends.sqlite3"

    database_config = {
        "ENGINE": engine,
        "NAME": database_name,
    }
    if options:
        database_config["OPTIONS"] = options

    return {"default": database_config}
