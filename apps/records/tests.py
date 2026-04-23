from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models.patient_profile import PatientProfile
from apps.records.models.patient_record import PatientRecord
from apps.records.models.record_flag import RecordFlag, RecordFlagType


class RecordModelTests(TestCase):
    def test_record_flag_defaults_and_string_representation(self) -> None:
        user = get_user_model().objects.create_user(
            username="patientuser",
            password="testpass123",
        )

        patient_profile = PatientProfile.objects.create(user=user)

        patient_record = PatientRecord.objects.create(patient=patient_profile)

        record_flag = RecordFlag.objects.create(
            patient_record=patient_record,
            reason="Administrative review required",
        )

        self.assertEqual(record_flag.flag_type, RecordFlagType.ADMIN)
        self.assertTrue(record_flag.is_active)
        self.assertEqual(str(record_flag), "admin flag")
