from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from patients.models import RecoveryCredential
from patients.recovery import generate_recovery_key, hash_recovery_key
from system_settings.models import SystemSettings


def settings_hub(request):
    system_settings = SystemSettings.get_solo()
    recovery_credential = None

    if request.user.is_authenticated:
        recovery_credential = RecoveryCredential.objects.filter(user=request.user).first()

    if recovery_credential:
        recovery_status = {
            "configured": True,
            "message": "Configured",
            "detail": "A recovery key hash exists for this system user.",
            "created_at": recovery_credential.created_at,
            "last_used_at": recovery_credential.last_used_at,
        }
    else:
        recovery_status = {
            "configured": False,
            "message": "Not configured",
            "detail": "No recovery key has been created for this system user yet.",
            "created_at": None,
            "last_used_at": None,
        }

    cards = [
        {
            "title": "App Settings",
            "description": f"Manage local time, lock-screen behavior, and desktop preferences. Current time zone: {system_settings.time_zone}.",
            "url": reverse("admin:system_settings_systemsettings_change", args=[system_settings.pk]),
            "icon": "fas fa-sliders-h",
        },
        {
            "title": "Users",
            "description": "Manage the local system owner account and password.",
            "url": reverse("admin:auth_user_changelist"),
            "icon": "fas fa-user",
        },
        {
            "title": "Groups",
            "description": "Advanced Django permission groups.",
            "url": reverse("admin:auth_group_changelist"),
            "icon": "fas fa-users",
        },
        {
            "title": "Recovery Keys",
            "description": "View recovery-key status and stored hashes.",
            "url": reverse("admin:patients_recoverycredential_changelist"),
            "icon": "fas fa-key",
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Settings",
        "settings_cards": cards,
        "recovery_status": recovery_status,
        "recovery_key_action_url": reverse("admin_recovery_key_generate"),
    }
    return render(request, "admin/settings_hub.html", context)


def recovery_key_generate(request):
    if not request.user.is_authenticated:
        return redirect("admin:login")

    credential = RecoveryCredential.objects.filter(user=request.user).first()

    if request.method == "POST":
        recovery_key = generate_recovery_key()
        RecoveryCredential.objects.update_or_create(
            user=request.user,
            defaults={"recovery_key_hash": hash_recovery_key(recovery_key)},
        )

        messages.warning(
            request,
            "Save this recovery key now. HolyFHIR cannot show it again.",
        )
        return render(
            request,
            "admin/recovery_key_generated.html",
            {
                **admin.site.each_context(request),
                "title": "Recovery Key Generated",
                "recovery_key": recovery_key,
            },
        )

    context = {
        **admin.site.each_context(request),
        "title": "Generate Recovery Key",
        "has_existing_key": credential is not None,
    }
    return render(request, "admin/recovery_key_generate_confirm.html", context)


def fhir_interop_hub(request):
    cards = [
        {
            "title": "FHIR Links",
            "description": "Review connections between local records and FHIR resources.",
            "url": reverse("admin:fhir_fhirlink_changelist"),
            "icon": "fas fa-link",
        },
        {
            "title": "FHIR Resource Snapshots",
            "description": "Inspect imported raw FHIR resources kept for traceability.",
            "url": reverse("admin:fhir_fhirresourcesnapshot_changelist"),
            "icon": "fas fa-database",
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "FHIR / Interop",
        "interop_cards": cards,
    }
    return render(request, "admin/fhir_interop_hub.html", context)
