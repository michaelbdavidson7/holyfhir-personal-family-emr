import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, override_settings

from config.database import (
    DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
    DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
    DEFAULT_DATABASE_NAME,
    DEFAULT_DATABASE_KDF_ITER,
    DEFAULT_DATABASE_TIMEOUT,
    build_default_database_config,
)
from config.auth_forms import RateLimitedAdminAuthenticationForm, _cache_key
from config.db.backends.sqlcipher.base import _is_plaintext_sqlite_database
from config.env import load_env, parse_env_file


class DatabaseConfigTests(SimpleTestCase):
    def test_requires_encryption_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_default_database_config(Path("/tmp/personal-emr"))

    def test_always_uses_sqlcipher_when_key_is_present(self):
        with patch.dict(
            "os.environ",
            {
                "DATABASE_ENCRYPTION_KEY": "super-secret",
            },
            clear=True,
        ):
            databases = build_default_database_config(Path("/tmp/personal-emr"))

        self.assertEqual(databases["default"]["ENGINE"], "config.db.backends.sqlcipher")
        self.assertEqual(databases["default"]["OPTIONS"]["passphrase"], "super-secret")
        self.assertEqual(databases["default"]["OPTIONS"]["cipher_page_size"], DEFAULT_DATABASE_CIPHER_PAGE_SIZE)
        self.assertEqual(databases["default"]["OPTIONS"]["kdf_iter"], DEFAULT_DATABASE_KDF_ITER)
        self.assertEqual(
            databases["default"]["OPTIONS"]["cipher_compatibility"],
            DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
        )
        self.assertEqual(databases["default"]["OPTIONS"]["timeout"], DEFAULT_DATABASE_TIMEOUT)

    def test_can_override_database_defaults(self):
        with patch.dict(
            "os.environ",
            {
                "DATABASE_NAME": "custom.sqlite3",
                "DATABASE_TIMEOUT": "30",
                "DATABASE_ENCRYPTION_KEY": "super-secret",
                "DATABASE_CIPHER_PAGE_SIZE": "8192",
                "DATABASE_KDF_ITER": "512000",
                "DATABASE_CIPHER_COMPATIBILITY": "4",
            },
            clear=True,
        ):
            databases = build_default_database_config(Path("/tmp/personal-emr"))

        self.assertEqual(databases["default"]["NAME"], "custom.sqlite3")
        self.assertEqual(databases["default"]["OPTIONS"]["timeout"], 30.0)
        self.assertEqual(databases["default"]["OPTIONS"]["cipher_page_size"], 8192)
        self.assertEqual(databases["default"]["OPTIONS"]["kdf_iter"], 512000)
        self.assertEqual(databases["default"]["OPTIONS"]["cipher_compatibility"], 4)

    def test_detects_plaintext_sqlite_database_files(self):
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "db.sqlite3"
            database_path.write_bytes(b"SQLite format 3\x00" + b"unused")

            self.assertTrue(_is_plaintext_sqlite_database(database_path))

    def test_plaintext_detector_ignores_missing_files(self):
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "missing.sqlite3"

            self.assertFalse(_is_plaintext_sqlite_database(database_path))

class EnvFileTests(SimpleTestCase):
    def test_env_example_contains_supported_settings_keys(self):
        values = parse_env_file(Path(".env.example"))

        expected_keys = {
            "DJANGO_SETTINGS_MODULE",
            "DJANGO_ENV_FILE",
            "DJANGO_ENV_EXAMPLE_FILE",
            "SECRET_KEY",
            "DEBUG",
            "ALLOWED_HOSTS",
            "DATABASE_NAME",
            "DATABASE_TIMEOUT",
            "DATABASE_ENCRYPTION_KEY",
            "DATABASE_CIPHER_PAGE_SIZE",
            "DATABASE_KDF_ITER",
            "DATABASE_CIPHER_COMPATIBILITY",
        }

        self.assertEqual(set(values), expected_keys)

    def test_parse_env_file_supports_comments_quotes_and_export(self):
        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "# comment",
                        "DATABASE_NAME=db.sqlite3",
                        "DATABASE_TIMEOUT='20.0'",
                        'export DEBUG="1"',
                        "DATABASE_ENCRYPTION_KEY=value#not-comment",
                        "DATABASE_CIPHER_PAGE_SIZE=4096 # comment",
                    ]
                ),
                encoding="utf-8",
            )

            values = parse_env_file(env_file)

        self.assertEqual(values["DATABASE_NAME"], "db.sqlite3")
        self.assertEqual(values["DATABASE_TIMEOUT"], "20.0")
        self.assertEqual(values["DEBUG"], "1")
        self.assertEqual(values["DATABASE_ENCRYPTION_KEY"], "value#not-comment")
        self.assertEqual(values["DATABASE_CIPHER_PAGE_SIZE"], "4096")

    def test_load_env_requires_env_to_match_example_keys(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / ".env.example").write_text("DATABASE_NAME=db.sqlite3\nDATABASE_TIMEOUT=20.0\n", encoding="utf-8")
            (base_dir / ".env").write_text("DATABASE_NAME=db.sqlite3\n", encoding="utf-8")

            with self.assertRaises(ImproperlyConfigured):
                load_env(base_dir)

    def test_load_env_sets_values_without_overriding_process_environment(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / ".env.example").write_text("DATABASE_NAME=db.sqlite3\nDATABASE_TIMEOUT=20.0\n", encoding="utf-8")
            (base_dir / ".env").write_text("DATABASE_NAME=from-file.sqlite3\nDATABASE_TIMEOUT=30.0\n", encoding="utf-8")

            with patch.dict("os.environ", {"DATABASE_NAME": "from-shell.sqlite3"}, clear=True):
                load_env(base_dir)

                self.assertEqual(os.environ["DATABASE_NAME"], "from-shell.sqlite3")
                self.assertEqual(os.environ["DATABASE_TIMEOUT"], "30.0")

    def test_load_env_allows_missing_env_file(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / ".env.example").write_text("DATABASE_NAME=db.sqlite3\n", encoding="utf-8")

            with patch.dict("os.environ", {}, clear=True):
                load_env(base_dir)

                self.assertNotIn("DATABASE_NAME", os.environ)


class BootstrapSecretsCommandTests(SimpleTestCase):
    def test_bootstrap_secrets_creates_env_with_generated_secrets(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            env_path = base_dir / ".env"

            call_command("bootstrap_secrets", env_file=str(env_path), yes=True)

            values = parse_env_file(env_path)

        self.assertNotEqual(values["DATABASE_ENCRYPTION_KEY"], "replace-with-a-strong-passphrase")
        self.assertGreaterEqual(len(values["DATABASE_ENCRYPTION_KEY"]), 48)
        self.assertNotEqual(values["SECRET_KEY"], "django-insecure-development-only-change-me")
        self.assertEqual(values["DATABASE_NAME"], DEFAULT_DATABASE_NAME)

    def test_bootstrap_secrets_preserves_existing_secrets(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            env_path = base_dir / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "DJANGO_SETTINGS_MODULE=config.settings",
                        "DJANGO_ENV_FILE=.env",
                        "DJANGO_ENV_EXAMPLE_FILE=.env.example",
                        "SECRET_KEY=existing-secret-key",
                        "DEBUG=1",
                        "ALLOWED_HOSTS=",
                        "DATABASE_NAME=db.sqlite3",
                        "DATABASE_TIMEOUT=20.0",
                        "DATABASE_ENCRYPTION_KEY=existing-db-key",
                        "DATABASE_CIPHER_PAGE_SIZE=4096",
                        "DATABASE_KDF_ITER=256000",
                        "DATABASE_CIPHER_COMPATIBILITY=4",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            call_command("bootstrap_secrets", env_file=str(env_path), yes=True)

            values = parse_env_file(env_path)

        self.assertEqual(values["DATABASE_ENCRYPTION_KEY"], "existing-db-key")
        self.assertEqual(values["SECRET_KEY"], "existing-secret-key")

    def test_bootstrap_secrets_aborts_before_rewriting_existing_env_without_confirmation(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            env_path = base_dir / ".env"
            original_content = "DATABASE_ENCRYPTION_KEY=existing-db-key\nSECRET_KEY=existing-secret-key\n"
            env_path.write_text(original_content, encoding="utf-8")

            with patch("builtins.input", return_value="no"):
                with self.assertRaises(CommandError):
                    call_command("bootstrap_secrets", env_file=str(env_path))

            self.assertEqual(env_path.read_text(encoding="utf-8"), original_content)

    def test_bootstrap_secrets_rotates_existing_secrets_with_confirmation(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            env_path = base_dir / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "DJANGO_SETTINGS_MODULE=config.settings",
                        "DJANGO_ENV_FILE=.env",
                        "DJANGO_ENV_EXAMPLE_FILE=.env.example",
                        "SECRET_KEY=existing-secret-key",
                        "DEBUG=1",
                        "ALLOWED_HOSTS=",
                        "DATABASE_NAME=db.sqlite3",
                        "DATABASE_TIMEOUT=20.0",
                        "DATABASE_ENCRYPTION_KEY=existing-db-key",
                        "DATABASE_CIPHER_PAGE_SIZE=4096",
                        "DATABASE_KDF_ITER=256000",
                        "DATABASE_CIPHER_COMPATIBILITY=4",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("builtins.input", return_value="yes"):
                call_command("bootstrap_secrets", env_file=str(env_path), rotate=True)

            values = parse_env_file(env_path)

        self.assertNotEqual(values["DATABASE_ENCRYPTION_KEY"], "existing-db-key")
        self.assertNotEqual(values["SECRET_KEY"], "existing-secret-key")


class LoginRateLimitTests(SimpleTestCase):
    def test_login_blocks_when_username_has_too_many_failures(self):
        request = RequestFactory().post("/admin/login/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        username_key = _cache_key("login-failures:username", "owner")
        client_key = _cache_key("login-failures:client", "127.0.0.1")

        with override_settings(
            HOLYFHIR_LOGIN_MAX_ATTEMPTS_PER_USERNAME=1,
            HOLYFHIR_LOGIN_MAX_ATTEMPTS_PER_CLIENT=20,
            HOLYFHIR_LOGIN_LOCKOUT_SECONDS=60,
        ), patch("django.contrib.auth.forms.authenticate", return_value=None):
            form = RateLimitedAdminAuthenticationForm(
                request=request,
                data={"username": "owner", "password": "wrong-password"},
            )
            self.assertFalse(form.is_valid())

            form = RateLimitedAdminAuthenticationForm(
                request=request,
                data={"username": "owner", "password": "another-wrong-password"},
            )
            self.assertFalse(form.is_valid())

        self.assertIn("Too many failed login attempts.", form.errors["__all__"][0])

        from django.core.cache import cache

        cache.delete(username_key)
        cache.delete(client_key)
