from django.contrib import admin
from .models import ClinicalDocument


@admin.register(ClinicalDocument)
class ClinicalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "title",
        "document_type",
        "source_name",
        "source_date",
    )

    search_fields = (
        "title",
        "document_type",
        "source_name",
    )

    list_filter = (
        "patient",
        "document_type",
        "source_date",
    )

    autocomplete_fields = ["patient"]
