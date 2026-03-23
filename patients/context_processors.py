from .models import PatientProfile


def admin_recent_patients(request):
    if not request.path.startswith("/admin"):
        return {}

    return {
        "recent_patients": PatientProfile.objects.order_by("-updated_at")[:8]
    }