from django.db import models

from apps.profiles.models import StaffProfile
from apps.scheduling.models import Appointment

from .patient_record import PatientRecord


class SupportingDocumentType(models.TextChoices):
    PDF = "pdf", "PDF"
    IMAGE = "image", "Image"
    FORM = "form", "Form"
    OTHER = "other", "Other"


class SupportingDocument(models.Model):
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name="supporting_documents",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supporting_documents",
    )
    uploaded_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
    )
    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=20,
        choices=SupportingDocumentType.choices,
        default=SupportingDocumentType.OTHER,
    )
    file_path = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title