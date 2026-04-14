import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.database import (
    DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
    DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
    DEFAULT_DATABASE_KDF_ITER,
    DEFAULT_DATABASE_TIMEOUT,
    build_default_database_config,
)
from config.env import load_env, parse_env_file


class DatabaseConfigTests(SimpleTestCase):
    def test_defaults_to_plain_sqlite_when_no_key_is_set(self):
        with patch.dict("os.environ", {}, clear=True):
            databases = build_default_database_config(Path("/tmp/personal-emr"))

        self.assertEqual(databases["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(databases["default"]["NAME"], str(Path("/tmp/personal-emr") / "db.sqlite3"))
        self.assertEqual(databases["default"]["OPTIONS"]["timeout"], DEFAULT_DATABASE_TIMEOUT)

    def test_switches_to_sqlcipher_when_key_is_present(self):
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

    def test_can_require_encryption_key(self):
        with patch.dict("os.environ", {"DATABASE_ENCRYPTION_REQUIRED": "1"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_default_database_config(Path("/tmp/personal-emr"))


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
            "DATABASE_ENCRYPTION_REQUIRED",
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
                        'export DATABASE_ENCRYPTION_REQUIRED="0"',
                        "DATABASE_ENCRYPTION_KEY=value#not-comment",
                        "DATABASE_CIPHER_PAGE_SIZE=4096 # comment",
                    ]
                ),
                encoding="utf-8",
            )

            values = parse_env_file(env_file)

        self.assertEqual(values["DATABASE_NAME"], "db.sqlite3")
        self.assertEqual(values["DATABASE_TIMEOUT"], "20.0")
        self.assertEqual(values["DATABASE_ENCRYPTION_REQUIRED"], "0")
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
