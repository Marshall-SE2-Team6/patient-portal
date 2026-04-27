from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models.patient_profile import PatientProfile
from apps.profiles.models.staff_profile import StaffProfile, StaffRole


class ProfileModelTests(TestCase):
    def test_staff_profile_defaults_are_applied(self) -> None:
        user = get_user_model().objects.create_user(
            username="staffuser",
            password="testpass123",
        )

        profile = StaffProfile.objects.create(user=user)

        self.assertEqual(profile.staff_role, StaffRole.ADMIN)
        self.assertTrue(profile.is_active_staff)


def test_patient_profile_string_representation(self) -> None:
    user = get_user_model().objects.create_user(
        username="patientprofileuser",
        password="testpass123",
    )

    profile = PatientProfile.objects.create(user=user)

    self.assertEqual(str(profile), "PatientProfile<patientprofileuser>")