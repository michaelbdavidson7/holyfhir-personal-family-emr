from django.core.exceptions import ImproperlyConfigured


def get_sqlcipher_dbapi():
    try:
        import sqlcipher3 as database

        return database
    except ImportError:
        pass

    try:
        from pysqlcipher3 import dbapi2 as database

        return database
    except ImportError as exc:
        raise ImproperlyConfigured(
            "Database encryption requires a SQLCipher-compatible Python driver. "
            "Install `sqlcipher3` (recommended) or `pysqlcipher3` (legacy fallback)."
        ) from exc
