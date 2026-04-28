from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.billing.models import Invoice, InvoiceLineItem, Payment, PaymentMethod, PaymentMethodType
from apps.profiles.models import PatientProfile


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
        self.assertEqual(list(response.context["invoice_rows"]), [])

    def test_patient_can_pay_invoice_and_balance_updates(self) -> None:
        user = get_user_model().objects.create_user(
            username="alicebilling",
            password="testpass123",
        )
        patient_profile = PatientProfile.objects.create(user=user)
        method = PaymentMethod.objects.create(
            patient=patient_profile,
            method_type=PaymentMethodType.CREDIT_CARD,
            nickname="Visa",
            last4="1111",
            is_default=True,
        )
        invoice = Invoice.objects.create(
            patient=patient_profile,
            invoice_number="INV-T100",
            status="issued",
            tax_amount=Decimal("0.00"),
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Office Visit",
            quantity=1,
            unit_price=Decimal("120.00"),
            line_total=Decimal("120.00"),
        )
        invoice.refresh_totals()

        self.client.login(username="alicebilling", password="testpass123")
        response = self.client.post(
            reverse("billing:pay_invoice", args=[invoice.id]),
            {
                f"invoice-{invoice.id}-payment_method": method.id,
                f"invoice-{invoice.id}-amount": "50.00",
                f"invoice-{invoice.id}-notes": "First payment",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "partially_paid")
        self.assertEqual(invoice.balance_due, Decimal("70.00"))
        self.assertTrue(Payment.objects.filter(invoice=invoice, amount=Decimal("50.00")).exists())
