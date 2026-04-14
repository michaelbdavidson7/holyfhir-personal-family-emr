from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.database import build_default_database_config


class DatabaseConfigTests(SimpleTestCase):
    def test_defaults_to_plain_sqlite_when_no_key_is_set(self):
        with patch.dict("os.environ", {}, clear=True):
            databases = build_default_database_config(Path("/tmp/personal-emr"))

        self.assertEqual(databases["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(databases["default"]["NAME"], str(Path("/tmp/personal-emr") / "db.sqlite3"))
        self.assertNotIn("OPTIONS", databases["default"])

    def test_switches_to_sqlcipher_when_key_is_present(self):
        with patch.dict(
            "os.environ",
            {
                "DATABASE_ENCRYPTION_KEY": "super-secret",
                "DATABASE_CIPHER_PAGE_SIZE": "4096",
                "DATABASE_KDF_ITER": "256000",
            },
            clear=True,
        ):
            databases = build_default_database_config(Path("/tmp/personal-emr"))

        self.assertEqual(databases["default"]["ENGINE"], "config.db.backends.sqlcipher")
        self.assertEqual(databases["default"]["OPTIONS"]["passphrase"], "super-secret")
        self.assertEqual(databases["default"]["OPTIONS"]["cipher_page_size"], 4096)
        self.assertEqual(databases["default"]["OPTIONS"]["kdf_iter"], 256000)

    def test_can_require_encryption_key(self):
        with patch.dict("os.environ", {"DATABASE_ENCRYPTION_REQUIRED": "1"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_default_database_config(Path("/tmp/personal-emr"))
