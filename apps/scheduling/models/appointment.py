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

    class Meta:
        ordering = ["scheduled_start"]

    def __str__(self) -> str:
        return f"Appointment<{self.patient.user.username} with {self.provider}>"