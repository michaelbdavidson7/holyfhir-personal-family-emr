from django.contrib import admin
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