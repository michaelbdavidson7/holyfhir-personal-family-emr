from django.db import models
from patients.models import PatientProfile


class ClinicalDocument(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100, blank=True)  # discharge summary, lab report, scan
    description = models.TextField(blank=True)

    file = models.FileField(upload_to="clinical_documents/")
    mime_type = models.CharField(max_length=100, blank=True)

    source_name = models.CharField(max_length=255, blank=True)
    source_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)