from django.core.management.base import BaseCommand

from patients.models import LoginLockout


class Command(BaseCommand):
    help = "Clear local HolyFHIR login lockout counters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clear all local cache entries. Use this for the default locmem cache.",
        )

    def handle(self, *args, **options):
        deleted_count, _ = LoginLockout.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Cleared {deleted_count} local login lockout counter(s)."
            )
        )
