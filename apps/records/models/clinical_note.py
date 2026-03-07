from django.db import models

from apps.profiles.models import StaffProfile
from apps.scheduling.models import Appointment

from .patient_record import PatientRecord


class ClinicalNoteType(models.TextChoices):
    GENERAL = "general", "General"
    SOAP = "soap", "SOAP"
    CONSULT = "consult", "Consult"
    DISCHARGE = "discharge", "Discharge"


class ClinicalNote(models.Model):
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name="clinical_notes",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_notes",
    )
    author = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_clinical_notes",
    )
    title = models.CharField(max_length=255)
    note_type = models.CharField(
        max_length=20,
        choices=ClinicalNoteType.choices,
        default=ClinicalNoteType.GENERAL,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"ClinicalNote<{self.title}>"