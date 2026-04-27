from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.scheduling.models import Appointment, AppointmentRequest, AppointmentRequestStatus, Provider


class AccountsViewTests(TestCase):
    def test_login_page_loads(self) -> None:
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")


class AppointmentRequestApprovalTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()

        self.patient_user = user_model.objects.create_user(
            username="alice",
            password="testpass123",
            first_name="Alice",
            last_name="Patient",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)

        self.doctor_user = user_model.objects.create_user(
            username="drlee",
            password="testpass123",
            first_name="Dana",
            last_name="Lee",
            role=user_model.Role.PHYSICIAN,
        )
        doctor_staff = StaffProfile.objects.create(
            user=self.doctor_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.provider = Provider.objects.create(
            staff_profile=doctor_staff,
            specialty="Family Medicine",
        )

        self.reception_user = user_model.objects.create_user(
            username="frontdesk",
            password="testpass123",
            first_name="Fran",
            last_name="Desk",
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=self.reception_user,
            staff_role=StaffRole.RECEPTIONIST,
        )

        self.other_doctor_user = user_model.objects.create_user(
            username="drother",
            password="testpass123",
            first_name="Owen",
            last_name="Hart",
            role=user_model.Role.PHYSICIAN,
        )
        other_doctor_staff = StaffProfile.objects.create(
            user=self.other_doctor_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.other_provider = Provider.objects.create(
            staff_profile=other_doctor_staff,
            specialty="Cardiology",
        )

        start = timezone.now() + timedelta(days=5)
        self.appointment_request = AppointmentRequest.objects.create(
            patient=self.patient_profile,
            preferred_provider=self.provider,
            requested_start=start,
            requested_end=start + timedelta(hours=1),
            reason="Annual wellness visit",
            status=AppointmentRequestStatus.PENDING,
        )

    def test_receptionist_can_approve_request_and_create_appointment(self) -> None:
        self.client.login(username="frontdesk", password="testpass123")

        response = self.client.post(
            reverse("approve_appointment_request", args=[self.appointment_request.id]),
            {"next": reverse("admin_dashboard")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment_request.refresh_from_db()
        self.assertEqual(self.appointment_request.status, AppointmentRequestStatus.APPROVED)

        appointment = Appointment.objects.get(appointment_request=self.appointment_request)
        self.assertEqual(appointment.patient, self.patient_profile)
        self.assertEqual(appointment.provider, self.provider)
        self.assertEqual(appointment.reason, self.appointment_request.reason)

    def test_doctor_can_only_approve_own_requests(self) -> None:
        self.client.login(username="drother", password="testpass123")

        response = self.client.post(
            reverse("approve_appointment_request", args=[self.appointment_request.id]),
            {"next": reverse("doctor_dashboard")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment_request.refresh_from_db()
        self.assertEqual(self.appointment_request.status, AppointmentRequestStatus.PENDING)
        self.assertFalse(Appointment.objects.filter(appointment_request=self.appointment_request).exists())

    def test_doctor_can_approve_own_request(self) -> None:
        self.client.login(username="drlee", password="testpass123")

        response = self.client.post(
            reverse("approve_appointment_request", args=[self.appointment_request.id]),
            {"next": reverse("doctor_dashboard")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.appointment_request.refresh_from_db()
        self.assertEqual(self.appointment_request.status, AppointmentRequestStatus.APPROVED)
        self.assertTrue(Appointment.objects.filter(appointment_request=self.appointment_request).exists())
