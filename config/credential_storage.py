import os

from django.core.exceptions import ImproperlyConfigured


CREDENTIAL_STORAGE_FILE = "file"
CREDENTIAL_STORAGE_SYSTEM = "system"
CREDENTIAL_STORAGE_ENV = "DATABASE_CREDENTIAL_STORAGE"
CREDENTIAL_STORAGE_CHOICES = {CREDENTIAL_STORAGE_FILE, CREDENTIAL_STORAGE_SYSTEM}

KEYRING_SERVICE_NAME = "HolyFHIR Personal EMR"


SECRET_PLACEHOLDERS = {
    "DATABASE_ENCRYPTION_KEY": {"", "replace-with-a-strong-passphrase"},
    "SECRET_KEY": {"", "django-insecure-development-only-change-me"},
}


class CredentialStorageError(RuntimeError):
    pass


def credential_storage_mode(default=CREDENTIAL_STORAGE_FILE):
    value = os.getenv(CREDENTIAL_STORAGE_ENV, default).strip().lower()
    if value not in CREDENTIAL_STORAGE_CHOICES:
        choices = ", ".join(sorted(CREDENTIAL_STORAGE_CHOICES))
        raise ImproperlyConfigured(
            f"{CREDENTIAL_STORAGE_ENV} must be one of: {choices}."
        )
    return value


def is_placeholder_secret(key, value):
    return value in SECRET_PLACEHOLDERS.get(key, {""})


def get_env_secret(key):
    value = os.getenv(key, "").strip()
    if is_placeholder_secret(key, value):
        return ""
    return value


def _keyring():
    try:
        import keyring
        from keyring.errors import KeyringError
    except ImportError as error:
        raise CredentialStorageError(
            "System secure storage needs the Python 'keyring' package."
        ) from error

    return keyring, KeyringError


def get_system_credential(key):
    keyring, KeyringError = _keyring()
    try:
        return keyring.get_password(KEYRING_SERVICE_NAME, key) or ""
    except KeyringError as error:
        raise CredentialStorageError(
            "HolyFHIR could not read from this computer's secure storage."
        ) from error


def set_system_credential(key, value):
    keyring, KeyringError = _keyring()
    try:
        keyring.set_password(KEYRING_SERVICE_NAME, key, value)
    except KeyringError as error:
        raise CredentialStorageError(
            "HolyFHIR could not save to this computer's secure storage."
        ) from error


def get_configured_secret(key):
    env_value = get_env_secret(key)
    if env_value:
        return env_value

    if credential_storage_mode() == CREDENTIAL_STORAGE_SYSTEM:
        return get_system_credential(key)

    return ""
