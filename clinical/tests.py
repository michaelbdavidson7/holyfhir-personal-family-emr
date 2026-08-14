from decimal import Decimal
from datetime import datetime
from datetime import timezone as datetime_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from patients.models import PatientProfile

from .models import Observation
from .models import QuickLog


class ObservationChartTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="correct-password",
        )
        self.patient = PatientProfile.objects.create(
            first_name="Ada",
            last_name="Lovelace",
        )

    def test_observation_chart_renders_numeric_observations(self):
        Observation.objects.create(
            patient=self.patient,
            category="vital",
            name="Systolic blood pressure",
            value_quantity=Decimal("122"),
            unit="mmHg",
            effective_datetime=timezone.now(),
        )
        Observation.objects.create(
            patient=self.patient,
            category="vital",
            name="Systolic blood pressure",
            value_string="not numeric",
            effective_datetime=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("observation_charts"),
            {"patient": self.patient.pk, "names": "Systolic blood pressure"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Health Trends")
        self.assertContains(response, "Systolic blood pressure")
        self.assertContains(response, "122.0")
        self.assertNotContains(response, "not numeric")

    def test_observation_chart_empty_state_links_to_add_observation(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("observation_charts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chartable measurements yet")
        self.assertContains(response, reverse("admin:clinical_observation_add"))


class QuickLogTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="correct-password",
        )
        self.patient = PatientProfile.objects.create(
            first_name="Ada",
            last_name="Lovelace",
        )

    def test_quick_log_page_creates_log(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("quick_logs"),
            {
                "patient": self.patient.pk,
                "category": QuickLog.CATEGORY_BOWEL,
                "logged_at": "2026-08-13T09:15",
                "summary": "Normal bowel movement",
                "details": "No discomfort.",
            },
        )

        self.assertRedirects(
            response,
            (
                f"{reverse('quick_logs')}?"
                f"patient={self.patient.pk}&category={QuickLog.CATEGORY_BOWEL}"
            ),
            fetch_redirect_response=False,
        )
        log = QuickLog.objects.get()
        self.assertEqual(log.patient, self.patient)
        self.assertEqual(log.category, QuickLog.CATEGORY_BOWEL)
        self.assertEqual(log.summary, "Normal bowel movement")
        self.assertEqual(log.details, "No discomfort.")

    def test_quick_logs_are_ordered_newest_first(self):
        older = QuickLog.objects.create(
            patient=self.patient,
            category=QuickLog.CATEGORY_DIET,
            logged_at=datetime(2026, 8, 13, 8, 0, tzinfo=datetime_timezone.utc),
            summary="Breakfast",
        )
        newer = QuickLog.objects.create(
            patient=self.patient,
            category=QuickLog.CATEGORY_SYMPTOM,
            logged_at=datetime(2026, 8, 13, 12, 0, tzinfo=datetime_timezone.utc),
            summary="Mild nausea",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("quick_logs"))

        self.assertEqual(response.status_code, 200)
        logs = list(response.context["logs"])
        self.assertEqual(logs, [newer, older])
        self.assertContains(response, "Mild nausea")
        self.assertContains(response, "Breakfast")

    def test_quick_log_form_remembers_last_category(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("quick_logs"),
            {
                "patient": self.patient.pk,
                "category": QuickLog.CATEGORY_DIET,
                "logged_at": "2026-08-13T09:15",
                "summary": "Oatmeal and berries",
                "details": "",
            },
        )

        response = self.client.get(reverse("quick_logs"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].initial["category"], QuickLog.CATEGORY_DIET
        )
        self.assertContains(response, '<option value="diet" selected>Dietary</option>')

    def test_quick_log_form_remembers_last_patient(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("quick_logs"),
            {
                "patient": self.patient.pk,
                "category": QuickLog.CATEGORY_SLEEP,
                "logged_at": "2026-08-13T22:15",
                "summary": "Went to bed",
                "details": "",
            },
        )

        response = self.client.get(reverse("quick_logs"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["patient"], self.patient.pk)

    def test_quick_log_patient_query_overrides_remembered_patient(self):
        other_patient = PatientProfile.objects.create(
            first_name="Grace",
            last_name="Hopper",
        )
        session = self.client.session
        session["quick_logs_last_patient"] = self.patient.pk
        session.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse("quick_logs"), {"patient": other_patient.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].initial["patient"], str(other_patient.pk)
        )

    def test_quick_logs_filter_by_category_tab(self):
        QuickLog.objects.create(
            patient=self.patient,
            category=QuickLog.CATEGORY_DIET,
            logged_at=datetime(2026, 8, 13, 8, 0, tzinfo=datetime_timezone.utc),
            summary="Breakfast",
        )
        QuickLog.objects.create(
            patient=self.patient,
            category=QuickLog.CATEGORY_BOWEL,
            logged_at=datetime(2026, 8, 13, 9, 0, tzinfo=datetime_timezone.utc),
            summary="BM after breakfast",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("quick_logs"), {"category": QuickLog.CATEGORY_DIET}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_category"], QuickLog.CATEGORY_DIET)
        self.assertContains(response, "Breakfast")
        self.assertNotContains(response, "BM after breakfast")
        self.assertContains(response, "quick-log-tab-selected")
        self.assertContains(response, 'aria-current="page"')

    def test_quick_log_category_query_overrides_remembered_category(self):
        session = self.client.session
        session["quick_logs_last_category"] = QuickLog.CATEGORY_DIET
        session.save()
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("quick_logs"), {"category": QuickLog.CATEGORY_BOWEL}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].initial["category"], QuickLog.CATEGORY_BOWEL
        )

    def test_quick_log_save_redirects_to_patient_category_list(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("quick_logs"),
            {
                "patient": self.patient.pk,
                "category": QuickLog.CATEGORY_MOOD,
                "logged_at": "2026-08-13T14:15",
                "summary": "Felt steady",
                "details": "",
            },
        )

        self.assertRedirects(
            response,
            (
                f"{reverse('quick_logs')}?"
                f"patient={self.patient.pk}&category={QuickLog.CATEGORY_MOOD}"
            ),
            fetch_redirect_response=False,
        )
