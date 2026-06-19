from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SettingsBackupPageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="correct-password",
        )
        self.client.force_login(self.user)

    def test_settings_links_to_backups_page(self):
        response = self.client.get(reverse("admin_settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backups")
        self.assertContains(response, reverse("admin_backups"))

    def test_backups_page_renders_manual_restore_explainer(self):
        response = self.client.get(reverse("admin_backups"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manual Restore")
        self.assertContains(response, "Close HolyFHIR completely")
        self.assertContains(response, "FHIR Import Backups")

    def test_clinical_care_team_directory_lists_directory_sections(self):
        response = self.client.get(reverse("clinical_care_team_directory"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Care Teams")
        self.assertContains(response, "Practitioners")
        self.assertContains(response, "Organizations")
        self.assertContains(response, "Locations")
        self.assertContains(response, reverse("admin:clinical_careteam_changelist"))
        self.assertContains(response, reverse("admin:clinical_practitioner_changelist"))
        self.assertContains(response, reverse("admin:clinical_organization_changelist"))
        self.assertContains(response, reverse("admin:clinical_location_changelist"))

    def test_clinical_resources_directory_lists_all_clinical_resources(self):
        response = self.client.get(reverse("clinical_resources_directory"))

        self.assertEqual(response.status_code, 200)
        expected_resources = [
            ("Conditions", "admin:clinical_condition_changelist"),
            ("Allergies", "admin:clinical_allergy_changelist"),
            ("Adverse Events", "admin:clinical_adverseevent_changelist"),
            ("Family History", "admin:clinical_familymemberhistory_changelist"),
            ("Related People", "admin:clinical_relatedperson_changelist"),
            ("People", "admin:clinical_person_changelist"),
            ("Clinical Impressions", "admin:clinical_clinicalimpression_changelist"),
            ("Detected Issues", "admin:clinical_detectedissue_changelist"),
            ("Medications", "admin:clinical_medication_changelist"),
            ("Immunizations", "admin:clinical_immunization_changelist"),
            ("Vitals &amp; Labs", "admin:clinical_observation_changelist"),
            ("Diagnostic Reports", "admin:clinical_diagnosticreport_changelist"),
            ("Visits &amp; Actions", "admin:clinical_encounter_changelist"),
            ("Devices", "admin:clinical_device_changelist"),
            ("Groups", "admin:clinical_fhirgroup_changelist"),
            ("Care Teams", "admin:clinical_careteam_changelist"),
            ("Care Plans", "admin:clinical_careplan_changelist"),
            ("Service Requests", "admin:clinical_servicerequest_changelist"),
            ("Episodes of Care", "admin:clinical_episodeofcare_changelist"),
            ("Procedures", "admin:clinical_procedure_changelist"),
            ("Specimens", "admin:clinical_specimen_changelist"),
            ("Practitioners", "admin:clinical_practitioner_changelist"),
            ("Practitioner Roles", "admin:clinical_practitionerrole_changelist"),
            ("Organizations", "admin:clinical_organization_changelist"),
            ("Locations", "admin:clinical_location_changelist"),
        ]
        for label, url_name in expected_resources:
            self.assertContains(response, label)
            self.assertContains(response, reverse(url_name))
