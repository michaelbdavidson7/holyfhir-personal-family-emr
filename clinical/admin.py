from django import forms
from django.contrib import admin
from django.db import models
from .models import (
    AdverseEvent,
    Allergy,
    CarePlan,
    CareTeam,
    CareTeamParticipant,
    ClinicalImpression,
    ClinicalImpressionFinding,
    Condition,
    DetectedIssue,
    Device,
    DiagnosticReport,
    Encounter,
    EpisodeOfCare,
    FamilyMemberHistory,
    FamilyMemberHistoryCondition,
    FHIRGroup,
    FHIRGroupMember,
    Immunization,
    Location,
    Medication,
    Observation,
    Organization,
    Person,
    PersonLink,
    Practitioner,
    PractitionerRole,
    Procedure,
    ProcedurePerformer,
    RelatedPerson,
    ServiceRequest,
    Specimen,
)


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "clinical_status", "onset_date")
    list_display_links = ("name",)
    search_fields = ("name", "icd10_code", "snomed_code")
    list_filter = ("patient", "clinical_status")
    autocomplete_fields = ["patient"]
    ordering = ("-onset_date",)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "substance", "category", "severity")
    list_display_links = ("substance",)
    search_fields = ("substance", "rxnorm_code", "snomed_code")
    list_filter = ("patient", "category", "severity", "criticality")
    autocomplete_fields = ["patient"]


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "status", "indication", "start_date")
    list_display_links = ("name",)
    search_fields = ("name", "rxnorm_code", "prescriber")
    list_filter = ("patient", "status")
    ordering = ("-start_date",)
    autocomplete_fields = ["patient"]


@admin.register(Immunization)
class ImmunizationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "vaccine_name", "occurrence_date")
    list_display_links = ("vaccine_name",)
    search_fields = ("vaccine_name", "cvx_code")
    list_filter = ("patient",)
    ordering = ("-occurrence_date",)
    autocomplete_fields = ["patient"]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "category", "specimen", "device", "effective_datetime")
    list_display_links = ("name",)
    search_fields = ("name", "loinc_code")
    list_filter = ("patient", "category")
    ordering = ("-effective_datetime",)
    autocomplete_fields = ["patient", "specimen", "device"]


@admin.register(DiagnosticReport)
class DiagnosticReportAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "code", "status", "category", "effective_datetime", "issued")
    list_display_links = ("code",)
    search_fields = ("code", "category", "conclusion", "conclusion_code", "notes")
    list_filter = ("patient", "status", "category")
    ordering = ("-effective_datetime", "-issued")
    autocomplete_fields = ["patient", "encounter"]
    filter_horizontal = (
        "care_plans",
        "service_requests",
        "specimens",
        "observations",
        "performers_practitioners",
        "performers_roles",
        "performers_organizations",
        "performers_care_teams",
        "interpreter_practitioners",
        "interpreter_roles",
        "interpreter_organizations",
        "interpreter_care_teams",
        "presented_documents",
    )


@admin.register(DetectedIssue)
class DetectedIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "issue_label", "patient", "severity", "status", "identified_datetime")
    list_display_links = ("issue_label",)
    search_fields = ("code", "detail", "evidence_summary", "mitigation_summary", "implicated_summary", "notes")
    list_filter = ("patient", "status", "severity", "code")
    ordering = ("-identified_datetime", "-updated_at")
    autocomplete_fields = ["patient", "author_practitioner", "author_role", "author_device"]
    filter_horizontal = (
        "implicated_conditions",
        "implicated_medications",
        "implicated_immunizations",
        "implicated_observations",
        "implicated_service_requests",
        "implicated_procedures",
        "implicated_devices",
        "implicated_diagnostic_reports",
        "evidence_observations",
        "evidence_conditions",
        "evidence_diagnostic_reports",
    )

    @admin.display(description="Issue", ordering="code")
    def issue_label(self, obj):
        return obj.code or obj.detail or f"Detected Issue #{obj.pk}"


class PersonLinkInline(admin.StackedInline):
    model = PersonLink
    fk_name = "person"
    extra = 0
    fields = (
        "patient",
        "practitioner",
        "related_person",
        "linked_person",
        "assurance",
        "target_display",
        "target_reference",
    )
    autocomplete_fields = ["patient", "practitioner", "related_person", "linked_person"]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    inlines = (PersonLinkInline,)
    list_display = ("id", "person_label", "gender", "birth_date", "phone", "email", "managing_organization", "active")
    list_display_links = ("person_label",)
    search_fields = ("name", "phone", "email", "address", "notes")
    list_filter = ("active", "gender", "managing_organization")
    ordering = ("name",)
    autocomplete_fields = ["managing_organization"]

    @admin.display(description="Person", ordering="name")
    def person_label(self, obj):
        return obj.name or f"Person #{obj.pk}"


@admin.register(RelatedPerson)
class RelatedPersonAdmin(admin.ModelAdmin):
    list_display = ("id", "person_label", "person", "patient", "relationship", "phone", "email", "active")
    list_display_links = ("person_label",)
    search_fields = ("name", "relationship", "phone", "email", "address", "notes")
    list_filter = ("patient", "active", "relationship", "gender", "person")
    ordering = ("patient", "name", "relationship")
    autocomplete_fields = ["person", "patient"]

    @admin.display(description="Related person", ordering="name")
    def person_label(self, obj):
        return obj.name or obj.relationship or f"Related Person #{obj.pk}"


class FHIRGroupMemberInline(admin.StackedInline):
    model = FHIRGroupMember
    fk_name = "group"
    extra = 0
    fieldsets = (
        (None, {
            "fields": (
                "patient",
                "practitioner",
                "practitioner_role",
                "device",
                "medication",
                "member_group",
            ),
        }),
        ("Source details", {
            "fields": (
                "entity_display",
                "entity_reference",
                "start_date",
                "end_date",
                "inactive",
            ),
            "classes": ("collapse",),
        }),
    )
    autocomplete_fields = ["patient", "practitioner", "practitioner_role", "device", "medication", "member_group"]


@admin.register(FHIRGroup)
class FHIRGroupAdmin(admin.ModelAdmin):
    inlines = (FHIRGroupMemberInline,)
    list_display = ("id", "group_label", "group_type", "actual", "quantity", "active")
    list_display_links = ("group_label",)
    search_fields = ("name", "code", "characteristic_summary", "notes")
    list_filter = ("active", "actual", "group_type")
    ordering = ("name", "code")
    autocomplete_fields = [
        "managing_organization",
        "managing_practitioner",
        "managing_role",
        "managing_related_person",
    ]

    @admin.display(description="Group", ordering="name")
    def group_label(self, obj):
        return obj.name or obj.code or f"Group #{obj.pk}"


@admin.register(Specimen)
class SpecimenAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "specimen_type", "status", "accession_identifier", "collected_datetime")
    list_display_links = ("specimen_type",)
    search_fields = ("specimen_type", "accession_identifier", "body_site", "collector_display")
    list_filter = ("patient", "status", "specimen_type")
    ordering = ("-collected_datetime", "-received_time")
    autocomplete_fields = ["patient"]
    filter_horizontal = ("parent_specimens",)


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "encounter_type", "provider_name", "facility_name", "display_start_time")
    list_display_links = ("encounter_type",)
    search_fields = ("provider_name", "facility_name", "reason")
    list_filter = ("patient", "status")
    ordering = ("-start_time",)
    autocomplete_fields = ["patient"]
    filter_horizontal = ("episodes_of_care",)

    @admin.display(description="Start time", ordering="start_time")
    def display_start_time(self, obj):
        if not obj.start_time:
            return "-"
        if obj.start_time.hour == 0 and obj.start_time.minute == 0 and obj.start_time.second == 0:
            return obj.start_time.date()
        return obj.start_time


class CareTeamParticipantInline(admin.StackedInline):
    model = CareTeamParticipant
    extra = 0
    fieldsets = (
        (None, {
            "fields": (
                "role",
                "practitioner",
                "organization",
                "location",
                "related_person",
            ),
        }),
        ("Source details", {
            "fields": (
                "member_display",
                "member_reference",
                "on_behalf_of_display",
                "on_behalf_of_reference",
                "start_date",
                "end_date",
            ),
            "classes": ("collapse",),
        }),
    )
    autocomplete_fields = ["practitioner", "organization", "location", "related_person"]


@admin.register(CareTeam)
class CareTeamAdmin(admin.ModelAdmin):
    inlines = (CareTeamParticipantInline,)
    list_display = ("id", "patient", "name", "status", "category", "start_date")
    list_display_links = ("name",)
    search_fields = ("name", "category", "participants", "reason")
    list_filter = ("patient", "status", "category")
    ordering = ("patient", "name")
    autocomplete_fields = ["patient", "managing_organizations"]
    filter_horizontal = ("managing_organizations",)


@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "title", "status", "intent", "start_date")
    list_display_links = ("title",)
    search_fields = ("title", "category", "description", "author_display")
    list_filter = ("patient", "status", "intent", "category")
    ordering = ("patient", "-start_date", "title")
    autocomplete_fields = ["patient"]
    filter_horizontal = ("conditions", "care_teams")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "status", "intent", "priority", "authored_on")
    list_display_links = ("name",)
    search_fields = ("name", "category", "reason", "patient_instruction")
    list_filter = ("patient", "status", "intent", "priority", "category")
    ordering = ("-authored_on",)
    autocomplete_fields = [
        "patient",
        "encounter",
        "requester_practitioner",
        "requester_role",
        "requester_organization",
        "requester_device",
    ]
    filter_horizontal = (
        "care_plans",
        "replaces",
        "performers_practitioners",
        "performers_roles",
        "performers_organizations",
        "performers_care_teams",
        "performers_devices",
        "locations",
        "conditions",
        "specimens",
    )


@admin.register(EpisodeOfCare)
class EpisodeOfCareAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "episode_type", "status", "managing_organization", "start_date", "end_date")
    list_display_links = ("episode_type",)
    search_fields = ("episode_type", "diagnosis_summary", "notes")
    list_filter = ("patient", "status", "episode_type", "managing_organization")
    ordering = ("-start_date",)
    autocomplete_fields = [
        "patient",
        "managing_organization",
        "care_manager_practitioner",
        "care_manager_role",
    ]
    filter_horizontal = ("referral_requests", "care_teams")


@admin.register(AdverseEvent)
class AdverseEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_label", "patient", "actuality", "severity", "outcome", "event_date")
    list_display_links = ("event_label",)
    search_fields = ("event", "category", "seriousness", "severity", "outcome", "suspect_entity_summary")
    list_filter = ("patient", "actuality", "severity", "outcome", "category")
    ordering = ("-event_date", "-recorded_date")
    autocomplete_fields = [
        "patient",
        "encounter",
        "location",
        "recorder_practitioner",
        "recorder_role",
    ]
    filter_horizontal = (
        "resulting_conditions",
        "contributor_practitioners",
        "contributor_roles",
        "contributor_devices",
        "suspect_immunizations",
        "suspect_procedures",
        "suspect_medications",
        "suspect_devices",
        "reference_documents",
        "subject_medical_history_conditions",
        "subject_medical_history_observations",
        "subject_medical_history_immunizations",
        "subject_medical_history_procedures",
    )

    @admin.display(description="Event", ordering="event")
    def event_label(self, obj):
        return obj.event or obj.category or f"Adverse Event #{obj.pk}"


class FamilyMemberHistoryConditionInline(admin.StackedInline):
    model = FamilyMemberHistoryCondition
    extra = 0
    autocomplete_fields = ["condition"]
    fieldsets = (
        (None, {
            "fields": (
                "condition",
                "condition_text",
                "outcome",
                "contributed_to_death",
                "onset_text",
            ),
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ("collapse",),
        }),
    )
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 3})},
    }


@admin.register(FamilyMemberHistory)
class FamilyMemberHistoryAdmin(admin.ModelAdmin):
    inlines = (FamilyMemberHistoryConditionInline,)
    list_display = ("id", "patient", "relationship", "status", "sex", "age_text", "deceased")
    list_display_links = ("relationship",)
    search_fields = ("relationship", "reason", "notes", "condition_links__condition_text")
    list_filter = ("patient", "status", "relationship", "sex", "deceased")
    ordering = ("patient", "relationship")
    autocomplete_fields = ["patient"]
    filter_horizontal = ("conditions",)


class ClinicalImpressionFindingInline(admin.StackedInline):
    model = ClinicalImpressionFinding
    extra = 0
    autocomplete_fields = ["condition", "observation"]
    fieldsets = (
        (None, {
            "fields": (
                "condition",
                "observation",
                "finding_text",
            ),
        }),
        ("Basis", {
            "fields": ("basis",),
            "classes": ("collapse",),
        }),
    )
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 3})},
    }


@admin.register(ClinicalImpression)
class ClinicalImpressionAdmin(admin.ModelAdmin):
    inlines = (ClinicalImpressionFindingInline,)
    list_display = ("id", "impression_label", "patient", "status", "date", "encounter")
    list_display_links = ("impression_label",)
    search_fields = ("description", "summary", "prognosis", "notes")
    list_filter = ("patient", "status", "date")
    ordering = ("-date", "-effective_datetime")
    autocomplete_fields = [
        "patient",
        "encounter",
        "assessor_practitioner",
        "assessor_role",
    ]
    filter_horizontal = ("conditions", "observations", "problems", "investigations_observations")

    @admin.display(description="Impression", ordering="description")
    def impression_label(self, obj):
        return obj.description or obj.summary or f"Clinical Impression #{obj.pk}"


@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "qualification", "phone", "email", "active", "care_team_count")
    list_display_links = ("name",)
    search_fields = ("name", "npi", "qualification", "phone", "email")
    list_filter = ("active", "qualification")
    ordering = ("name",)

    @admin.display(description="Care teams")
    def care_team_count(self, obj):
        return obj.care_team_participations.count()


@admin.register(PractitionerRole)
class PractitionerRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_label", "practitioner", "organization", "specialty", "active")
    list_display_links = ("role_label",)
    search_fields = ("role", "specialty", "practitioner__name", "organization__name")
    list_filter = ("active", "role", "specialty", "organization")
    ordering = ("practitioner__name", "organization__name", "role")
    autocomplete_fields = ["practitioner", "organization"]
    filter_horizontal = ("locations",)

    @admin.display(description="Role", ordering="role")
    def role_label(self, obj):
        return obj.role or obj.specialty or str(obj.practitioner or obj.organization or f"Practitioner Role #{obj.pk}")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "display_name", "device_type", "status", "manufacturer", "owner")
    list_display_links = ("display_name",)
    search_fields = (
        "display_name",
        "device_type",
        "manufacturer",
        "model_number",
        "serial_number",
        "lot_number",
        "distinct_identifier",
    )
    list_filter = ("patient", "status", "device_type", "manufacturer", "owner")
    ordering = ("display_name",)
    autocomplete_fields = ["patient", "owner", "location"]


class ProcedurePerformerInline(admin.StackedInline):
    model = ProcedurePerformer
    extra = 0
    fieldsets = (
        (None, {
            "fields": (
                "role",
                "practitioner",
                "organization",
            ),
        }),
        ("Source details", {
            "fields": (
                "actor_display",
                "actor_reference",
                "on_behalf_of_display",
                "on_behalf_of_reference",
            ),
            "classes": ("collapse",),
        }),
    )
    autocomplete_fields = ["practitioner", "organization"]


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    inlines = (ProcedurePerformerInline,)
    list_display = ("id", "patient", "name", "status", "category", "performed_start")
    list_display_links = ("name",)
    search_fields = ("name", "category", "reason", "body_site", "outcome")
    list_filter = ("patient", "status", "category")
    ordering = ("-performed_start",)
    autocomplete_fields = ["patient", "encounter"]
    filter_horizontal = ("care_plans", "service_requests", "conditions")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization_type", "phone", "email", "active", "care_team_count")
    list_display_links = ("name",)
    search_fields = ("name", "organization_type", "phone", "email")
    list_filter = ("active", "organization_type")
    ordering = ("name",)

    @admin.display(description="Care teams")
    def care_team_count(self, obj):
        participation_count = obj.care_team_participations.count()
        managing_count = obj.managed_care_teams.count()
        return participation_count + managing_count


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "mode", "location_type", "managing_organization", "care_team_count")
    list_display_links = ("name",)
    search_fields = ("name", "location_type", "managing_organization", "phone", "email")
    list_filter = ("status", "mode", "location_type")
    ordering = ("name",)

    @admin.display(description="Care teams")
    def care_team_count(self, obj):
        return obj.care_team_participations.count()
