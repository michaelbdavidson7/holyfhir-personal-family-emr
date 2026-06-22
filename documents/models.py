from django.db import models
from patients.models import PatientProfile


class ClinicalDocument(models.Model):
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="documents"
    )
    encounter = models.ForeignKey(
        "clinical.Encounter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    authors = models.ManyToManyField(
        "clinical.Practitioner", blank=True, related_name="authored_documents"
    )
    custodian = models.ForeignKey(
        "clinical.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custodied_documents",
    )
    related_documents = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="related_to_documents"
    )
    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=100, blank=True
    )  # discharge summary, lab report, scan
    description = models.TextField(blank=True)

    file = models.FileField(upload_to="clinical_documents/")
    mime_type = models.CharField(max_length=100, blank=True)

    source_name = models.CharField(max_length=255, blank=True)
    source_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
