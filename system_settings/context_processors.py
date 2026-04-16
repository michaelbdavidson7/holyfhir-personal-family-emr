from .models import SystemSettings


def system_settings(request):
    try:
        settings = SystemSettings.get_solo()
    except Exception:
        settings = None

    return {
        "holyfhir_system_settings": settings,
        "holyfhir_lock_shortcut_enabled": bool(settings and settings.lock_shortcut_enabled),
    }
