from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import PatientProfile


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

    readonly_fields = ("related_records", "created_at", "updated_at")

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
        ("Records", {
            "fields": ("related_records",)
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at")
        }),
    )

    @admin.display(description="Related records")
    def related_records(self, obj):
        if not obj or not obj.pk:
            return "Save this patient before adding clinical records."

        rows = [
            self._related_record_link(obj, "Conditions", "clinical_condition", obj.conditions.count()),
            self._related_record_link(obj, "Allergies", "clinical_allergy", obj.allergies.count()),
            self._related_record_link(obj, "Medications", "clinical_medication", obj.medications.count()),
            self._related_record_link(obj, "Immunizations", "clinical_immunization", obj.immunizations.count()),
            self._related_record_link(obj, "Observations", "clinical_observation", obj.observations.count()),
            self._related_record_link(obj, "Encounters", "clinical_encounter", obj.encounters.count()),
            self._related_record_link(obj, "Documents", "documents_clinicaldocument", obj.documents.count()),
            self._related_record_link(obj, "FHIR snapshots", "fhir_fhirresourcesnapshot", obj.fhir_snapshots.count()),
        ]

        return format_html("<ul>{}</ul>", format_html_join("", "<li>{}</li>", ((row,) for row in rows)))

    def _related_record_link(self, obj, label, admin_model_name, count):
        changelist_url = reverse(f"admin:{admin_model_name}_changelist")
        add_url = reverse(f"admin:{admin_model_name}_add")
        query = f"patient__id__exact={obj.pk}"
        return format_html(
            '<a href="{}?{}">{} ({})</a> <span class="quiet">|</span> <a href="{}?patient={}">Add</a>',
            changelist_url,
            query,
            label,
            count,
            add_url,
            obj.pk,
        )
