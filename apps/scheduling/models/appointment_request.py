from django.db import models
from django.utils import timezone

from apps.profiles.models import PatientProfile

from .availability_slot import AvailabilitySlot
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
    requested_slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_requests",
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
        if self.requested_slot:
            if self.requested_slot.is_booked and getattr(self.requested_slot, "appointment_id", None) != getattr(getattr(self, "appointment", None), "id", None):
                raise ValueError("That requested slot is no longer available.")
            self.requested_start = self.requested_slot.start_time
            self.requested_end = self.requested_slot.end_time
            self.preferred_provider = self.requested_slot.provider
        if not self.requested_start or not self.requested_end:
            raise ValueError("Appointment requests need start and end times before approval.")

        appointment, _ = Appointment.objects.update_or_create(
            appointment_request=self,
            defaults={
                "patient": self.patient,
                "provider": self.preferred_provider,
                "availability_slot": self.requested_slot,
                "scheduled_start": self.requested_start,
                "scheduled_end": self.requested_end,
                "reason": self.reason,
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        self.status = AppointmentRequestStatus.APPROVED
        self.save(update_fields=["status", "requested_start", "requested_end", "updated_at"])

        if self.requested_slot and not self.requested_slot.is_booked:
            self.requested_slot.is_booked = True
            self.requested_slot.save(update_fields=["is_booked"])

        appointment.send_notification(
            subject="Appointment Approved",
            message=(
                f"Your appointment request for "
                f"{appointment.scheduled_start.strftime('%B %d, %Y at %I:%M %p')} "
                f"has been approved."
            ),
            notification_type="appointment_status",
        )
        return appointment

    def reject(self):
        from .appointment import AppointmentStatus
        from apps.notifications.models import Notification, NotificationStatus

        self.status = AppointmentRequestStatus.REJECTED
        self.save(update_fields=["status", "updated_at"])

        appointment = getattr(self, "appointment", None)
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])
            appointment._release_slot()
            appointment.send_notification(
                subject="Appointment Request Rejected",
                message="Your appointment request was reviewed and could not be scheduled.",
                notification_type="appointment_status",
            )
        else:
            Notification.objects.create(
                recipient=self.patient.user,
                subject="Appointment Request Rejected",
                message="Your appointment request was reviewed and could not be scheduled.",
                notification_type="appointment_status",
                status=NotificationStatus.SENT,
                sent_at=timezone.now(),
            )

    def cancel(self):
        from .appointment import AppointmentStatus

        self.status = AppointmentRequestStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

        appointment = getattr(self, "appointment", None)
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])
            appointment._release_slot()
