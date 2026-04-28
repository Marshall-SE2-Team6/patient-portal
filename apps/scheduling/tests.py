from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.notifications.models import Notification
from apps.scheduling.models import (
    Appointment,
    AppointmentRequest,
    AppointmentRequestStatus,
    AppointmentStatus,
    AvailabilitySlot,
    CheckInRecord,
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
        start = timezone.now() + timedelta(days=3)
        self.slot = AvailabilitySlot.objects.create(
            provider=self.provider,
            start_time=start,
            end_time=start + timedelta(hours=1),
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

        response = self.client.post(
            reverse("request_appointment"),
            {
                "provider": self.provider.id,
                "requested_slot": self.slot.id,
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
        self.assertEqual(appointment_request.requested_slot, self.slot)
        self.assertEqual(appointment_request.requested_start.replace(second=0, microsecond=0), self.slot.start_time.replace(second=0, microsecond=0))
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


class AppointmentLifecycleTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.patient_user = user_model.objects.create_user(
            username="alice2",
            password="testpass123",
            first_name="Alice",
            last_name="Stone",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)

        doctor_user = user_model.objects.create_user(
            username="doctorlifecycle",
            password="testpass123",
            role=user_model.Role.PHYSICIAN,
        )
        doctor_staff = StaffProfile.objects.create(
            user=doctor_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.provider = Provider.objects.create(
            staff_profile=doctor_staff,
            specialty="Family Medicine",
        )

        self.frontdesk_user = user_model.objects.create_user(
            username="frontdesk2",
            password="testpass123",
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=self.frontdesk_user,
            staff_role=StaffRole.RECEPTIONIST,
        )

        start = timezone.now() + timedelta(minutes=30)
        self.original_slot = AvailabilitySlot.objects.create(
            provider=self.provider,
            start_time=start,
            end_time=start + timedelta(hours=1),
        )
        self.new_slot = AvailabilitySlot.objects.create(
            provider=self.provider,
            start_time=start + timedelta(days=1),
            end_time=start + timedelta(days=1, hours=1),
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient_profile,
            provider=self.provider,
            availability_slot=self.original_slot,
            scheduled_start=self.original_slot.start_time,
            scheduled_end=self.original_slot.end_time,
            reason="Consultation",
            status=AppointmentStatus.SCHEDULED,
        )
        self.original_slot.is_booked = True
        self.original_slot.save(update_fields=["is_booked"])

    def test_patient_can_reschedule_to_open_slot(self) -> None:
        self.client.login(username="alice2", password="testpass123")

        response = self.client.post(
            reverse("reschedule_appointment", args=[self.appointment.id]),
            {"slot": self.new_slot.id},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.original_slot.refresh_from_db()
        self.new_slot.refresh_from_db()

        self.assertEqual(self.appointment.availability_slot, self.new_slot)
        self.assertFalse(self.original_slot.is_booked)
        self.assertTrue(self.new_slot.is_booked)
        self.assertTrue(Notification.objects.filter(appointment=self.appointment, subject="Appointment Rescheduled").exists())

    def test_patient_can_cancel_upcoming_appointment(self) -> None:
        self.client.login(username="alice2", password="testpass123")

        response = self.client.post(
            reverse("cancel_appointment", args=[self.appointment.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.original_slot.refresh_from_db()

        self.assertEqual(self.appointment.status, AppointmentStatus.CANCELLED)
        self.assertFalse(self.original_slot.is_booked)

    def test_receptionist_can_check_in_patient(self) -> None:
        self.client.login(username="frontdesk2", password="testpass123")

        response = self.client.post(
            reverse("check_in_appointment", args=[self.appointment.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CHECKED_IN)
        self.assertTrue(CheckInRecord.objects.filter(appointment=self.appointment).exists())

    def test_receptionist_cannot_check_in_future_day_appointment(self) -> None:
        self.appointment.scheduled_start = timezone.now() + timedelta(days=2)
        self.appointment.scheduled_end = timezone.now() + timedelta(days=2, hours=1)
        self.appointment.save(update_fields=["scheduled_start", "scheduled_end"])

        self.client.login(username="frontdesk2", password="testpass123")
        response = self.client.post(
            reverse("check_in_appointment", args=[self.appointment.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.SCHEDULED)
        self.assertContains(
            response,
            "Patients can only be checked in for scheduled appointments happening today.",
        )

    def test_staff_can_directly_schedule_appointment_from_slot(self) -> None:
        self.client.login(username="frontdesk2", password="testpass123")

        patient_user = get_user_model().objects.create_user(
            username="bookme",
            password="testpass123",
            first_name="Book",
            last_name="Me",
        )
        patient_profile = PatientProfile.objects.create(user=patient_user)
        staff_slot = AvailabilitySlot.objects.create(
            provider=self.provider,
            start_time=timezone.now() + timedelta(days=6),
            end_time=timezone.now() + timedelta(days=6, hours=1),
        )

        response = self.client.post(
            reverse("staff_schedule_appointment"),
            {
                "patient": patient_profile.id,
                "slot": staff_slot.id,
                "reason": "Front desk booking",
                "notes": "Booked by staff",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Appointment.objects.filter(
                patient=patient_profile,
                availability_slot=staff_slot,
                reason="Front desk booking",
            ).exists()
        )
        staff_slot.refresh_from_db()
        self.assertTrue(staff_slot.is_booked)


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
