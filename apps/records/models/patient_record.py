from django.db import models

from apps.profiles.models import PatientProfile
from apps.scheduling.models import Provider


class PatientRecord(models.Model):
    patient = models.OneToOneField(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="record",
    )
    primary_provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_patient_records",
    )
    blood_type = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    general_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"PatientRecord<{self.patient.user.username}>"