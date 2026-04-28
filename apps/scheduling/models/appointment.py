from django.db import models
from django.utils import timezone

from apps.profiles.models import PatientProfile

from .appointment_request import AppointmentRequest
from .availability_slot import AvailabilitySlot
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
    availability_slot = models.OneToOneField(
        AvailabilitySlot,
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
        return self.scheduled_start >= timezone.now()

    @property
    def can_pre_check_in(self):
        return (
            self.status in {AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN}
            and self.scheduled_end >= timezone.now()
        )

    @property
    def has_pre_check_in(self):
        return hasattr(self, "pre_check_in_record")


    @property
    def needs_reminder(self):
        now = timezone.now()
        return (
            self.status == AppointmentStatus.SCHEDULED
            and not self.reminder_sent
            and now <= self.scheduled_start <= now + timezone.timedelta(hours=24)
        )

    @property
    def can_reschedule(self):
        return self.status == AppointmentStatus.SCHEDULED and self.scheduled_start > timezone.now()

    @property
    def can_cancel(self):
        return self.status in {AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN} and self.scheduled_start > timezone.now()

    @property
    def can_check_in(self):
        now = timezone.now()
        today = timezone.localdate()
        return (
            self.status == AppointmentStatus.SCHEDULED
            and self.scheduled_end >= now
            and self.scheduled_start.astimezone(timezone.get_current_timezone()).date() == today
        )

    def _release_slot(self) -> None:
        slot = self.availability_slot
        if slot and slot.is_booked:
            slot.is_booked = False
            slot.save(update_fields=["is_booked"])

    def _book_slot(self, slot: AvailabilitySlot) -> None:
        if slot.is_booked and slot.appointment_id != self.id:
            raise ValueError("That time slot is no longer available.")

        slot.is_booked = True
        slot.save(update_fields=["is_booked"])
        self.availability_slot = slot
        self.provider = slot.provider
        self.scheduled_start = slot.start_time
        self.scheduled_end = slot.end_time

    def send_notification(self, subject: str, message: str, notification_type: str) -> None:
        from apps.notifications.models import Notification, NotificationStatus

        Notification.objects.create(
            recipient=self.patient.user,
            subject=subject,
            message=message,
            appointment=self,
            notification_type=notification_type,
            status=NotificationStatus.SENT,
            sent_at=timezone.now(),
        )

    def transition_status(self, new_status: str, *, actor_label: str = "Staff") -> None:
        allowed_transitions = {
            AppointmentStatus.SCHEDULED: {
                AppointmentStatus.CHECKED_IN,
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW,
                AppointmentStatus.COMPLETED,
            },
            AppointmentStatus.CHECKED_IN: {
                AppointmentStatus.COMPLETED,
                AppointmentStatus.NO_SHOW,
                AppointmentStatus.CANCELLED,
            },
            AppointmentStatus.COMPLETED: set(),
            AppointmentStatus.CANCELLED: set(),
            AppointmentStatus.NO_SHOW: set(),
        }

        if new_status == self.status:
            return

        allowed = allowed_transitions.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Appointments cannot move from {self.get_status_display()} to "
                f"{AppointmentStatus(new_status).label}."
            )

        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

        self.send_notification(
            subject=f"Appointment {AppointmentStatus(new_status).label}",
            message=(
                f"{actor_label} updated your appointment on "
                f"{self.scheduled_start.strftime('%B %d, %Y at %I:%M %p')} "
                f"to {AppointmentStatus(new_status).label}."
            ),
            notification_type="appointment_status",
        )

    def reschedule_to_slot(self, slot: AvailabilitySlot, *, actor_label: str = "Staff") -> None:
        if not self.can_reschedule:
            raise ValueError("Only future scheduled appointments can be rescheduled.")

        old_start = self.scheduled_start
        old_slot = self.availability_slot

        if old_slot and old_slot.id == slot.id:
            raise ValueError("Please choose a different time slot.")

        self._book_slot(slot)
        self.status = AppointmentStatus.SCHEDULED
        self.save(update_fields=[
            "availability_slot",
            "provider",
            "scheduled_start",
            "scheduled_end",
            "status",
            "updated_at",
        ])

        if old_slot:
            old_slot.is_booked = False
            old_slot.save(update_fields=["is_booked"])

        self.send_notification(
            subject="Appointment Rescheduled",
            message=(
                f"{actor_label} moved your appointment from "
                f"{old_start.strftime('%B %d, %Y at %I:%M %p')} to "
                f"{self.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}."
            ),
            notification_type="appointment_status",
        )

    def cancel(self, *, actor_label: str = "Staff") -> None:
        if not self.can_cancel:
            raise ValueError("This appointment can no longer be cancelled.")

        self.transition_status(AppointmentStatus.CANCELLED, actor_label=actor_label)
        self._release_slot()

    def check_in(self, *, actor_label: str = "Front Desk") -> None:
        if not self.can_check_in:
            raise ValueError("Patients can only be checked in for scheduled appointments happening today.")
        self.transition_status(AppointmentStatus.CHECKED_IN, actor_label=actor_label)

    def complete(self, *, actor_label: str = "Staff") -> None:
        self.transition_status(AppointmentStatus.COMPLETED, actor_label=actor_label)

    def mark_no_show(self, *, actor_label: str = "Staff") -> None:
        self.transition_status(AppointmentStatus.NO_SHOW, actor_label=actor_label)
