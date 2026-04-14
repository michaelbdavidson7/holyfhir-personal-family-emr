import warnings
from itertools import tee
from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3.base import FORMAT_QMARK_REGEX
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.base import register_functions

from config.sqlcipher import get_sqlcipher_dbapi


def _sql_quote(value):
    return str(value).replace("'", "''")


class DatabaseWrapper(SQLiteDatabaseWrapper):
    vendor = "sqlite"
    display_name = "SQLCipher"

    def get_connection_params(self):
        database = get_sqlcipher_dbapi()

        settings_dict = self.settings_dict
        if not settings_dict["NAME"]:
            raise ImproperlyConfigured(
                "settings.DATABASES is improperly configured. Please supply the NAME value."
            )

        options = dict(settings_dict.get("OPTIONS", {}))
        kwargs = {
            "database": settings_dict["NAME"],
            "detect_types": database.PARSE_DECLTYPES | database.PARSE_COLNAMES,
            **options,
        }

        if "check_same_thread" in kwargs and kwargs["check_same_thread"]:
            warnings.warn(
                "The `check_same_thread` option was provided and set to True. "
                "It will be overridden with False. Use the "
                "`DatabaseWrapper.allow_thread_sharing` property instead.",
                RuntimeWarning,
            )

        kwargs.update({"check_same_thread": False, "uri": True})
        return kwargs

    def get_new_connection(self, conn_params):
        database = get_sqlcipher_dbapi()
        passphrase = conn_params.pop("passphrase", None)
        cipher_page_size = conn_params.pop("cipher_page_size", None)
        kdf_iter = conn_params.pop("kdf_iter", None)
        cipher_compatibility = conn_params.pop("cipher_compatibility", None)

        conn = database.connect(**conn_params)

        if passphrase:
            conn.execute(f"PRAGMA key = '{_sql_quote(passphrase)}'")
            if cipher_compatibility:
                conn.execute(f"PRAGMA cipher_compatibility = {int(cipher_compatibility)}")
            if cipher_page_size:
                conn.execute(f"PRAGMA cipher_page_size = {int(cipher_page_size)}")
            if kdf_iter:
                conn.execute(f"PRAGMA kdf_iter = {int(kdf_iter)}")

            # Force an initial page read so invalid keys fail fast.
            conn.execute("SELECT count(*) FROM sqlite_master")

        register_functions(conn)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA legacy_alter_table = OFF")
        return conn

    def create_cursor(self, name=None):
        return SQLiteCursorWrapper(self.connection.cursor())


class SQLiteCursorWrapper:
    """
    Mirror Django's SQLite placeholder conversion, but for SQLCipher cursors.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        if params is None:
            return self.cursor.execute(query)
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
        return self.cursor.execute(query, params)

    def executemany(self, query, param_list):
        peekable, param_list = tee(iter(param_list))
        if (params := next(peekable, None)) and isinstance(params, Mapping):
            param_names = list(params)
        else:
            param_names = None
        query = self.convert_query(query, param_names=param_names)
        return self.cursor.executemany(query, param_list)

    def convert_query(self, query, *, param_names=None):
        if param_names is None:
            return FORMAT_QMARK_REGEX.sub("?", query).replace("%%", "%")
        return query % {name: f":{name}" for name in param_names}

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __enter__(self):
        self.cursor.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.cursor.__exit__(exc_type, exc_value, traceback)
