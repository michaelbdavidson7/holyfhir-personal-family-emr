import shutil
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.utils import timezone


@dataclass(frozen=True)
class DatabaseBackup:
    path: Path
    name: str
    size_bytes: int
    created_at: object


def database_path():
    database_name = settings.DATABASES["default"].get("NAME", "")
    if not database_name or database_name == ":memory:":
        return None
    return Path(database_name)


def fhir_import_backup_dir():
    path = database_path()
    if path is None:
        return None
    return path.parent / "backups" / "fhir-imports"


def list_fhir_import_database_backups():
    backup_dir = fhir_import_backup_dir()
    if backup_dir is None or not backup_dir.exists():
        return []

    backups = []
    for path in backup_dir.glob("*.pre-fhir-import.*"):
        if not path.is_file():
            continue
        stat = path.stat()
        backups.append(
            DatabaseBackup(
                path=path,
                name=path.name,
                size_bytes=stat.st_size,
                created_at=timezone.datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone()),
            )
        )

    return sorted(backups, key=lambda backup: backup.name, reverse=True)


def create_pre_import_database_backup():
    path = database_path()
    if path is None or not path.exists() or not path.is_file():
        return None

    backup_dir = fhir_import_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}.pre-fhir-import.{timestamp}{path.suffix}"

    connections["default"].close()
    shutil.copy2(path, backup_path)
    return backup_path
