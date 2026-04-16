from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import SystemSettings


class AppLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            timezone.activate(SystemSettings.get_solo().time_zone)

        if self._should_redirect_to_unlock(request):
            request.session["unlock_next"] = request.get_full_path()
            return redirect("app_unlock")

        return self.get_response(request)

    def _should_redirect_to_unlock(self, request):
        if not request.user.is_authenticated:
            return False

        if not request.session.get("app_locked"):
            return False

        allowed_paths = {
            reverse("app_unlock"),
            reverse("admin:logout"),
        }

        return request.path not in allowed_paths and not request.path.startswith("/static/")
