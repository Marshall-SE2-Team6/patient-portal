from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.billing.models import Invoice
from apps.scheduling.models import Appointment


class NotificationType(models.TextChoices):
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
    APPOINTMENT_STATUS = "appointment_status", "Appointment Status"
    BILLING_UPDATE = "billing_update", "Billing Update"
    SYSTEM = "system", "System"
    GENERAL = "general", "General"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In App"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    READ = "read", "Read"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    channel = models.CharField(
        max_length=16,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    status = models.CharField(
        max_length=16,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_as_read(self) -> None:
        self.status = NotificationStatus.READ
        self.read_at = timezone.now()
        self.save(update_fields=["status", "read_at"])

    def __str__(self) -> str:
        return f"Notification<{self.recipient.username}: {self.notification_type}>"