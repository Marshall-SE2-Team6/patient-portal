from django.test import TestCase
from django.urls import reverse


class AccountsViewTests(TestCase):
    def test_login_page_loads(self) -> None:
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
