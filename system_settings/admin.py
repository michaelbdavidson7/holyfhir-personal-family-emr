from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Lock screen", {
            "fields": ("lock_shortcut_enabled",),
            "description": "Manual Lock app is always available from the account menu. The keyboard shortcut is opt in.",
        }),
        ("Meta", {
            "fields": ("updated_at",),
        }),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
