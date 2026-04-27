from django.db import models

from apps.profiles.models import StaffProfile

from .appointment import Appointment


class CheckInRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="check_in_record",
    )
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_check_ins",
    )
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"CheckInRecord<appointment={self.appointment_id}>"
