from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model


class BillingViewTests(TestCase):
    def test_invoice_list_requires_login(self) -> None:
        response = self.client.get(reverse("billing:invoice_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

def test_invoice_list_profile_missing_for_user_without_patient_profile(self) -> None:
    user = get_user_model().objects.create_user(
        username="billinguser",
        password="testpass123",
    )
    self.client.login(username="billinguser", password="testpass123")

    response = self.client.get(reverse("billing:invoice_list"))

    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.context["profile_missing"])
    self.assertEqual(list(response.context["invoices"]), [])