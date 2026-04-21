from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from patients.models import PatientProfile

from .models import Observation


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
        self.assertContains(response, "Observation Charts")
        self.assertContains(response, "Systolic blood pressure")
        self.assertContains(response, "122.0")
        self.assertNotContains(response, "not numeric")

    def test_observation_chart_empty_state_links_to_add_observation(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("observation_charts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chartable observations yet")
        self.assertContains(response, reverse("admin:clinical_observation_add"))
