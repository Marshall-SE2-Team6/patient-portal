from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model


class SchedulingViewTests(TestCase):
    def test_request_appointment_requires_login(self) -> None:
        response = self.client.get(reverse("request_appointment"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


def test_my_appointments_profile_missing_for_user_without_patient_profile(self) -> None:
    user = get_user_model().objects.create_user(
        username="scheduser",
        password="testpass123",
    )
    self.client.login(username="scheduser", password="testpass123")

    response = self.client.get(reverse("my_appointments"))

    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.context["profile_missing"])
    self.assertEqual(list(response.context["appointments"]), [])