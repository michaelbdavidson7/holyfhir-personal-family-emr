from django.contrib import admin
from .models import Condition, Allergy, Medication, Immunization, Observation, Encounter


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "clinical_status", "onset_date")
    search_fields = ("name", "icd10_code", "snomed_code")
    list_filter = ("clinical_status",)
    autocomplete_fields = ["patient"]


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "substance", "category", "severity")
    search_fields = ("substance", "rxnorm_code", "snomed_code")
    list_filter = ("category", "severity", "criticality")
    autocomplete_fields = ["patient"]


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "status", "start_date")
    search_fields = ("name", "rxnorm_code", "prescriber")
    list_filter = ("status",)
    autocomplete_fields = ["patient"]


@admin.register(Immunization)
class ImmunizationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "vaccine_name", "occurrence_date")
    search_fields = ("vaccine_name", "cvx_code")
    autocomplete_fields = ["patient"]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "category", "effective_datetime")
    search_fields = ("name", "loinc_code")
    list_filter = ("category",)
    autocomplete_fields = ["patient"]


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "encounter_type", "start_time")
    search_fields = ("provider_name", "facility_name", "reason")
    autocomplete_fields = ["patient"]