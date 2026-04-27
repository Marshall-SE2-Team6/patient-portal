from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.scheduling.models import (
    Appointment,
    AppointmentRequest,
    AppointmentRequestStatus,
    AppointmentStatus,
    PreCheckInRecord,
    Provider,
)


class SchedulingViewTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.patient_user = user_model.objects.create_user(
            username="alice",
            password="testpass123",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)

        provider_user = user_model.objects.create_user(
            username="doctor2",
            password="testpass123",
            role=user_model.Role.PHYSICIAN,
        )
        staff_profile = StaffProfile.objects.create(
            user=provider_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.provider = Provider.objects.create(
            staff_profile=staff_profile,
            specialty="Internal Medicine",
        )

    def test_request_appointment_requires_login(self) -> None:
        response = self.client.get(reverse("request_appointment"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_my_appointments_profile_missing_for_user_without_patient_profile(self) -> None:
        user = get_user_model().objects.create_user(
            username="scheduser",
            password="testpass123",
        )
        self.client.login(username="scheduser", password="testpass123")

        response = self.client.get(reverse("my_appointments"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["profile_missing"])
        self.assertEqual(list(response.context["appointments"]), [])

    def test_request_appointment_creates_pending_request_not_appointment(self) -> None:
        self.client.login(username="alice", password="testpass123")

        start = timezone.now() + timedelta(days=3)
        end = start + timedelta(hours=1)

        response = self.client.post(
            reverse("request_appointment"),
            {
                "provider": self.provider.id,
                "scheduled_start": start.strftime("%Y-%m-%dT%H:%M"),
                "scheduled_end": end.strftime("%Y-%m-%dT%H:%M"),
                "reason": "Follow-up visit",
                "notes": "Morning preferred.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "will stay pending until a doctor or receptionist approves it")
        self.assertEqual(Appointment.objects.count(), 0)

        appointment_request = AppointmentRequest.objects.get(patient=self.patient_profile)
        self.assertEqual(appointment_request.status, AppointmentRequestStatus.PENDING)
        self.assertEqual(appointment_request.preferred_provider, self.provider)
        self.assertEqual(appointment_request.requested_start.replace(second=0, microsecond=0), start.replace(second=0, microsecond=0))
        self.assertIn("Follow-up visit", appointment_request.reason)
        self.assertIn("Patient notes: Morning preferred.", appointment_request.reason)

    def test_my_appointments_shows_pending_requests(self) -> None:
        AppointmentRequest.objects.create(
            patient=self.patient_profile,
            preferred_provider=self.provider,
            requested_start=timezone.now() + timedelta(days=1),
            requested_end=timezone.now() + timedelta(days=1, hours=1),
            reason="Annual visit",
            status=AppointmentRequestStatus.PENDING,
        )

        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("my_appointments"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pending_requests"].count(), 1)
        self.assertContains(response, "Pending Approval")


class PreCheckInViewTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()

        self.patient_user = user_model.objects.create_user(
            username="patient1",
            password="testpass123",
            first_name="Pat",
            last_name="Jones",
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            phone_number="111-111-1111",
            address_line_1="100 Main St",
            city="Boston",
            state="MA",
            postal_code="02110",
            emergency_contact_name="Alex Jones",
            emergency_contact_phone="222-222-2222",
        )

        doctor_user = user_model.objects.create_user(
            username="doctor1",
            password="testpass123",
            first_name="Morgan",
            last_name="Lee",
            role=user_model.Role.PHYSICIAN,
        )
        doctor_staff_profile = StaffProfile.objects.create(
            user=doctor_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.provider = Provider.objects.create(
            staff_profile=doctor_staff_profile,
            specialty="Family Medicine",
        )

        start = timezone.now() + timedelta(days=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient_profile,
            provider=self.provider,
            scheduled_start=start,
            scheduled_end=start + timedelta(hours=1),
            reason="Annual checkup",
            status=AppointmentStatus.SCHEDULED,
        )

    def test_pre_check_in_requires_login(self) -> None:
        response = self.client.get(reverse("pre_check_in", args=[self.appointment.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_patient_can_submit_pre_check_in_and_profile_is_updated(self) -> None:
        self.client.login(username="patient1", password="testpass123")

        response = self.client.post(
            reverse("pre_check_in", args=[self.appointment.id]),
            {
                "phone_number": "333-333-3333",
                "address_line_1": "400 Elm St",
                "address_line_2": "Apt 2",
                "city": "Cambridge",
                "state": "MA",
                "postal_code": "02139",
                "emergency_contact_name": "Jamie Jones",
                "emergency_contact_phone": "444-444-4444",
                "symptoms": "Cough and fever",
                "current_medications": "Ibuprofen",
                "allergies": "Peanuts",
                "insurance_provider": "Blue Cross",
                "insurance_member_id": "MEM123",
                "accommodation_notes": "Wheelchair assistance",
                "additional_notes": "Please keep visit brief.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pre-check-in submitted successfully.")

        record = PreCheckInRecord.objects.get(appointment=self.appointment)
        self.assertEqual(record.symptoms, "Cough and fever")
        self.assertEqual(record.insurance_provider, "Blue Cross")

        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.phone_number, "333-333-3333")
        self.assertEqual(self.patient_profile.address_line_1, "400 Elm St")
        self.assertEqual(self.patient_profile.emergency_contact_name, "Jamie Jones")

    def test_patient_cannot_pre_check_in_for_past_appointment(self) -> None:
        self.appointment.scheduled_start = timezone.now() - timedelta(days=2)
        self.appointment.scheduled_end = timezone.now() - timedelta(days=2, hours=-1)
        self.appointment.save()

        self.client.login(username="patient1", password="testpass123")
        response = self.client.get(
            reverse("pre_check_in", args=[self.appointment.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Pre-check-in is only available for scheduled visits that have not ended yet.",
        )
        self.assertFalse(PreCheckInRecord.objects.filter(appointment=self.appointment).exists())

    def test_patient_cannot_access_another_patients_pre_check_in(self) -> None:
        other_user = get_user_model().objects.create_user(
            username="otherpatient",
            password="testpass123",
        )
        other_profile = PatientProfile.objects.create(user=other_user)

        self.client.login(username="otherpatient", password="testpass123")
        response = self.client.get(reverse("pre_check_in", args=[self.appointment.id]))

        self.assertEqual(response.status_code, 404)
