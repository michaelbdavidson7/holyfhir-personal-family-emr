from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import PatientProfile, RecoveryCredential


User = get_user_model()


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


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    readonly_fields = (*DjangoUserAdmin.readonly_fields, "recovery_key_status_detail")

    fieldsets = (
        *DjangoUserAdmin.fieldsets,
        (
            "Recovery key",
            {
                "fields": ("recovery_key_status_detail",),
                "description": (
                    "Recovery keys are not fully enabled in first-run setup yet. "
                    "The raw recovery key is never stored and cannot be viewed here."
                ),
            },
        ),
    )

    def get_list_display(self, request):
        base_list_display = list(super().get_list_display(request))

        if "recovery_key_status" not in base_list_display:
            base_list_display.append("recovery_key_status")

        return base_list_display

    @admin.display(description="Recovery key", boolean=True)
    def recovery_key_status(self, obj):
        return hasattr(obj, "recovery_credential")

    @admin.display(description="Recovery key status")
    def recovery_key_status_detail(self, obj):
        if not obj or not obj.pk:
            return "Save this user before configuring recovery."

        if not hasattr(obj, "recovery_credential"):
            return "No recovery key has been created for this user yet."

        credential = obj.recovery_credential

        if credential.last_used_at:
            return format_html(
                "Recovery key is configured. Last used: {}. The raw key cannot be viewed here.",
                credential.last_used_at,
            )

        return format_html(
            "Recovery key is configured. Created: {}. The raw key cannot be viewed here.",
            credential.created_at,
        )


@admin.register(RecoveryCredential)
class RecoveryCredentialAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "hash_preview",
        "created_at",
        "last_used_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "recovery_key_hash",
    )
    readonly_fields = (
        "user",
        "recovery_key_hash",
        "created_at",
        "last_used_at",
    )
    fields = (
        "user",
        "recovery_key_hash",
        "created_at",
        "last_used_at",
    )

    @admin.display(description="Stored hash")
    def hash_preview(self, obj):
        if not obj.recovery_key_hash:
            return "-"

        return f"{obj.recovery_key_hash[:24]}..."

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
