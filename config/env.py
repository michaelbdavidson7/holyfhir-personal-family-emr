import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def _strip_inline_comment(value):
    in_single_quote = False
    in_double_quote = False

    for index, char in enumerate(value):
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif (
            char == "#"
            and not in_single_quote
            and not in_double_quote
            and (index == 0 or value[index - 1].isspace())
        ):
            return value[:index].rstrip()

    return value


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_file(path: Path):
    values = {}

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            raise ImproperlyConfigured(f"Invalid environment line in {path} at line {line_number}: expected KEY=VALUE.")

        key, value = line.split("=", 1)
        key = key.strip()

        if not key:
            raise ImproperlyConfigured(f"Invalid environment line in {path} at line {line_number}: key is empty.")

        values[key] = _unquote(_strip_inline_comment(value.strip()))

    return values


def _resolve_env_path(base_dir: Path, file_name):
    path = Path(file_name)
    if path.is_absolute():
        return path
    return base_dir / path


def load_env(base_dir: Path, env_file_name=".env", example_file_name=".env.example"):
    env_path = _resolve_env_path(base_dir, env_file_name)
    example_path = _resolve_env_path(base_dir, example_file_name)

    if not example_path.exists():
        raise ImproperlyConfigured(f"Missing environment example file: {example_path}")

    example_values = parse_env_file(example_path)
    required_keys = set(example_values)

    if not env_path.exists():
        return

    env_values = parse_env_file(env_path)
    missing_keys = sorted(key for key in required_keys - set(env_values) if not os.getenv(key))

    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ImproperlyConfigured(f"{env_path} is missing required key(s) from {example_path}: {missing}")

    for key, value in env_values.items():
        os.environ.setdefault(key, value)
