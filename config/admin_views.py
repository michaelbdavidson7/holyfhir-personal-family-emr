from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from clinical.models import (
    AdverseEvent,
    Allergy,
    BodyStructure,
    CarePlan,
    CareTeam,
    ClinicalImpression,
    Condition,
    DetectedIssue,
    Device,
    DeviceRequest,
    DeviceUseStatement,
    DiagnosticReport,
    Encounter,
    EpisodeOfCare,
    FamilyMemberHistory,
    FHIRGroup,
    FHIRList,
    Flag,
    Goal,
    Immunization,
    ImmunizationRecommendation,
    Location,
    Medication,
    MedicationAdministration,
    MedicationCatalog,
    MedicationDispense,
    NutritionOrder,
    Observation,
    Organization,
    Person,
    Practitioner,
    PractitionerRole,
    Procedure,
    RelatedPerson,
    RiskAssessment,
    ServiceRequest,
    Specimen,
    Communication,
    CommunicationRequest,
    QuestionnaireResponse,
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
                    "title": "Adverse Events",
                    "description": "Actual or potential harm events, contributors, outcomes, and suspect entities.",
                    "url": reverse("admin:clinical_adverseevent_changelist"),
                    "icon": "fas fa-exclamation-circle",
                    "count": AdverseEvent.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Family History",
                    "description": "Family member relationships, conditions, outcomes, and notes.",
                    "url": reverse("admin:clinical_familymemberhistory_changelist"),
                    "icon": "fas fa-people-arrows",
                    "count": FamilyMemberHistory.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Related People",
                    "description": "Personal contacts involved with a patient, such as family, guardians, or caregivers.",
                    "url": reverse("admin:clinical_relatedperson_changelist"),
                    "icon": "fas fa-address-book",
                    "count": RelatedPerson.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "People",
                    "description": "Shared identity records linking patients, practitioners, and related people.",
                    "url": reverse("admin:clinical_person_changelist"),
                    "icon": "fas fa-user-circle",
                    "count": Person.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Clinical Impressions",
                    "description": "Clinical assessments, summaries, findings, and supporting investigations.",
                    "url": reverse("admin:clinical_clinicalimpression_changelist"),
                    "icon": "fas fa-notes-medical",
                    "count": ClinicalImpression.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Detected Issues",
                    "description": "Clinical safety or quality issues such as interactions and duplicate therapy.",
                    "url": reverse("admin:clinical_detectedissue_changelist"),
                    "icon": "fas fa-shield-alt",
                    "count": DetectedIssue.objects.count(),
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
                    "title": "Medication Catalog",
                    "description": "Standalone FHIR Medication definitions used by orders, dispenses, and administrations.",
                    "url": reverse("admin:clinical_medicationcatalog_changelist"),
                    "icon": "fas fa-capsules",
                    "count": MedicationCatalog.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Medication Administrations",
                    "description": "Medication events where a dose was administered to a patient.",
                    "url": reverse("admin:clinical_medicationadministration_changelist"),
                    "icon": "fas fa-prescription-bottle",
                    "count": MedicationAdministration.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Medication Dispenses",
                    "description": "Pharmacy or supply events where medication was dispensed.",
                    "url": reverse("admin:clinical_medicationdispense_changelist"),
                    "icon": "fas fa-prescription-bottle-alt",
                    "count": MedicationDispense.objects.count(),
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
                    "title": "Immunization Recommendations",
                    "description": "Vaccine forecasts, recommended timing, and supporting immunization history.",
                    "url": reverse("admin:clinical_immunizationrecommendation_changelist"),
                    "icon": "fas fa-calendar-check",
                    "count": ImmunizationRecommendation.objects.count(),
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
                    "title": "Diagnostic Reports",
                    "description": "Lab, pathology, imaging, and diagnostic reports with results and specimens.",
                    "url": reverse("admin:clinical_diagnosticreport_changelist"),
                    "icon": "fas fa-file-medical-alt",
                    "count": DiagnosticReport.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Flags",
                    "description": "Patient alerts, warnings, and awareness notes.",
                    "url": reverse("admin:clinical_flag_changelist"),
                    "icon": "fas fa-flag",
                    "count": Flag.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Communications",
                    "description": "Messages or information sent between people, organizations, and patients.",
                    "url": reverse("admin:clinical_communication_changelist"),
                    "icon": "fas fa-comments",
                    "count": Communication.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Questionnaire Responses",
                    "description": "Completed forms, assessments, and patient-entered answers.",
                    "url": reverse("admin:clinical_questionnaireresponse_changelist"),
                    "icon": "fas fa-clipboard-list",
                    "count": QuestionnaireResponse.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "FHIR Lists",
                    "description": "Curated FHIR lists of problems, medications, results, or other records.",
                    "url": reverse("admin:clinical_fhirlist_changelist"),
                    "icon": "fas fa-list",
                    "count": FHIRList.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Risk Assessments",
                    "description": "Clinical risk estimates, predictions, basis records, and mitigation notes.",
                    "url": reverse("admin:clinical_riskassessment_changelist"),
                    "icon": "fas fa-chart-pie",
                    "count": RiskAssessment.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Body Structures",
                    "description": "Anatomical locations, morphology, qualifiers, and body-site descriptions.",
                    "url": reverse("admin:clinical_bodystructure_changelist"),
                    "icon": "fas fa-diagnoses",
                    "count": BodyStructure.objects.count(),
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
                {
                    "title": "Devices",
                    "description": "Patient devices, implanted devices, owners, locations, and identifiers.",
                    "url": reverse("admin:clinical_device_changelist"),
                    "icon": "fas fa-laptop-medical",
                    "count": Device.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Device Use",
                    "description": "Statements that a patient uses or used a device.",
                    "url": reverse("admin:clinical_deviceusestatement_changelist"),
                    "icon": "fas fa-notes-medical",
                    "count": DeviceUseStatement.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Groups",
                    "description": "FHIR groups of people, practitioners, devices, medications, or other groups.",
                    "url": reverse("admin:clinical_fhirgroup_changelist"),
                    "icon": "fas fa-layer-group",
                    "count": FHIRGroup.objects.count(),
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
                    "title": "Service Requests",
                    "description": "Orders, referrals, requested services, performers, reasons, and specimens.",
                    "url": reverse("admin:clinical_servicerequest_changelist"),
                    "icon": "fas fa-tasks",
                    "count": ServiceRequest.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Communication Requests",
                    "description": "Requests to convey information to specific recipients.",
                    "url": reverse("admin:clinical_communicationrequest_changelist"),
                    "icon": "fas fa-paper-plane",
                    "count": CommunicationRequest.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Nutrition Orders",
                    "description": "Diet, supplement, oral, and enteral nutrition orders.",
                    "url": reverse("admin:clinical_nutritionorder_changelist"),
                    "icon": "fas fa-utensils",
                    "count": NutritionOrder.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Goals",
                    "description": "Care goals, addressed concerns, targets, outcomes, and status.",
                    "url": reverse("admin:clinical_goal_changelist"),
                    "icon": "fas fa-bullseye",
                    "count": Goal.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Device Requests",
                    "description": "Orders and requests for devices, performers, reasons, and timing.",
                    "url": reverse("admin:clinical_devicerequest_changelist"),
                    "icon": "fas fa-toolbox",
                    "count": DeviceRequest.objects.count(),
                    "count_label": "record",
                },
                {
                    "title": "Episodes of Care",
                    "description": "Care responsibility intervals, care managers, teams, and referral requests.",
                    "url": reverse("admin:clinical_episodeofcare_changelist"),
                    "icon": "fas fa-project-diagram",
                    "count": EpisodeOfCare.objects.count(),
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
                    "title": "Practitioner Roles",
                    "description": "Practitioner roles by organization, specialty, dates, and locations.",
                    "url": reverse("admin:clinical_practitionerrole_changelist"),
                    "icon": "fas fa-id-badge",
                    "count": PractitionerRole.objects.count(),
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
