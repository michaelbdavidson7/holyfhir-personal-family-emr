from django.contrib import admin
from .models import PatientProfile

from clinical.models import (
    Condition,
    Allergy,
    Medication,
    Immunization,
    Observation,
    Encounter,
)
from documents.models import ClinicalDocument

class ConditionInline(admin.StackedInline):
    model = Condition
    extra = 0
    fields = ("name", "clinical_status", "onset_date", "abatement_date", "notes")
    show_change_link = True


class AllergyInline(admin.StackedInline):
    model = Allergy
    extra = 0
    fields = ("substance", "category", "criticality", "reaction", "severity", "notes")
    show_change_link = True


class MedicationInline(admin.StackedInline):
    model = Medication
    extra = 0
    fields = ("name", "dosage_text", "frequency", "status", "start_date", "end_date")
    show_change_link = True


class ImmunizationInline(admin.StackedInline):
    model = Immunization
    extra = 0
    fields = ("vaccine_name", "occurrence_date", "lot_number", "manufacturer")
    show_change_link = True


class ObservationInline(admin.StackedInline):
    model = Observation
    extra = 0
    fields = ("category", "name", "value_string", "value_quantity", "unit", "effective_datetime")
    show_change_link = True


class EncounterInline(admin.StackedInline):
    model = Encounter
    extra = 0
    fields = ("encounter_type", "status", "start_time", "end_time", "provider_name", "facility_name")
    show_change_link = True


class ClinicalDocumentInline(admin.StackedInline):
    model = ClinicalDocument
    extra = 0
    fields = ("title", "document_type", "source_name", "source_date", "file")
    show_change_link = True

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "date_of_birth",
        "phone",
        "email",
        "updated_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    list_filter = (
        'sex_at_birth',
        "organ_donor",
        "created_at",
    )

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "first_name",
                "last_name",
                "date_of_birth",
                'sex_at_birth',
                "gender_identity",
            )
        }),
        ("Contact", {
            "fields": (
                "phone",
                "email",
            )
        }),
        ("Address", {
            "fields": (
                "address_line_1",
                "address_line_2",
                "city",
                "state",
                "postal_code",
                "country",
            )
        }),
        ("Medical Info", {
            "fields": (
                "blood_type",
                "organ_donor",
            )
        }),
        ("Emergency Contact", {
            "fields": (
                "emergency_contact_name",
                "emergency_contact_phone",
                "emergency_contact_relationship",
            )
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at")
        }),
    )
    
    inlines = [
        ConditionInline,
        AllergyInline,
        MedicationInline,
        ImmunizationInline,
        ObservationInline,
        EncounterInline,
        ClinicalDocumentInline,
    ]