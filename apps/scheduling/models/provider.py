from django.db import models

from apps.profiles.models import StaffProfile, PatientProfile


class Provider(models.Model):
    staff_profile = models.OneToOneField(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )

    patients = models.ManyToManyField(
        PatientProfile,
        blank=True,
        related_name="providers",
    )

    specialty = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    accepts_new_patients = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Provider<{self.staff_profile.user.username}>"