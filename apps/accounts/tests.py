from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.core import mail

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.records.models import ClinicalNote, LabOrder, VitalsRecord
from apps.scheduling.models import Appointment, AppointmentRequest, AppointmentRequestStatus, AppointmentStatus, Provider


class AccountsViewTests(TestCase):
    def test_login_page_loads(self) -> None:
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_signup_saves_patient_email(self) -> None:
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Alice",
                "last_name": "Portal",
                "username": "portalalice",
                "email": "alice@example.com",
                "phone_number": "555-111-2222",
                "date_of_birth": "1998-04-21",
                "address": "123 Main Street",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username="portalalice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(PatientProfile.objects.filter(user=user, phone_number="555-111-2222").exists())

    def test_password_reset_request_sends_email(self) -> None:
        user = get_user_model().objects.create_user(
            username="resetuser",
            password="testpass123",
            email="reset@example.com",
        )
        PatientProfile.objects.create(user=user)

        response = self.client.post(
            reverse("password_reset"),
            {"email": "reset@example.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_done.html")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Marco's Medical Portal password reset", mail.outbox[0].subject)

    def test_edit_profile_updates_patient_profile_fields(self) -> None:
        user = get_user_model().objects.create_user(
            username="profileuser",
            password="testpass123",
            email="old@example.com",
            first_name="Old",
            last_name="Name",
        )
        PatientProfile.objects.create(user=user)

        self.client.login(username="profileuser", password="testpass123")
        response = self.client.post(
            reverse("edit_profile"),
            {
                "first_name": "New",
                "last_name": "Patient",
                "email": "new@example.com",
                "phone_number": "555-333-4444",
                "date_of_birth": "1995-06-15",
                "address_line_1": "10 Market Street",
                "address_line_2": "Unit 5",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02110",
                "emergency_contact_name": "Jordan Patient",
                "emergency_contact_phone": "555-999-0000",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        user.patient_profile.refresh_from_db()
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.patient_profile.phone_number, "555-333-4444")
        self.assertEqual(user.patient_profile.city, "Boston")
        self.assertEqual(user.patient_profile.emergency_contact_name, "Jordan Patient")


class StaffPortalRoutingTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()

        self.reception_user = user_model.objects.create_user(
            username="frontdeskportal",
            password="testpass123",
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=self.reception_user,
            staff_role=StaffRole.RECEPTIONIST,
        )

        self.admin_user = user_model.objects.create_user(
            username="siteadmin",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

    def test_receptionist_redirects_to_front_desk_dashboard(self) -> None:
        self.client.login(username="frontdeskportal", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("receptionist_dashboard"))

    def test_receptionist_cannot_open_admin_dashboard(self) -> None:
        self.client.login(username="frontdeskportal", password="testpass123")
        response = self.client.get(reverse("admin_dashboard"), follow=True)
        self.assertRedirects(response, reverse("receptionist_dashboard"))

    def test_admin_user_redirects_to_admin_dashboard(self) -> None:
        self.client.login(username="siteadmin", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("admin_dashboard"))


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


class DoctorWorkflowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.doctor_user = user_model.objects.create_user(
            username="drwork",
            password="testpass123",
            role=user_model.Role.PHYSICIAN,
        )
        doctor_staff = StaffProfile.objects.create(
            user=self.doctor_user,
            staff_role=StaffRole.PHYSICIAN,
        )
        self.provider = Provider.objects.create(staff_profile=doctor_staff, specialty="Family Medicine")

        self.patient_user = user_model.objects.create_user(
            username="patwork",
            password="testpass123",
            first_name="Pat",
            last_name="Work",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)
        self.provider.patients.add(self.patient_profile)

    def test_doctor_can_add_clinical_note(self) -> None:
        self.client.login(username="drwork", password="testpass123")
        response = self.client.post(
            reverse("doctor_patient_record_detail", args=[self.patient_profile.id]),
            {
                "action": "add_note",
                "note-title": "Progress Note",
                "note-note_type": "general",
                "note-content": "Patient is stable and improving.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ClinicalNote.objects.filter(title="Progress Note").exists())

    def test_doctor_can_add_lab_order(self) -> None:
        self.client.login(username="drwork", password="testpass123")
        response = self.client.post(
            reverse("doctor_patient_record_detail", args=[self.patient_profile.id]),
            {
                "action": "add_lab_order",
                "lab-order-test_name": "Lipid Panel",
                "lab-order-instructions": "Fasting required",
                "lab-order-status": "ordered",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(LabOrder.objects.filter(test_name="Lipid Panel").exists())


class NurseWorkflowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()

        self.nurse_user = user_model.objects.create_user(
            username="nurseflow",
            password="testpass123",
            first_name="Nora",
            last_name="Nurse",
            is_staff=True,
        )
        self.nurse_staff = StaffProfile.objects.create(
            user=self.nurse_user,
            staff_role=StaffRole.NURSE,
        )

        doctor_user = user_model.objects.create_user(
            username="nurseroute",
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

        self.patient_user = user_model.objects.create_user(
            username="nursepatient",
            password="testpass123",
            first_name="Paula",
            last_name="Patient",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)
        self.appointment = Appointment.objects.create(
            patient=self.patient_profile,
            provider=self.provider,
            scheduled_start=timezone.now() + timedelta(hours=2),
            scheduled_end=timezone.now() + timedelta(hours=3),
            reason="Vitals check",
            status=AppointmentStatus.SCHEDULED,
        )
        self.request = AppointmentRequest.objects.create(
            patient=self.patient_profile,
            preferred_provider=self.provider,
            requested_start=timezone.now() + timedelta(days=2),
            requested_end=timezone.now() + timedelta(days=2, hours=1),
            reason="Pending request",
            status=AppointmentRequestStatus.PENDING,
        )

    def test_nurse_redirects_to_nurse_dashboard(self) -> None:
        self.client.login(username="nurseflow", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("nurse_dashboard"))

    def test_nurse_cannot_approve_appointment_request(self) -> None:
        self.client.login(username="nurseflow", password="testpass123")
        response = self.client.post(
            reverse("approve_appointment_request", args=[self.request.id]),
            {"next": reverse("nurse_dashboard")},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, AppointmentRequestStatus.PENDING)

    def test_nurse_can_record_vitals_from_nurse_chart(self) -> None:
        self.client.login(username="nurseflow", password="testpass123")
        response = self.client.post(
            reverse("nurse_patient_record_detail", args=[self.patient_profile.id]),
            {
                "vitals-height_cm": "170.5",
                "vitals-weight_kg": "68.4",
                "vitals-temperature_c": "37.1",
                "vitals-systolic_bp": "120",
                "vitals-diastolic_bp": "80",
                "vitals-pulse_bpm": "74",
                "vitals-respiratory_rate": "16",
                "vitals-oxygen_saturation": "98",
                "vitals-notes": "Recorded during intake.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(VitalsRecord.objects.filter(patient_record__patient=self.patient_profile).exists())
