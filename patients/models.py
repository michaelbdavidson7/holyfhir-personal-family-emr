from django.db import models
from django.conf import settings
from django.utils import timezone


class PatientProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    sex_at_birth = models.CharField(max_length=20, blank=True)
    gender_identity = models.CharField(max_length=50, blank=True)

    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="USA")

    blood_type = models.CharField(max_length=10, blank=True)
    organ_donor = models.BooleanField(default=False)

    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class LoginLockout(models.Model):
    SCOPE_USERNAME = "username"
    SCOPE_CLIENT = "client"

    SCOPE_CHOICES = (
        (SCOPE_USERNAME, "Username"),
        (SCOPE_CLIENT, "Client"),
    )

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    key = models.CharField(max_length=64)
    failure_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scope", "key"], name="unique_login_lockout_scope_key"),
        ]
        verbose_name = "Login Lockout"
        verbose_name_plural = "Login Lockouts"

    def is_locked(self):
        return self.locked_until is not None and self.locked_until > timezone.now()

    def __str__(self):
        return f"{self.scope}:{self.key}"


class RecoveryCredential(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recovery_credential",
    )
    recovery_key_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Recovery Credential"
        verbose_name_plural = "Recovery Credentials"

    def __str__(self):
        return f"Recovery credential for {self.user}"
