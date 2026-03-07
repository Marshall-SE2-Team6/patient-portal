from django.db import models
from django.utils import timezone

from apps.profiles.models import StaffProfile

from .lab_order import LabOrder


class LabResultStatus(models.TextChoices):
    PRELIMINARY = "preliminary", "Preliminary"
    FINAL = "final", "Final"
    AMENDED = "amended", "Amended"


class LabResult(models.Model):
    lab_order = models.OneToOneField(
        LabOrder,
        on_delete=models.CASCADE,
        related_name="result",
    )
    reviewed_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_lab_results",
    )
    result_summary = models.TextField()
    result_value = models.CharField(max_length=100, blank=True)
    units = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=LabResultStatus.choices,
        default=LabResultStatus.FINAL,
    )
    resulted_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"LabResult<order={self.lab_order_id}>"