from django.db import models

from apps.profiles.models import StaffProfile

from .patient_record import PatientRecord


class MedicalSummary(models.Model):
    patient_record = models.OneToOneField(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name="medical_summary",
    )
    summary_text = models.TextField(blank=True)
    last_updated_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_medical_summaries",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"MedicalSummary<{self.patient_record.patient.user.username}>"