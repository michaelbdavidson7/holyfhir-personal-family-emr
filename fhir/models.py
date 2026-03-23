from django.db import models
from patients.models import PatientProfile


class FHIRResourceSnapshot(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="fhir_snapshots",
        null=True,
        blank=True,
    )

    resource_type = models.CharField(max_length=100)   # Patient, Observation, Condition
    resource_id = models.CharField(max_length=100, blank=True)
    version_id = models.CharField(max_length=100, blank=True)

    source = models.CharField(max_length=50, default="internal")  
    # internal, imported, exported, synced

    raw_json = models.JSONField()
    checksum = models.CharField(max_length=128, blank=True)

    is_valid = models.BooleanField(default=True)
    validation_errors = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class FHIRLink(models.Model):
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, null=True, blank=True)

    django_model = models.CharField(max_length=100)    # Medication, Observation, etc.
    django_object_id = models.PositiveIntegerField()

    last_synced_at = models.DateTimeField(null=True, blank=True)
    direction = models.CharField(max_length=20, default="internal_to_fhir")