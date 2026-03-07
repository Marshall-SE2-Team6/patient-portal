from django.conf import settings
from django.db import models


class StaffRole(models.TextChoices):
    PHYSICIAN = "physician", "Physician"
    NURSE = "nurse", "Nurse"
    RECEPTIONIST = "receptionist", "Receptionist"
    LAB_TECH = "lab_tech", "Lab Tech"
    BILLING = "billing", "Billing"
    ADMIN = "admin", "Admin"


class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    staff_role = models.CharField(
        max_length=32,
        choices=StaffRole.choices,
        default=StaffRole.ADMIN,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    is_active_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"StaffProfile<{self.user.username}>"