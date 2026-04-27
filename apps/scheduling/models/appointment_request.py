from django.db import models

from apps.profiles.models import PatientProfile

from .provider import Provider


class AppointmentRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class AppointmentRequest(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="appointment_requests",
    )
    preferred_provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_for_requests",
    )
    requested_start = models.DateTimeField(null=True, blank=True)
    requested_end = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=AppointmentRequestStatus.choices,
        default=AppointmentRequestStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"AppointmentRequest<{self.patient.user.username}>"

    def approve(self):
        from .appointment import Appointment, AppointmentStatus

        if not self.preferred_provider:
            raise ValueError("Appointment requests need a provider before approval.")
        if not self.requested_start or not self.requested_end:
            raise ValueError("Appointment requests need start and end times before approval.")

        appointment, _ = Appointment.objects.update_or_create(
            appointment_request=self,
            defaults={
                "patient": self.patient,
                "provider": self.preferred_provider,
                "scheduled_start": self.requested_start,
                "scheduled_end": self.requested_end,
                "reason": self.reason,
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        self.status = AppointmentRequestStatus.APPROVED
        self.save(update_fields=["status", "updated_at"])
        return appointment

    def reject(self):
        from .appointment import AppointmentStatus

        self.status = AppointmentRequestStatus.REJECTED
        self.save(update_fields=["status", "updated_at"])

        appointment = getattr(self, "appointment", None)
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])

    def cancel(self):
        from .appointment import AppointmentStatus

        self.status = AppointmentRequestStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

        appointment = getattr(self, "appointment", None)
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])
