from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from clinical.models import (
    Allergy,
    CarePlan,
    CareTeam,
    Condition,
    Encounter,
    Immunization,
    Location,
    Medication,
    Observation,
    Organization,
    Practitioner,
    Procedure,
    Specimen,
)
from fhir.backups import database_path, fhir_import_backup_dir, list_fhir_import_database_backups
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
        {
            "title": "Backups",
            "description": "Find FHIR pre-import database backups and review the manual restore steps.",
            "url": reverse("admin_backups"),
            "icon": "fas fa-archive",
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


def backups_hub(request):
    context = {
        **admin.site.each_context(request),
        "title": "Backups",
        "database_path": database_path(),
        "backup_dir": fhir_import_backup_dir(),
        "backups": list_fhir_import_database_backups(),
    }
    return render(request, "admin/backups_hub.html", context)


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


def clinical_care_team_directory(request):
    cards = [
        {
            "title": "Care Teams",
            "description": "Manage patient care-team records imported from FHIR or entered locally.",
            "url": reverse("admin:clinical_careteam_changelist"),
            "icon": "fas fa-user-friends",
            "count": CareTeam.objects.count(),
            "count_label": "managed record",
        },
        {
            "title": "Practitioners",
            "description": "Manage clinicians and other people involved in care.",
            "url": reverse("admin:clinical_practitioner_changelist"),
            "icon": "fas fa-user-md",
            "count": Practitioner.objects.count(),
            "count_label": "managed record",
        },
        {
            "title": "Organizations",
            "description": "Manage facilities, practices, departments, and other care organizations.",
            "url": reverse("admin:clinical_organization_changelist"),
            "icon": "fas fa-hospital",
            "count": Organization.objects.count(),
            "count_label": "managed record",
        },
        {
            "title": "Locations",
            "description": "Manage clinics, hospitals, rooms, and other care sites.",
            "url": reverse("admin:clinical_location_changelist"),
            "icon": "fas fa-map-marker-alt",
            "count": Location.objects.count(),
            "count_label": "managed record",
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Care Team",
        "directory_cards": cards,
    }
    return render(request, "admin/clinical_care_team_directory.html", context)


def clinical_resources_directory(request):
    sections = [
        {
            "title": "Patient Records",
            "cards": [
                {
                    "title": "Conditions",
                    "description": "Problems, diagnoses, and active or historical conditions.",
                    "url": reverse("admin:clinical_condition_changelist"),
                    "icon": "fas fa-heartbeat",
                    "count": Condition.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Allergies",
                    "description": "Allergies, intolerances, reactions, and severity details.",
                    "url": reverse("admin:clinical_allergy_changelist"),
                    "icon": "fas fa-exclamation-triangle",
                    "count": Allergy.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Medications",
                    "description": "Medication requests, statements, dosage text, and status.",
                    "url": reverse("admin:clinical_medication_changelist"),
                    "icon": "fas fa-pills",
                    "count": Medication.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Immunizations",
                    "description": "Vaccines, occurrence dates, lot numbers, and performers.",
                    "url": reverse("admin:clinical_immunization_changelist"),
                    "icon": "fas fa-syringe",
                    "count": Immunization.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Vitals & Labs",
                    "description": "Observations, vital signs, lab values, and specimen links.",
                    "url": reverse("admin:clinical_observation_changelist"),
                    "icon": "fas fa-chart-line",
                    "count": Observation.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Visits & Actions",
                    "description": "Encounters, visits, facilities, provider text, and summaries.",
                    "url": reverse("admin:clinical_encounter_changelist"),
                    "icon": "fas fa-stethoscope",
                    "count": Encounter.objects.count(),
                    "count_label": "record",
                },
            ],
        },
        {
            "title": "Care Planning",
            "cards": [
                {
                    "title": "Care Teams",
                    "description": "Patient care-team records and structured participants.",
                    "url": reverse("admin:clinical_careteam_changelist"),
                    "icon": "fas fa-user-friends",
                    "count": CareTeam.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Care Plans",
                    "description": "Care plans connected to conditions and care teams.",
                    "url": reverse("admin:clinical_careplan_changelist"),
                    "icon": "fas fa-clipboard-list",
                    "count": CarePlan.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Procedures",
                    "description": "Completed procedures, actions, performers, and reasons.",
                    "url": reverse("admin:clinical_procedure_changelist"),
                    "icon": "fas fa-procedures",
                    "count": Procedure.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Specimens",
                    "description": "Lab specimens, collection details, and parent specimens.",
                    "url": reverse("admin:clinical_specimen_changelist"),
                    "icon": "fas fa-vial",
                    "count": Specimen.objects.count(),
                    "count_label": "record",
                },
            ],
        },
        {
            "title": "Directory",
            "cards": [
                {
                    "title": "Practitioners",
                    "description": "Clinicians and other people involved in care.",
                    "url": reverse("admin:clinical_practitioner_changelist"),
                    "icon": "fas fa-user-md",
                    "count": Practitioner.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Organizations",
                    "description": "Facilities, practices, departments, and care organizations.",
                    "url": reverse("admin:clinical_organization_changelist"),
                    "icon": "fas fa-hospital",
                    "count": Organization.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Locations",
                    "description": "Clinics, hospitals, rooms, and care sites.",
                    "url": reverse("admin:clinical_location_changelist"),
                    "icon": "fas fa-map-marker-alt",
                    "count": Location.objects.count(),
                    "count_label": "record",
                },
            ],
        },
    ]

    context = {
        **admin.site.each_context(request),
        "title": "Clinical Resources",
        "directory_sections": sections,
    }
    return render(request, "admin/clinical_resources_directory.html", context)


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
