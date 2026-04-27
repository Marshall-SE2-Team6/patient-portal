from django.db import models

from apps.profiles.models import PatientProfile

from .appointment_request import AppointmentRequest
from .provider import Provider


class AppointmentStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CHECKED_IN = "checked_in", "Checked In"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"


class Appointment(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    appointment_request = models.OneToOneField(
        AppointmentRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment",
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["scheduled_start"]

    def __str__(self) -> str:
        return f"Appointment<{self.patient.user.username} with {self.provider}>"

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.scheduled_start >= timezone.now()

    @property
    def can_pre_check_in(self):
        from django.utils import timezone

        return (
            self.status == AppointmentStatus.SCHEDULED
            and self.scheduled_end >= timezone.now()
        )

    @property
    def has_pre_check_in(self):
        return hasattr(self, "pre_check_in_record")


    @property
    def needs_reminder(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == AppointmentStatus.SCHEDULED
            and not self.reminder_sent
            and now <= self.scheduled_start <= now + timezone.timedelta(hours=24)
        )
