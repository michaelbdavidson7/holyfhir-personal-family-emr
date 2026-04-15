import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="HolyFHIRBackend",
        description="Bundled Django command runner for HolyFHIR Personal EMR.",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to the bundled Django project root.",
    )
    parser.add_argument("django_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.argv = ["manage.py", *args.django_args]

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
