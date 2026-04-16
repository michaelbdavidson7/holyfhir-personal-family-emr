import os
import secrets
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key

from config.env import parse_env_file
from config.file_backups import backup_existing_file


SECRET_PLACEHOLDERS = {
    "DATABASE_ENCRYPTION_KEY": {"", "replace-with-a-strong-passphrase"},
    "SECRET_KEY": {"", "django-insecure-development-only-change-me"},
}

SECRET_KEYS = {"DATABASE_ENCRYPTION_KEY", "SECRET_KEY"}


def _quote_env_value(value):
    escaped_value = value.replace('"', '\\"')
    if any(char.isspace() for char in value) or "#" in value:
        return f'"{escaped_value}"'
    return value


class Command(BaseCommand):
    help = "Create or update a local .env file with generated development secrets."

    def add_arguments(self, parser):
        parser.add_argument("--env-file", default=".env", help="Environment file to create or update. Default: .env.")
        parser.add_argument(
            "--example-file",
            default=".env.example",
            help="Environment template to copy keys/defaults from. Default: .env.example.",
        )
        parser.add_argument(
            "--rotate",
            action="store_true",
            help="Generate new secrets even when usable values already exist. This can make an existing encrypted database unreadable.",
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

        if not example_path.exists():
            raise CommandError(f"Missing environment example file: {example_path}")

        example_values = parse_env_file(example_path)
        env_values = parse_env_file(env_path) if env_path.exists() else {}
        merged_values = {**example_values, **env_values}

        for key in example_values:
            merged_values.setdefault(key, example_values[key])

        self._apply_runtime_defaults(merged_values, env_values)

        existing_real_secret_keys = [
            key
            for key in sorted(SECRET_KEYS)
            if key in env_values and env_values[key] not in SECRET_PLACEHOLDERS[key]
        ]
        needs_confirmation = env_path.exists()
        if options["rotate"] and existing_real_secret_keys:
            self._confirm_rotation(env_path, existing_real_secret_keys, assume_yes=options["yes"])
        elif needs_confirmation:
            self._confirm_existing_env_update(env_path, assume_yes=options["yes"])

        self._set_secret(
            merged_values,
            "DATABASE_ENCRYPTION_KEY",
            secrets.token_urlsafe(48),
            rotate=options["rotate"],
        )
        self._set_secret(
            merged_values,
            "SECRET_KEY",
            get_random_secret_key(),
            rotate=options["rotate"],
        )

        env_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path = backup_existing_file(env_path)
        self._write_env_file(env_path, example_path, example_values, merged_values)

        os.environ.setdefault("DATABASE_ENCRYPTION_KEY", merged_values["DATABASE_ENCRYPTION_KEY"])
        os.environ.setdefault("SECRET_KEY", merged_values["SECRET_KEY"])

        if backup_path:
            self.stdout.write(self.style.WARNING(f"Backed up previous .env to {backup_path}"))
        self.stdout.write(self.style.SUCCESS(f"Bootstrapped local secrets in {env_path}"))
        if options["rotate"]:
            self.stdout.write(
                self.style.WARNING(
                    "Secrets were rotated. Existing encrypted databases may require backup/restore or re-encryption."
                )
            )

    def _resolve_path(self, base_dir, path):
        resolved = Path(path)
        if resolved.is_absolute():
            return resolved
        return base_dir / resolved

    def _set_secret(self, values, key, generated_value, rotate=False):
        if rotate or values.get(key, "") in SECRET_PLACEHOLDERS[key]:
            values[key] = generated_value

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
        self.stdout.write("Existing usable secrets will be preserved, but comments and formatting may be overwritten.")
        self._require_yes("Continue rewriting this .env file?")

    def _confirm_rotation(self, env_path, secret_keys, assume_yes=False):
        if assume_yes:
            return

        self.stdout.write(self.style.ERROR("DANGER: You are about to rotate local HolyFHIR secrets."))
        self.stdout.write(
            self.style.ERROR(
                "Changing DATABASE_ENCRYPTION_KEY can permanently lock you out of the existing encrypted database "
                "unless you have a backup or re-encryption plan."
            )
        )
        self.stdout.write(f"File: {env_path}")
        self.stdout.write(f"Secrets that will be replaced: {', '.join(secret_keys)}")
        self._require_yes("Type yes to rotate these secrets and rewrite .env.")

    def _require_yes(self, prompt):
        response = input(f"{prompt} [yes/no]: ").strip().lower()
        if response != "yes":
            raise CommandError("Aborted. No changes were written.")

    def _write_env_file(self, env_path, example_path, example_values, values):
        lines = [
            "# Local HolyFHIR settings.",
            f"# Generated from {example_path.name}. Do not commit this file.",
            "",
        ]

        for key in example_values:
            lines.append(f"{key}={_quote_env_value(values.get(key, ''))}")

        extra_keys = sorted(set(values) - set(example_values))
        if extra_keys:
            lines.extend(["", "# Additional local values"])
            for key in extra_keys:
                lines.append(f"{key}={_quote_env_value(values[key])}")

        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
