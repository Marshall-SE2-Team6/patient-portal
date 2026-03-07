from django.db import models

from apps.profiles.models import StaffProfile
from apps.scheduling.models import Appointment

from .patient_record import PatientRecord


class LabOrderStatus(models.TextChoices):
    ORDERED = "ordered", "Ordered"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class LabOrder(models.Model):
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name="lab_orders",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_orders",
    )
    ordered_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_labs",
    )
    test_name = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=LabOrderStatus.choices,
        default=LabOrderStatus.ORDERED,
    )
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"LabOrder<{self.test_name}>"