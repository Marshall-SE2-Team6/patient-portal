from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.records.models import ClinicalNote, ClinicalNoteType, PatientRecord, Prescription, RecordFlag, RecordFlagType, VitalsRecord


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

    def test_patient_record_string_representation(self) -> None:
        user = get_user_model().objects.create_user(
            username="recorduser",
            password="testpass123",
        )
        patient_profile = PatientProfile.objects.create(user=user)
        patient_record = PatientRecord.objects.create(patient=patient_profile)

        self.assertEqual(str(patient_record), "PatientRecord<recorduser>")


class PatientRecordsViewTests(TestCase):
    def test_my_records_shows_prescriptions_and_notes(self) -> None:
        user_model = get_user_model()
        patient_user = user_model.objects.create_user(username="alice", password="testpass123")
        patient_profile = PatientProfile.objects.create(user=patient_user)
        patient_record = PatientRecord.objects.create(patient=patient_profile)

        doctor_user = user_model.objects.create_user(username="drnotes", password="testpass123")
        doctor_staff = StaffProfile.objects.create(user=doctor_user, staff_role=StaffRole.PHYSICIAN)

        Prescription.objects.create(
            patient_record=patient_record,
            prescribed_by=doctor_staff,
            medication_name="Amoxicillin",
            dosage="500 mg",
            frequency="Twice daily",
            instructions="Take with food.",
        )
        ClinicalNote.objects.create(
            patient_record=patient_record,
            author=doctor_staff,
            title="Follow-up Note",
            note_type=ClinicalNoteType.GENERAL,
            content="Patient improving with medication.",
        )

        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("records:my_records"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amoxicillin")
        self.assertContains(response, "Follow-up Note")

    def test_patient_record_detail_shows_health_chart_data(self) -> None:
        user_model = get_user_model()
        patient_user = user_model.objects.create_user(
            username="chartuser",
            password="testpass123",
            first_name="Casey",
            last_name="Patient",
            email="casey@example.com",
        )
        patient_profile = PatientProfile.objects.create(
            user=patient_user,
            phone_number="555-222-3333",
        )
        patient_record = PatientRecord.objects.create(
            patient=patient_profile,
            blood_type="O+",
            allergies="Peanuts",
            chronic_conditions="Asthma",
            general_notes="Bring inhaler to each visit.",
        )

        doctor_user = user_model.objects.create_user(username="drchart", password="testpass123")
        doctor_staff = StaffProfile.objects.create(user=doctor_user, staff_role=StaffRole.PHYSICIAN)

        VitalsRecord.objects.create(
            patient_record=patient_record,
            recorded_by=doctor_staff,
            height_cm=170,
            weight_kg=68,
            pulse_bpm=72,
        )
        Prescription.objects.create(
            patient_record=patient_record,
            prescribed_by=doctor_staff,
            medication_name="Albuterol",
            dosage="2 puffs",
            frequency="As needed",
            instructions="Use during breathing flare-ups.",
        )
        ClinicalNote.objects.create(
            patient_record=patient_record,
            author=doctor_staff,
            title="Asthma Follow-up",
            note_type=ClinicalNoteType.GENERAL,
            content="Symptoms are stable.",
        )

        self.client.login(username="chartuser", password="testpass123")
        response = self.client.get(reverse("records:patient_record_detail"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Read-Only Health Chart")
        self.assertContains(response, "O+")
        self.assertContains(response, "Peanuts")
        self.assertContains(response, "Albuterol")
        self.assertContains(response, "Asthma Follow-up")
