import shutil
from datetime import datetime
from pathlib import Path


def backup_existing_file(path):
    path = Path(path)
    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.backup.{timestamp}")
    counter = 2

    while backup_path.exists():
        backup_path = path.with_name(f"{path.name}.backup.{timestamp}.{counter}")
        counter += 1

    shutil.copy2(path, backup_path)
    return backup_path
