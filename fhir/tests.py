import json
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from clinical.models import Condition, Medication, Observation
from patients.models import PatientProfile

from .forms import FHIRImportForm
from .importer import import_fhir_json, import_fhir_payloads, loads_fhir_documents, loads_fhir_json
from .models import FHIRLink, FHIRResourceSnapshot


class FHIRImportTests(TestCase):
    def test_imports_bundle_patient_and_clinical_resources(self):
        payload = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pat-1",
                        "name": [{"family": "Rivera", "given": ["Maya"]}],
                        "birthDate": "1980-04-12",
                        "gender": "female",
                        "telecom": [
                            {"system": "phone", "value": "555-0100"},
                            {"system": "email", "value": "maya@example.test"},
                        ],
                        "address": [{"line": ["1 Main St"], "city": "Boston", "state": "MA"}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "cond-1",
                        "subject": {"reference": "Patient/pat-1"},
                        "code": {
                            "text": "Asthma",
                            "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "J45.909"}],
                        },
                        "clinicalStatus": {"coding": [{"code": "active", "display": "Active"}]},
                        "onsetDateTime": "2020-01-02",
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationStatement",
                        "id": "med-1",
                        "subject": {"reference": "Patient/pat-1"},
                        "status": "active",
                        "medicationCodeableConcept": {"text": "Albuterol inhaler"},
                        "dosage": [{"text": "2 puffs as needed"}],
                        "effectivePeriod": {"start": "2021-02-03"},
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "id": "obs-1",
                        "subject": {"reference": "Patient/pat-1"},
                        "category": [{"text": "Vital Signs"}],
                        "code": {"text": "Body weight"},
                        "valueQuantity": {"value": 72.5, "unit": "kg"},
                        "effectiveDateTime": "2022-03-04T10:15:00Z",
                    }
                },
            ],
        }

        result = import_fhir_json(payload)

        self.assertEqual(result.created, 4)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.snapshots, 4)
        self.assertEqual(result.errors, [])

        patient = PatientProfile.objects.get()
        self.assertEqual(patient.first_name, "Maya")
        self.assertEqual(patient.last_name, "Rivera")
        self.assertEqual(patient.date_of_birth, date(1980, 4, 12))
        self.assertEqual(patient.email, "maya@example.test")

        condition = Condition.objects.get()
        self.assertEqual(condition.patient, patient)
        self.assertEqual(condition.name, "Asthma")
        self.assertEqual(condition.icd10_code, "J45.909")

        medication = Medication.objects.get()
        self.assertEqual(medication.name, "Albuterol inhaler")
        self.assertEqual(medication.dosage_text, "2 puffs as needed")

        observation = Observation.objects.get()
        self.assertEqual(observation.category, "vital")
        self.assertEqual(observation.value_quantity, 72.5)
        self.assertEqual(observation.unit, "kg")

        self.assertEqual(FHIRResourceSnapshot.objects.count(), 4)
        self.assertEqual(FHIRLink.objects.count(), 4)

    def test_reimport_updates_linked_resources(self):
        payload = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pat-1",
                        "name": [{"family": "Rivera", "given": ["Maya"]}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "cond-1",
                        "subject": {"reference": "Patient/pat-1"},
                        "code": {"text": "Asthma"},
                    }
                },
            ],
        }

        import_fhir_json(payload)
        payload["entry"][1]["resource"]["code"]["text"] = "Resolved asthma"
        result = import_fhir_json(payload)

        self.assertEqual(result.created, 0)
        self.assertEqual(result.updated, 2)
        self.assertEqual(PatientProfile.objects.count(), 1)
        self.assertEqual(Condition.objects.count(), 1)
        self.assertEqual(Condition.objects.get().name, "Resolved asthma")
        self.assertEqual(FHIRResourceSnapshot.objects.count(), 4)

    def test_import_can_attach_to_existing_patient(self):
        existing_patient = PatientProfile.objects.create(
            first_name="Mike",
            last_name="Davidson",
            email="existing@example.test",
        )
        payload = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "epic-patient-id",
                        "name": [{"family": "Davidson", "given": ["Michael"]}],
                        "telecom": [{"system": "phone", "value": "555-0199"}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "cond-1",
                        "subject": {"reference": "Patient/epic-patient-id"},
                        "code": {"text": "Asthma"},
                    }
                },
            ],
        }

        result = import_fhir_json(payload, target_patient=existing_patient)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(PatientProfile.objects.count(), 1)

        existing_patient.refresh_from_db()
        self.assertEqual(existing_patient.first_name, "Mike")
        self.assertEqual(existing_patient.email, "existing@example.test")
        self.assertEqual(existing_patient.phone, "555-0199")
        self.assertEqual(Condition.objects.get().patient, existing_patient)
        self.assertTrue(
            FHIRLink.objects.filter(
                resource_type="Patient",
                resource_id="epic-patient-id",
                django_object_id=existing_patient.id,
            ).exists()
        )

    def test_missing_patient_reference_is_snapshotted_as_invalid(self):
        result = import_fhir_json(
            {
                "resourceType": "Condition",
                "id": "orphan",
                "subject": {"reference": "Patient/missing"},
                "code": {"text": "Asthma"},
            }
        )

        self.assertEqual(result.created, 0)
        self.assertEqual(len(result.errors), 1)
        snapshot = FHIRResourceSnapshot.objects.get()
        self.assertFalse(snapshot.is_valid)
        self.assertEqual(snapshot.validation_errors, ["Missing or unknown patient reference."])

    def test_loads_fhir_json_rejects_invalid_json(self):
        with self.assertRaises(ValueError):
            loads_fhir_json("{not-json")

    def test_loads_ndjson_resources(self):
        payloads = loads_fhir_documents(
            "\n".join(
                [
                    json.dumps({"resourceType": "Patient", "id": "pat-1"}),
                    json.dumps({"resourceType": "Condition", "id": "cond-1"}),
                ]
            ),
            "export.ndjson",
        )

        self.assertEqual([payload["resourceType"] for payload in payloads], ["Patient", "Condition"])

    def test_form_accepts_mychart_zip_export(self):
        archive_content = BytesIO()
        with ZipFile(archive_content, "w") as archive:
            archive.writestr(
                "Requested Record/FHIR/Patient11694.NDJSON",
                json.dumps(
                    {
                        "resourceType": "Patient",
                        "id": "pat-1",
                        "name": [{"family": "Rivera", "given": ["Maya"]}],
                    }
                )
                + "\n",
            )
            archive.writestr(
                "Requested Record/FHIR/condition1168.NDJSON",
                json.dumps(
                    {
                        "resourceType": "Condition",
                        "id": "cond-1",
                        "subject": {"reference": "Patient/pat-1"},
                        "code": {"text": "Asthma"},
                    }
                )
                + "\n",
            )
            archive.writestr("Requested Record/readme.txt", "not fhir")

        uploaded_file = SimpleUploadedFile(
            "Requested Record.zip",
            archive_content.getvalue(),
            content_type="application/zip",
        )
        form = FHIRImportForm(data={}, files={"fhir_file": uploaded_file})

        self.assertTrue(form.is_valid(), form.errors)
        result = import_fhir_payloads(form.cleaned_data["payloads"])

        self.assertEqual(result.created, 2)
        self.assertEqual(PatientProfile.objects.count(), 1)
        self.assertEqual(Condition.objects.count(), 1)
