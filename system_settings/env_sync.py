import os
from pathlib import Path

from django.conf import settings

from config.file_backups import backup_existing_file


def _env_path():
    env_file = os.getenv("DJANGO_ENV_FILE", ".env")
    path = Path(env_file)
    if path.is_absolute():
        return path
    return Path(settings.BASE_DIR) / path


def _quote_env_value(value):
    escaped_value = value.replace('"', '\\"')
    if any(char.isspace() for char in value) or "#" in value:
        return f'"{escaped_value}"'
    return value


def update_env_value(key, value):
    path = _env_path()
    if not path.exists():
        return False

    replacement = f"{key}={_quote_env_value(value)}"
    lines = path.read_text(encoding="utf-8").splitlines()
    replaced = False
    updated_lines = []

    for line in lines:
        stripped = line.strip()
        prefix = "export " if stripped.startswith("export ") else ""
        comparable = stripped[7:].lstrip() if prefix else stripped

        if comparable.startswith(f"{key}="):
            updated_lines.append(f"{prefix}{replacement}")
            replaced = True
        else:
            updated_lines.append(line)

    if not replaced:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append(replacement)

    backup_existing_file(path)
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    os.environ[key] = value
    return True
