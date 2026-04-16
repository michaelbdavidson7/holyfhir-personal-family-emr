from django.db import models


class SystemSettings(models.Model):
    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    lock_shortcut_enabled = models.BooleanField(
        default=False,
        help_text="Allow Ctrl+Shift+L to lock the desktop app.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "System Settings"

    def save(self, *args, **kwargs):
        self.singleton_id = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(singleton_id=1)
        return settings
