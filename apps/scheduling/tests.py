from django.test import TestCase
from django.urls import reverse


class SchedulingViewTests(TestCase):
    def test_request_appointment_requires_login(self) -> None:
        response = self.client.get(reverse("request_appointment"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)