import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from config.sqlcipher import get_sqlcipher_dbapi


def _sql_quote(value):
    return str(value).replace("'", "''")


class Command(BaseCommand):
    help = "Convert a plaintext SQLite database file into an encrypted SQLCipher database."

    def add_arguments(self, parser):
        default_source = Path(settings.DATABASES["default"]["NAME"])
        default_target = default_source.with_name(f"{default_source.stem}.encrypted{default_source.suffix}")

        parser.add_argument("--source", default=str(default_source), help="Path to the plaintext SQLite database.")
        parser.add_argument("--target", default=str(default_target), help="Path for the encrypted SQLCipher database.")
        parser.add_argument("--key", help="Encryption key for the target database.")
        parser.add_argument(
            "--key-env",
            default="DATABASE_ENCRYPTION_KEY",
            help="Environment variable to read the encryption key from when --key is not supplied.",
        )
        parser.add_argument("--cipher-page-size", type=int, help="Optional SQLCipher page size for the target database.")
        parser.add_argument("--kdf-iter", type=int, help="Optional SQLCipher PBKDF iteration count for the target database.")
        parser.add_argument(
            "--cipher-compatibility",
            type=int,
            help="Optional SQLCipher compatibility mode for opening legacy databases.",
        )
        parser.add_argument("--force", action="store_true", help="Overwrite the target file if it already exists.")

    def handle(self, *args, **options):
        try:
            sqlcipher = get_sqlcipher_dbapi()
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        source = Path(options["source"]).expanduser().resolve()
        target = Path(options["target"]).expanduser().resolve()
        key = options["key"] or os.getenv(options["key_env"], "")

        if not key:
            raise CommandError("No encryption key was provided. Use --key or set the configured key environment variable.")

        if not source.exists():
            raise CommandError(f"Source database does not exist: {source}")

        if source == target:
            raise CommandError("Source and target databases must be different files.")

        if target.exists():
            if not options["force"]:
                raise CommandError(f"Target database already exists: {target}. Use --force to overwrite it.")
            target.unlink()

        target.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlcipher.connect(str(source))
        try:
            cursor = connection.cursor()

            cipher_compatibility = options.get("cipher_compatibility")
            if cipher_compatibility:
                cursor.execute(f"PRAGMA cipher_compatibility = {int(cipher_compatibility)}")

            cursor.execute(
                f"ATTACH DATABASE '{_sql_quote(target)}' AS encrypted KEY '{_sql_quote(key)}'"
            )

            cipher_page_size = options.get("cipher_page_size")
            if cipher_page_size:
                cursor.execute(f"PRAGMA encrypted.cipher_page_size = {int(cipher_page_size)}")

            kdf_iter = options.get("kdf_iter")
            if kdf_iter:
                cursor.execute(f"PRAGMA encrypted.kdf_iter = {int(kdf_iter)}")

            cursor.execute("SELECT sqlcipher_export('encrypted')")
            cursor.execute("DETACH DATABASE encrypted")
        except Exception as exc:
            if target.exists():
                target.unlink()
            raise CommandError(f"Database encryption failed: {exc}") from exc
        finally:
            connection.close()

        self.stdout.write(self.style.SUCCESS(f"Encrypted database written to {target}"))
