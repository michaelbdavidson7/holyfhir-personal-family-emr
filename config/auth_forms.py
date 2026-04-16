import hashlib

from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def _cache_key(prefix, value):
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return f"holyfhir:{prefix}:{digest}"


def _client_identifier(request):
    if request is None:
        return "unknown"

    return request.META.get("REMOTE_ADDR", "unknown")


def _increment_failure(key, timeout):
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout)
    return attempts


class RateLimitedAdminAuthenticationForm(AdminAuthenticationForm):
    """
    Adds local brute-force protection to Django Admin login.

    This is intentionally cache-backed and local-first. It slows password guessing
    in the desktop app without introducing accounts, email, SMS, or cloud recovery.
    """

    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "locked": _(
            "Too many failed login attempts. Wait a few minutes and try again."
        ),
    }

    def clean(self):
        username = self.cleaned_data.get("username", "")
        client = _client_identifier(self.request)
        timeout = settings.HOLYFHIR_LOGIN_LOCKOUT_SECONDS
        username_limit = settings.HOLYFHIR_LOGIN_MAX_ATTEMPTS_PER_USERNAME
        client_limit = settings.HOLYFHIR_LOGIN_MAX_ATTEMPTS_PER_CLIENT

        username_key = _cache_key("login-failures:username", username.lower())
        client_key = _cache_key("login-failures:client", client)

        if cache.get(username_key, 0) >= username_limit:
            raise ValidationError(
                self.error_messages["locked"],
                code="locked",
            )

        if cache.get(client_key, 0) >= client_limit:
            raise ValidationError(
                self.error_messages["locked"],
                code="locked",
            )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            _increment_failure(username_key, timeout)
            _increment_failure(client_key, timeout)
            raise

        cache.delete(username_key)
        cache.delete(client_key)
        return cleaned_data
