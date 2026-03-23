from django.contrib import admin
from .models import FHIRResourceSnapshot, FHIRLink


@admin.register(FHIRResourceSnapshot)
class FHIRResourceSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resource_type",
        "resource_id",
        "source",
        "is_valid",
        "created_at",
    )

    search_fields = (
        "resource_type",
        "resource_id",
    )

    list_filter = (
        "resource_type",
        "source",
        "is_valid",
    )

    readonly_fields = (
        "created_at",
        "raw_json",
        "validation_errors",
    )


@admin.register(FHIRLink)
class FHIRLinkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resource_type",
        "resource_id",
        "django_model",
        "django_object_id",
        "last_synced_at",
    )

    search_fields = (
        "resource_type",
        "resource_id",
        "django_model",
    )

    list_filter = (
        "resource_type",
        "direction",
    )