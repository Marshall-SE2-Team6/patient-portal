from django.db import models

from apps.profiles.models import StaffProfile

from .patient_record import PatientRecord


class RecordFlagType(models.TextChoices):
    ALLERGY = "allergy", "Allergy"
    RISK = "risk", "Risk"
    FOLLOW_UP = "follow_up", "Follow Up"
    ADMIN = "admin", "Administrative"


class RecordFlag(models.Model):
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name="flags",
    )
    created_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_record_flags",
    )
    flag_type = models.CharField(
        max_length=20,
        choices=RecordFlagType.choices,
        default=RecordFlagType.ADMIN,
    )
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.flag_type} flag"