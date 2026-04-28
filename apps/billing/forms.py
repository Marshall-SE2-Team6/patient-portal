from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Payment, PaymentMethod


class PaymentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_method", "amount", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, invoice=None, patient=None, **kwargs):
        self.invoice = invoice
        self.patient = patient
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].queryset = PaymentMethod.objects.filter(
            patient=patient,
            is_active=True,
        ).order_by("-is_default", "nickname", "id")

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0.00"):
            raise forms.ValidationError("Payment amount must be greater than zero.")
        if self.invoice and amount > self.invoice.balance_due:
            raise forms.ValidationError("Payment amount cannot be more than the invoice balance.")
        return amount

    def save(self, commit=True):
        payment = super().save(commit=False)
        payment.invoice = self.invoice
        payment.status = Payment.Status.COMPLETED if hasattr(Payment, "Status") else payment.status
        payment.transaction_reference = (
            f"PAY-{self.invoice.invoice_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        if commit:
            payment.save()

        return payment
