from django.db import models

from apps.profiles.models import PatientProfile


class PaymentMethodType(models.TextChoices):
    CREDIT_CARD = "credit_card", "Credit Card"
    DEBIT_CARD = "debit_card", "Debit Card"
    BANK_ACCOUNT = "bank_account", "Bank Account"
    CASH = "cash", "Cash"
    OTHER = "other", "Other"


class PaymentMethod(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    method_type = models.CharField(
        max_length=20,
        choices=PaymentMethodType.choices,
        default=PaymentMethodType.CREDIT_CARD,
    )
    nickname = models.CharField(max_length=100, blank=True)
    cardholder_name = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=50, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    expiration_month = models.PositiveSmallIntegerField(null=True, blank=True)
    expiration_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        label = self.nickname or self.get_method_type_display()
        return f"{label} ({self.last4})" if self.last4 else label