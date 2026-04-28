from django.db import models
from django.utils import timezone
from decimal import Decimal

from apps.profiles.models import PatientProfile
from apps.scheduling.models import Appointment


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    PAID = "paid", "Paid"
    VOID = "void", "Void"
    OVERDUE = "overdue", "Overdue"


class Invoice(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
    )
    issued_at = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.invoice_number

    def refresh_totals(self) -> None:
        from .payment import PaymentStatus

        subtotal = sum(
            (line.line_total for line in self.line_items.all()),
            Decimal("0.00"),
        )
        total_amount = subtotal + self.tax_amount
        paid_amount = sum(
            (
                payment.amount
                for payment in self.payments.filter(status=PaymentStatus.COMPLETED)
            ),
            Decimal("0.00"),
        )
        balance_due = total_amount - paid_amount

        if balance_due <= Decimal("0.00"):
            self.status = InvoiceStatus.PAID
            balance_due = Decimal("0.00")
        elif paid_amount > Decimal("0.00"):
            self.status = InvoiceStatus.PARTIALLY_PAID
        elif self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.ISSUED

        self.subtotal = subtotal
        self.total_amount = total_amount
        self.balance_due = balance_due
        self.save(update_fields=[
            "status",
            "subtotal",
            "total_amount",
            "balance_due",
            "updated_at",
        ])
