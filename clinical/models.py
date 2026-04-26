from django.db import models
from patients.models import PatientProfile


class Condition(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="conditions")
    name = models.CharField(max_length=255)
    icd10_code = models.CharField(max_length=20, blank=True)
    snomed_code = models.CharField(max_length=30, blank=True)
    clinical_status = models.CharField(max_length=30, blank=True)  # active, resolved, inactive
    onset_date = models.DateField(null=True, blank=True)
    abatement_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Allergy(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="allergies")
    substance = models.CharField(max_length=255)
    rxnorm_code = models.CharField(max_length=30, blank=True)
    snomed_code = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=50, blank=True)  # food, medication, environment
    criticality = models.CharField(max_length=20, blank=True)  # low, high, unable-to-assess
    reaction = models.CharField(max_length=255, blank=True)
    severity = models.CharField(max_length=20, blank=True)  # mild, moderate, severe
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Allergies"


class Medication(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=255)
    rxnorm_code = models.CharField(max_length=30, blank=True)
    dosage_text = models.CharField(max_length=255, blank=True)
    route = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, blank=True)  # active, stopped, completed
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    prescriber = models.CharField(max_length=255, blank=True)
    indication = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Immunization(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="immunizations")
    vaccine_name = models.CharField(max_length=255)
    cvx_code = models.CharField(max_length=20, blank=True)
    occurrence_date = models.DateField(null=True, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    performer = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Observation(models.Model):
    OBSERVATION_TYPES = [
        ("vital", "Vital"),
        ("lab", "Lab"),
        ("other", "Other"),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="observations")
    category = models.CharField(max_length=20, choices=OBSERVATION_TYPES, default="other")
    name = models.CharField(max_length=255)
    loinc_code = models.CharField(max_length=30, blank=True)

    value_string = models.CharField(max_length=255, blank=True)
    value_quantity = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)

    effective_datetime = models.DateTimeField(null=True, blank=True)
    interpretation = models.CharField(max_length=50, blank=True)  # high, low, normal
    reference_range = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Encounter(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="encounters")
    encounter_type = models.CharField(max_length=100, blank=True)  # office visit, ED, inpatient
    status = models.CharField(max_length=30, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)