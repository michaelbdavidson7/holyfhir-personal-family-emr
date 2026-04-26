import json
import tempfile
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from clinical.models import Condition, Medication, Observation
from patients.models import PatientProfile

from .backups import create_pre_import_database_backup, list_fhir_import_database_backups
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

    def test_import_page_can_quick_add_patient(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="correct-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("fhir_import"),
            {
                "action": "create_patient",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "date_of_birth": "1815-12-10",
            },
            follow=True,
        )

        patient = PatientProfile.objects.get(first_name="Ada", last_name="Lovelace")
        self.assertRedirects(response, f"{reverse('fhir_import')}?patient={patient.pk}")
        self.assertEqual(patient.date_of_birth, date(1815, 12, 10))
        self.assertEqual(response.context["form"].initial["patient"], str(patient.pk))

    def test_import_page_includes_admin_sidebar_context(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="correct-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("fhir_import"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("available_apps", response.context)
        self.assertContains(response, "jazzy-navigation")

    def test_pre_import_backup_copies_database_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "holyfhir.encrypted.sqlite3"
            database_path.write_bytes(b"encrypted database bytes")
            fake_connections = {"default": Mock()}

            with patch("fhir.backups.settings.DATABASES", {"default": {"NAME": str(database_path)}}):
                with patch("fhir.backups.connections", fake_connections):
                    backup_path = create_pre_import_database_backup()

            self.assertIsNotNone(backup_path)
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_bytes(), b"encrypted database bytes")
            self.assertEqual(backup_path.parent, database_path.parent / "backups" / "fhir-imports")
            self.assertIn(".pre-fhir-import.", backup_path.name)
            fake_connections["default"].close.assert_called_once()

    def test_lists_fhir_import_backups_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "holyfhir.encrypted.sqlite3"
            database_path.write_bytes(b"live")
            backup_dir = Path(temp_dir) / "backups" / "fhir-imports"
            backup_dir.mkdir(parents=True)
            older = backup_dir / "holyfhir.encrypted.pre-fhir-import.20260426-120000.sqlite3"
            newer = backup_dir / "holyfhir.encrypted.pre-fhir-import.20260426-130000.sqlite3"
            ignored = backup_dir / "notes.txt"
            older.write_bytes(b"older")
            newer.write_bytes(b"newer")
            ignored.write_text("not a backup")

            with patch("fhir.backups.settings.DATABASES", {"default": {"NAME": str(database_path)}}):
                backups = list_fhir_import_database_backups()

            self.assertEqual([backup.name for backup in backups], [newer.name, older.name])
            self.assertEqual(backups[0].size_bytes, 5)

    def test_import_page_creates_pre_import_backup(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="correct-password",
        )
        self.client.force_login(user)
        payload = {
            "resourceType": "Patient",
            "id": "pat-1",
            "name": [{"family": "Rivera", "given": ["Maya"]}],
        }

        with patch("fhir.views.create_pre_import_database_backup", return_value=Path("backup.sqlite3")) as backup:
            response = self.client.post(
                reverse("fhir_import"),
                {"action": "import_fhir", "fhir_json": json.dumps(payload)},
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        backup.assert_called_once()
        self.assertEqual(PatientProfile.objects.filter(first_name="Maya", last_name="Rivera").count(), 1)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("Pre-import database backup created: backup.sqlite3" in message for message in messages))

    def test_import_page_stops_if_pre_import_backup_fails(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="correct-password",
        )
        self.client.force_login(user)
        payload = {
            "resourceType": "Patient",
            "id": "pat-1",
            "name": [{"family": "Rivera", "given": ["Maya"]}],
        }

        with patch("fhir.views.create_pre_import_database_backup", side_effect=OSError("disk is full")):
            response = self.client.post(
                reverse("fhir_import"),
                {"action": "import_fhir", "fhir_json": json.dumps(payload)},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PatientProfile.objects.filter(first_name="Maya", last_name="Rivera").count(), 0)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("database backup failed" in message for message in messages))
