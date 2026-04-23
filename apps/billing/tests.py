from django.test import TestCase
from django.urls import reverse


class BillingViewTests(TestCase):
    def test_invoice_list_requires_login(self) -> None:
        response = self.client.get(reverse("billing:invoice_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)