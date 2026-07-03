import os
import secrets
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key

from config.credential_storage import (
    CREDENTIAL_STORAGE_ENV,
    CREDENTIAL_STORAGE_FILE,
    CREDENTIAL_STORAGE_SYSTEM,
    CredentialStorageError,
    get_system_credential,
    is_placeholder_secret,
    set_system_credential,
)
from config.database import DEFAULT_DATABASE_NAME
from config.env import parse_env_file
from config.file_backups import backup_existing_file


SECRET_KEYS = {"DATABASE_ENCRYPTION_KEY", "SECRET_KEY"}


def _quote_env_value(value):
    escaped_value = value.replace('"', '\\"')
    if any(char.isspace() for char in value) or "#" in value:
        return f'"{escaped_value}"'
    return value


class Command(BaseCommand):
    help = "Create or update local HolyFHIR settings and credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "--env-file",
            default=".env",
            help="Environment file to create or update. Default: .env.",
        )
        parser.add_argument(
            "--example-file",
            default=".env.example",
            help="Environment template to copy keys/defaults from. Default: .env.example.",
        )
        parser.add_argument(
            "--credential-storage",
            choices=(CREDENTIAL_STORAGE_SYSTEM, CREDENTIAL_STORAGE_FILE),
            default=os.getenv(CREDENTIAL_STORAGE_ENV, CREDENTIAL_STORAGE_FILE),
            help=(
                "Where HolyFHIR stores local credentials. Use 'system' for this computer's secure storage "
                "or 'file' to store credentials in the settings file."
            ),
        )
        parser.add_argument(
            "--rotate",
            action="store_true",
            help=(
                "Generate new secrets even when usable values already exist. "
                "This can make an existing encrypted database unreadable."
            ),
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip interactive confirmation prompts. Intended for scripts only.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        env_path = self._resolve_path(base_dir, options["env_file"])
        example_path = self._resolve_path(base_dir, options["example_file"])
        credential_storage = options["credential_storage"]

        if not example_path.exists():
            raise CommandError(f"Missing environment example file: {example_path}")

        example_values = parse_env_file(example_path)
        env_values = parse_env_file(env_path) if env_path.exists() else {}
        merged_values = {**example_values, **env_values}

        for key in example_values:
            merged_values.setdefault(key, example_values[key])

        merged_values[CREDENTIAL_STORAGE_ENV] = credential_storage
        self._apply_runtime_defaults(merged_values, env_values)

        available_secrets = self._available_secrets(env_values, credential_storage)
        self._guard_existing_database(
            merged_values, available_secrets, options["rotate"]
        )

        existing_real_secret_keys = sorted(available_secrets)
        needs_confirmation = env_path.exists()
        if options["rotate"] and existing_real_secret_keys:
            self._confirm_rotation(
                env_path, existing_real_secret_keys, assume_yes=options["yes"]
            )
        elif needs_confirmation:
            self._confirm_existing_env_update(env_path, assume_yes=options["yes"])

        generated_secrets = {
            "DATABASE_ENCRYPTION_KEY": secrets.token_urlsafe(48),
            "SECRET_KEY": get_random_secret_key(),
        }

        if credential_storage == CREDENTIAL_STORAGE_SYSTEM:
            self._store_system_credentials(
                merged_values, available_secrets, generated_secrets, options["rotate"]
            )
        else:
            self._store_file_credentials(
                merged_values, generated_secrets, options["rotate"]
            )

        env_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path = backup_existing_file(env_path)
        self._write_env_file(env_path, example_path, example_values, merged_values)

        if credential_storage == CREDENTIAL_STORAGE_FILE:
            for key in SECRET_KEYS:
                os.environ.setdefault(key, merged_values[key])
        os.environ[CREDENTIAL_STORAGE_ENV] = credential_storage

        if backup_path:
            self.stdout.write(
                self.style.WARNING(f"Backed up previous .env to {backup_path}")
            )
        self.stdout.write(
            self.style.SUCCESS(self._success_message(credential_storage, env_path))
        )
        if options["rotate"]:
            self.stdout.write(
                self.style.WARNING(
                    "Credentials were changed. Existing encrypted databases may require backup/restore or re-encryption."
                )
            )

    def _resolve_path(self, base_dir, path):
        resolved = Path(path)
        if resolved.is_absolute():
            return resolved
        return base_dir / resolved

    def _available_secrets(self, env_values, credential_storage):
        available = {}

        for key in SECRET_KEYS:
            env_value = env_values.get(key, "").strip()
            if not is_placeholder_secret(key, env_value):
                available[key] = env_value

        if credential_storage == CREDENTIAL_STORAGE_SYSTEM:
            try:
                for key in SECRET_KEYS:
                    system_value = get_system_credential(key)
                    if system_value:
                        available[key] = system_value
            except CredentialStorageError as error:
                raise CommandError(str(error)) from error

        return available

    def _store_system_credentials(
        self, values, available_secrets, generated_secrets, rotate
    ):
        try:
            for key in SECRET_KEYS:
                value = (
                    generated_secrets[key]
                    if rotate
                    else available_secrets.get(key) or generated_secrets[key]
                )
                set_system_credential(key, value)
                values[key] = ""
        except CredentialStorageError as error:
            raise CommandError(str(error)) from error

    def _store_file_credentials(self, values, generated_secrets, rotate):
        for key in SECRET_KEYS:
            if rotate or is_placeholder_secret(key, values.get(key, "")):
                values[key] = generated_secrets[key]

    def _guard_existing_database(self, values, available_secrets, rotate):
        if rotate or available_secrets.get("DATABASE_ENCRYPTION_KEY"):
            return

        database_name = values.get("DATABASE_NAME") or DEFAULT_DATABASE_NAME
        database_path = Path(database_name)
        if not database_path.is_absolute():
            database_path = Path(settings.BASE_DIR) / database_path

        if database_path.exists():
            raise CommandError(
                "HolyFHIR found an existing encrypted database but no saved database key. "
                "For safety, it will not create a new key that cannot open the existing records."
            )

    def _apply_runtime_defaults(self, values, env_values):
        for key in ("DATABASE_NAME", "TIME_ZONE"):
            if key not in env_values and os.getenv(key):
                values[key] = os.environ[key]

    def _confirm_existing_env_update(self, env_path, assume_yes=False):
        if assume_yes:
            return

        self.stdout.write(
            self.style.WARNING(
                f"WARNING: {env_path} already exists. This command will rewrite the file using .env.example order."
            )
        )
        self.stdout.write(
            "Existing usable credentials will be preserved, but comments and formatting may be overwritten."
        )
        self._require_yes("Continue rewriting this settings file?")

    def _confirm_rotation(self, env_path, secret_keys, assume_yes=False):
        if assume_yes:
            return

        self.stdout.write(
            self.style.ERROR(
                "DANGER: You are about to change local HolyFHIR credentials."
            )
        )
        self.stdout.write(
            self.style.ERROR(
                "Changing the database key can permanently lock you out of the existing encrypted database "
                "unless you have a backup or re-encryption plan."
            )
        )
        self.stdout.write(f"File: {env_path}")
        self.stdout.write(
            f"Credentials that will be replaced: {', '.join(secret_keys)}"
        )
        self._require_yes("Type yes to change these credentials and rewrite .env.")

    def _require_yes(self, prompt):
        response = input(f"{prompt} [yes/no]: ").strip().lower()
        if response != "yes":
            raise CommandError("Aborted. No changes were written.")

    def _success_message(self, credential_storage, env_path):
        if credential_storage == CREDENTIAL_STORAGE_SYSTEM:
            return "Bootstrapped local settings. Credentials are stored in this computer's secure storage."
        return f"Bootstrapped local settings and credentials in {env_path}"

    def _write_env_file(self, env_path, example_path, example_values, values):
        lines = [
            "# Local HolyFHIR settings.",
            f"# Generated from {example_path.name}. Do not commit this file.",
            "",
        ]

        if values.get(CREDENTIAL_STORAGE_ENV) == CREDENTIAL_STORAGE_SYSTEM:
            lines.extend(
                [
                    "# Credentials are stored in this computer's secure storage.",
                    "# To store credentials in this file instead, set DATABASE_CREDENTIAL_STORAGE=file and run bootstrap_secrets again.",
                    "",
                ]
            )

        for key in example_values:
            lines.append(f"{key}={_quote_env_value(values.get(key, ''))}")

        extra_keys = sorted(set(values) - set(example_values))
        if extra_keys:
            lines.extend(["", "# Additional local values"])
            for key in extra_keys:
                lines.append(f"{key}={_quote_env_value(values[key])}")

        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
