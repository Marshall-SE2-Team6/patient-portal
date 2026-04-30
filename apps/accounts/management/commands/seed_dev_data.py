from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.billing.models import (
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentMethodType,
    PaymentStatus,
)
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from apps.profiles.models import PatientProfile, StaffProfile, StaffRole
from apps.records.models import (
    ClinicalNote,
    ClinicalNoteType,
    LabOrder,
    LabOrderStatus,
    LabResult,
    LabResultStatus,
    MedicalSummary,
    Medication,
    PatientRecord,
    Prescription,
    PrescriptionStatus,
    RecordFlag,
    RecordFlagType,
    SupportingDocument,
    SupportingDocumentType,
    VitalsRecord,
)
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

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds development data for the patient portal project."

    @transaction.atomic
    def handle(self, *args, **options):
        dev_password = "DevPass123!"

        self.stdout.write(self.style.WARNING("Seeding development data..."))

        # ------------------------------------------------------------------
        # Users
        # ------------------------------------------------------------------
        admin_user = self._upsert_user(
            username="admin",
            email="admin@patientportal.local",
            password=dev_password,
            is_staff=True,
            is_superuser=True,
            first_name="System",
            last_name="Admin",
        )

        dr_smith_user = self._upsert_user(
            username="drsmith",
            email="drsmith@patientportal.local",
            password=dev_password,
            is_staff=True,
            role=User.Role.PHYSICIAN,
            first_name="John",
            last_name="Smith",
        )

        dr_lee_user = self._upsert_user(
            username="drlee",
            email="drlee@patientportal.local",
            password=dev_password,
            is_staff=True,
            role=User.Role.PHYSICIAN,
            first_name="Maya",
            last_name="Lee",
        )

        nurse_jane_user = self._upsert_user(
            username="nursejane",
            email="nursejane@patientportal.local",
            password=dev_password,
            is_staff=True,
            first_name="Jane",
            last_name="Miller",
        )

        frontdesk_user = self._upsert_user(
            username="frontdesk",
            email="frontdesk@patientportal.local",
            password=dev_password,
            is_staff=True,
            first_name="Rachel",
            last_name="Adams",
        )

        alice_user = self._upsert_user(
            username="alice",
            email="alice@patientportal.local",
            password=dev_password,
            first_name="Alice",
            last_name="Carter",
        )

        bob_user = self._upsert_user(
            username="bob",
            email="bob@patientportal.local",
            password=dev_password,
            first_name="Bob",
            last_name="Nguyen",
        )

        charlie_user = self._upsert_user(
            username="charlie",
            email="charlie@patientportal.local",
            password=dev_password,
            first_name="Charlie",
            last_name="Lopez",
        )

        diana_user = self._upsert_user(
            username="diana",
            email="diana@patientportal.local",
            password=dev_password,
            first_name="Diana",
            last_name="Brooks",
        )

        ethan_user = self._upsert_user(
            username="ethan",
            email="ethan@patientportal.local",
            password=dev_password,
            first_name="Ethan",
            last_name="Reed",
        )

        # ------------------------------------------------------------------
        # Profiles
        # ------------------------------------------------------------------
        alice_profile, _ = PatientProfile.objects.update_or_create(
            user=alice_user,
            defaults={
                "phone_number": "304-555-1001",
                "date_of_birth": "1994-05-14",
                "address_line_1": "101 Oak Street",
                "city": "Huntington",
                "state": "WV",
                "postal_code": "25701",
                "emergency_contact_name": "Ella Carter",
                "emergency_contact_phone": "304-555-2001",
            },
        )

        bob_profile, _ = PatientProfile.objects.update_or_create(
            user=bob_user,
            defaults={
                "phone_number": "304-555-1002",
                "date_of_birth": "1989-11-03",
                "address_line_1": "202 Pine Avenue",
                "city": "Charleston",
                "state": "WV",
                "postal_code": "25301",
                "emergency_contact_name": "Liam Nguyen",
                "emergency_contact_phone": "304-555-2002",
            },
        )

        charlie_profile, _ = PatientProfile.objects.update_or_create(
            user=charlie_user,
            defaults={
                "phone_number": "304-555-1003",
                "date_of_birth": "1978-02-21",
                "address_line_1": "303 Cedar Lane",
                "city": "Morgantown",
                "state": "WV",
                "postal_code": "26505",
                "emergency_contact_name": "Mia Lopez",
                "emergency_contact_phone": "304-555-2003",
            },
        )

        diana_profile, _ = PatientProfile.objects.update_or_create(
            user=diana_user,
            defaults={
                "phone_number": "304-555-1004",
                "date_of_birth": "1991-09-12",
                "address_line_1": "404 Birch Drive",
                "city": "Parkersburg",
                "state": "WV",
                "postal_code": "26101",
                "emergency_contact_name": "Noah Brooks",
                "emergency_contact_phone": "304-555-2004",
            },
        )

        ethan_profile, _ = PatientProfile.objects.update_or_create(
            user=ethan_user,
            defaults={
                "phone_number": "304-555-1005",
                "date_of_birth": "1984-07-30",
                "address_line_1": "505 Walnut Court",
                "city": "Wheeling",
                "state": "WV",
                "postal_code": "26003",
                "emergency_contact_name": "Sophia Reed",
                "emergency_contact_phone": "304-555-2005",
            },
        )

        dr_smith_profile, _ = StaffProfile.objects.update_or_create(
            user=dr_smith_user,
            defaults={
                "staff_role": StaffRole.PHYSICIAN,
                "phone_number": "304-555-3001",
                "department": "Family Medicine",
                "license_number": "PHY-1001",
                "employee_id": "EMP-1001",
                "is_active_staff": True,
            },
        )

        dr_lee_profile, _ = StaffProfile.objects.update_or_create(
            user=dr_lee_user,
            defaults={
                "staff_role": StaffRole.PHYSICIAN,
                "phone_number": "304-555-3002",
                "department": "Internal Medicine",
                "license_number": "PHY-1002",
                "employee_id": "EMP-1002",
                "is_active_staff": True,
            },
        )

        frontdesk_profile, _ = StaffProfile.objects.update_or_create(
            user=frontdesk_user,
            defaults={
                "staff_role": StaffRole.RECEPTIONIST,
                "phone_number": "304-555-3003",
                "department": "Front Desk",
                "license_number": "",
                "employee_id": "EMP-1003",
                "is_active_staff": True,
            },
        )

        nurse_jane_profile, _ = StaffProfile.objects.update_or_create(
            user=nurse_jane_user,
            defaults={
                "staff_role": StaffRole.NURSE,
                "phone_number": "304-555-3004",
                "department": "Clinical Support",
                "license_number": "NUR-1004",
                "employee_id": "EMP-1004",
                "is_active_staff": True,
            },
        )

        StaffProfile.objects.update_or_create(
            user=admin_user,
            defaults={
                "staff_role": StaffRole.ADMIN,
                "phone_number": "304-555-3000",
                "department": "Administration",
                "license_number": "",
                "employee_id": "EMP-1000",
                "is_active_staff": True,
            },
        )

        # ------------------------------------------------------------------
        # Providers
        # ------------------------------------------------------------------
        dr_smith_provider, _ = Provider.objects.update_or_create(
            staff_profile=dr_smith_profile,
            defaults={
                "specialty": "Family Medicine",
                "bio": "Primary care provider focused on preventive medicine.",
                "accepts_new_patients": True,
            },
        )

        dr_lee_provider, _ = Provider.objects.update_or_create(
            staff_profile=dr_lee_profile,
            defaults={
                "specialty": "Internal Medicine",
                "bio": "Internal medicine physician with interest in chronic care.",
                "accepts_new_patients": True,
            },
        )

        # ------------------------------------------------------------------
        # Availability
        # ------------------------------------------------------------------
        slot_1_start = self._dt(days=1, hour=9)
        slot_1_end = self._dt(days=1, hour=10)
        slot_2_start = self._dt(days=1, hour=10)
        slot_2_end = self._dt(days=1, hour=11)
        slot_3_start = self._dt(days=2, hour=13)
        slot_3_end = self._dt(days=2, hour=14)
        today_demo_anchor = (timezone.now() + timedelta(minutes=45)).replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        slot_4_start = today_demo_anchor + timedelta(hours=1)
        slot_4_end = slot_4_start + timedelta(hours=1)
        slot_5_start = self._dt(days=4, hour=11)
        slot_5_end = self._dt(days=4, hour=12)
        slot_6_start = self._dt(days=5, hour=14)
        slot_6_end = self._dt(days=5, hour=15)

        slot_1, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_1_start,
            end_time=slot_1_end,
            defaults={"is_booked": True, "notes": "Seeded slot"},
        )

        slot_2, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_2_start,
            end_time=slot_2_end,
            defaults={"is_booked": False, "notes": "Seeded slot"},
        )

        slot_3, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_3_start,
            end_time=slot_3_end,
            defaults={"is_booked": True, "notes": "Seeded slot"},
        )

        slot_4, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_4_start,
            end_time=slot_4_end,
            defaults={"is_booked": True, "notes": "Today clinic slot"},
        )

        slot_5, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_5_start,
            end_time=slot_5_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_6, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_6_start,
            end_time=slot_6_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_7_start = today_demo_anchor
        slot_7_end = slot_7_start + timedelta(hours=1)
        slot_8_start = self._dt(days=3, hour=9)
        slot_8_end = self._dt(days=3, hour=10)
        slot_9_start = self._dt(days=6, hour=10)
        slot_9_end = self._dt(days=6, hour=11)
        slot_10_start = today_demo_anchor + timedelta(hours=2)
        slot_10_end = slot_10_start + timedelta(hours=1)
        slot_11_start = self._dt(days=1, hour=11)
        slot_11_end = self._dt(days=1, hour=12)
        slot_12_start = self._dt(days=2, hour=9)
        slot_12_end = self._dt(days=2, hour=10)
        slot_13_start = self._dt(days=3, hour=11)
        slot_13_end = self._dt(days=3, hour=12)
        slot_14_start = self._dt(days=4, hour=14)
        slot_14_end = self._dt(days=4, hour=15)
        slot_15_start = self._dt(days=5, hour=9)
        slot_15_end = self._dt(days=5, hour=10)
        slot_16_start = self._dt(days=6, hour=13)
        slot_16_end = self._dt(days=6, hour=14)
        slot_17_start = today_demo_anchor + timedelta(hours=3)
        slot_17_end = slot_17_start + timedelta(hours=1)
        slot_18_start = today_demo_anchor + timedelta(hours=4)
        slot_18_end = slot_18_start + timedelta(hours=1)

        slot_7, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_7_start,
            end_time=slot_7_end,
            defaults={"is_booked": True, "notes": "Today waiting room slot"},
        )

        slot_8, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_8_start,
            end_time=slot_8_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_9, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_9_start,
            end_time=slot_9_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_10, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_10_start,
            end_time=slot_10_end,
            defaults={"is_booked": True, "notes": "Today scheduled follow-up slot"},
        )

        slot_11, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_11_start,
            end_time=slot_11_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_12, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_12_start,
            end_time=slot_12_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_13, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_13_start,
            end_time=slot_13_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_14, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_14_start,
            end_time=slot_14_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_15, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_15_start,
            end_time=slot_15_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_16, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_16_start,
            end_time=slot_16_end,
            defaults={"is_booked": False, "notes": "Future open slot"},
        )

        slot_17, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_lee_provider,
            start_time=slot_17_start,
            end_time=slot_17_end,
            defaults={"is_booked": True, "notes": "Today checked-in follow-up slot"},
        )

        slot_18, _ = AvailabilitySlot.objects.update_or_create(
            provider=dr_smith_provider,
            start_time=slot_18_start,
            end_time=slot_18_end,
            defaults={"is_booked": False, "notes": "Today open demo slot"},
        )

        # ------------------------------------------------------------------
        # Appointment Requests + Appointments
        # ------------------------------------------------------------------
        alice_request, _ = AppointmentRequest.objects.update_or_create(
            patient=alice_profile,
            preferred_provider=dr_smith_provider,
            requested_start=self._dt(days=-1, hour=9),
            defaults={
                "requested_slot": None,
                "requested_end": self._dt(days=-1, hour=10),
                "reason": "Annual wellness visit",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        bob_request, _ = AppointmentRequest.objects.update_or_create(
            patient=bob_profile,
            preferred_provider=dr_lee_provider,
            requested_start=self._dt(days=2, hour=13),
            defaults={
                "requested_slot": slot_3,
                "requested_end": self._dt(days=2, hour=14),
                "reason": "Blood pressure follow-up",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        charlie_pending_request, _ = AppointmentRequest.objects.update_or_create(
            patient=charlie_profile,
            preferred_provider=dr_smith_provider,
            requested_start=slot_6.start_time,
            defaults={
                "requested_slot": slot_6,
                "requested_end": slot_6.end_time,
                "reason": "New patient consultation request",
                "status": AppointmentRequestStatus.PENDING,
            },
        )

        alice_pending_request, _ = AppointmentRequest.objects.update_or_create(
            patient=alice_profile,
            preferred_provider=dr_lee_provider,
            requested_start=slot_5.start_time,
            defaults={
                "requested_slot": slot_5,
                "requested_end": slot_5.end_time,
                "reason": "Review persistent fatigue symptoms",
                "status": AppointmentRequestStatus.PENDING,
            },
        )

        alice_followup_request, _ = AppointmentRequest.objects.update_or_create(
            patient=alice_profile,
            preferred_provider=dr_lee_provider,
            requested_start=slot_9.start_time,
            defaults={
                "requested_slot": slot_9,
                "requested_end": slot_9.end_time,
                "reason": "Lab review and medication follow-up",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        alice_today_request, _ = AppointmentRequest.objects.update_or_create(
            patient=alice_profile,
            preferred_provider=dr_smith_provider,
            requested_start=slot_10.start_time,
            defaults={
                "requested_slot": slot_10,
                "requested_end": slot_10.end_time,
                "reason": "Same-day fatigue follow-up and care plan review",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        diana_request, _ = AppointmentRequest.objects.update_or_create(
            patient=diana_profile,
            preferred_provider=dr_lee_provider,
            requested_start=slot_7.start_time,
            defaults={
                "requested_slot": slot_7,
                "requested_end": slot_7.end_time,
                "reason": "Follow-up for migraine symptoms",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        ethan_rejected_request, _ = AppointmentRequest.objects.update_or_create(
            patient=ethan_profile,
            preferred_provider=dr_smith_provider,
            requested_start=slot_8.start_time,
            defaults={
                "requested_slot": slot_8,
                "requested_end": slot_8.end_time,
                "reason": "Travel clearance consultation",
                "status": AppointmentRequestStatus.REJECTED,
            },
        )

        bob_today_request, _ = AppointmentRequest.objects.update_or_create(
            patient=bob_profile,
            preferred_provider=dr_lee_provider,
            requested_start=slot_17.start_time,
            defaults={
                "requested_slot": slot_17,
                "requested_end": slot_17.end_time,
                "reason": "Same-day blood pressure recheck and medication review",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        alice_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_smith_provider,
            scheduled_start=self._dt(days=-1, hour=9),
            defaults={
                "appointment_request": alice_request,
                "availability_slot": None,
                "scheduled_end": self._dt(days=-1, hour=10),
                "reason": "Annual wellness visit",
                "notes": "Completed seeded visit.",
                "status": AppointmentStatus.COMPLETED,
            },
        )

        bob_appointment, _ = Appointment.objects.update_or_create(
            patient=bob_profile,
            provider=dr_lee_provider,
            scheduled_start=self._dt(days=2, hour=13),
            defaults={
                "appointment_request": bob_request,
                "availability_slot": slot_3,
                "scheduled_end": self._dt(days=2, hour=14),
                "reason": "Blood pressure follow-up",
                "notes": "Upcoming seeded appointment.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        charlie_appointment, _ = Appointment.objects.update_or_create(
            patient=charlie_profile,
            provider=dr_smith_provider,
            scheduled_start=slot_4.start_time,
            defaults={
                "availability_slot": slot_4,
                "scheduled_end": slot_4.end_time,
                "reason": "Same-day sick visit",
                "notes": "Patient already arrived and is waiting in exam room.",
                "status": AppointmentStatus.CHECKED_IN,
            },
        )

        diana_appointment, _ = Appointment.objects.update_or_create(
            patient=diana_profile,
            provider=dr_lee_provider,
            scheduled_start=slot_7.start_time,
            defaults={
                "appointment_request": diana_request,
                "availability_slot": slot_7,
                "scheduled_end": slot_7.end_time,
                "reason": "Follow-up for migraine symptoms",
                "notes": "Patient is in waiting area and chart review is ready.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        ethan_no_show_appointment, _ = Appointment.objects.update_or_create(
            patient=ethan_profile,
            provider=dr_smith_provider,
            scheduled_start=self._dt(days=-2, hour=14),
            defaults={
                "availability_slot": None,
                "scheduled_end": self._dt(days=-2, hour=15),
                "reason": "Travel clearance consultation",
                "notes": "Seeded missed visit for no-show demo.",
                "status": AppointmentStatus.NO_SHOW,
            },
        )

        alice_cancelled_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_lee_provider,
            scheduled_start=self._dt(days=7, hour=10),
            defaults={
                "availability_slot": None,
                "scheduled_end": self._dt(days=7, hour=11),
                "reason": "Nutrition counseling",
                "notes": "Seeded cancelled appointment for patient history.",
                "status": AppointmentStatus.CANCELLED,
            },
        )

        alice_followup_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_lee_provider,
            scheduled_start=slot_9.start_time,
            defaults={
                "appointment_request": alice_followup_request,
                "availability_slot": slot_9,
                "scheduled_end": slot_9.end_time,
                "reason": "Lab review and medication follow-up",
                "notes": "Seeded future visit with pre-check-in complete for patient demo.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        alice_today_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_smith_provider,
            scheduled_start=slot_10.start_time,
            defaults={
                "appointment_request": alice_today_request,
                "availability_slot": slot_10,
                "scheduled_end": slot_10.end_time,
                "reason": "Same-day fatigue follow-up and care plan review",
                "notes": "Seeded same-day appointment so patient and doctor dashboards both show an active visit.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        bob_today_appointment, _ = Appointment.objects.update_or_create(
            patient=bob_profile,
            provider=dr_lee_provider,
            scheduled_start=slot_17.start_time,
            defaults={
                "appointment_request": bob_today_request,
                "availability_slot": slot_17,
                "scheduled_end": slot_17.end_time,
                "reason": "Same-day blood pressure recheck and medication review",
                "notes": "Seeded same-day checked-in follow-up for nurse and doctor demos.",
                "status": AppointmentStatus.CHECKED_IN,
            },
        )

        ethan_future_appointment, _ = Appointment.objects.update_or_create(
            patient=ethan_profile,
            provider=dr_smith_provider,
            scheduled_start=slot_8.start_time,
            defaults={
                "availability_slot": slot_8,
                "scheduled_end": slot_8.end_time,
                "reason": "Post-travel wellness clearance follow-up",
                "notes": "Seeded upcoming appointment for doctor schedule depth.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        alice_no_show_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_smith_provider,
            scheduled_start=self._dt(days=-12, hour=8),
            defaults={
                "availability_slot": None,
                "scheduled_end": self._dt(days=-12, hour=9),
                "reason": "Missed allergy follow-up",
                "notes": "Seeded no-show history item for appointment timeline demo.",
                "status": AppointmentStatus.NO_SHOW,
            },
        )

        slot_1.is_booked = True
        slot_1.save(update_fields=["is_booked"])
        slot_3.is_booked = True
        slot_3.save(update_fields=["is_booked"])
        slot_4.is_booked = True
        slot_4.save(update_fields=["is_booked"])
        slot_2.is_booked = False
        slot_2.save(update_fields=["is_booked"])
        slot_5.is_booked = False
        slot_5.save(update_fields=["is_booked"])
        slot_6.is_booked = False
        slot_6.save(update_fields=["is_booked"])
        slot_7.is_booked = True
        slot_7.save(update_fields=["is_booked"])
        slot_8.is_booked = True
        slot_8.save(update_fields=["is_booked"])
        slot_9.is_booked = True
        slot_9.save(update_fields=["is_booked"])
        slot_10.is_booked = True
        slot_10.save(update_fields=["is_booked"])
        slot_11.is_booked = False
        slot_11.save(update_fields=["is_booked"])
        slot_12.is_booked = False
        slot_12.save(update_fields=["is_booked"])
        slot_13.is_booked = False
        slot_13.save(update_fields=["is_booked"])
        slot_14.is_booked = False
        slot_14.save(update_fields=["is_booked"])
        slot_15.is_booked = False
        slot_15.save(update_fields=["is_booked"])
        slot_16.is_booked = False
        slot_16.save(update_fields=["is_booked"])
        slot_17.is_booked = True
        slot_17.save(update_fields=["is_booked"])
        slot_18.is_booked = False
        slot_18.save(update_fields=["is_booked"])

        CheckInRecord.objects.update_or_create(
            appointment=alice_appointment,
            defaults={
                "checked_in_by": frontdesk_profile,
                "notes": "Patient arrived on time.",
            },
        )

        CheckInRecord.objects.update_or_create(
            appointment=charlie_appointment,
            defaults={
                "checked_in_by": nurse_jane_profile,
                "notes": "Vitals pending room assignment complete.",
            },
        )

        CheckInRecord.objects.update_or_create(
            appointment=bob_today_appointment,
            defaults={
                "checked_in_by": nurse_jane_profile,
                "notes": "Same-day follow-up patient checked in for blood pressure recheck.",
            },
        )

        PreCheckInRecord.objects.update_or_create(
            appointment=bob_appointment,
            defaults={
                "phone_number": bob_profile.phone_number,
                "address_line_1": bob_profile.address_line_1,
                "city": bob_profile.city,
                "state": bob_profile.state,
                "postal_code": bob_profile.postal_code,
                "emergency_contact_name": bob_profile.emergency_contact_name,
                "emergency_contact_phone": bob_profile.emergency_contact_phone,
                "symptoms": "Occasional headaches and elevated home blood pressure readings.",
                "current_medications": "Lisinopril 10 mg daily",
                "allergies": "None reported",
                "insurance_provider": "Mountain State Health",
                "insurance_member_id": "MSH-BOB-1002",
                "accommodation_notes": "",
                "additional_notes": "Would like to discuss medication adjustment.",
            },
        )

        PreCheckInRecord.objects.update_or_create(
            appointment=diana_appointment,
            defaults={
                "phone_number": diana_profile.phone_number,
                "address_line_1": diana_profile.address_line_1,
                "city": diana_profile.city,
                "state": diana_profile.state,
                "postal_code": diana_profile.postal_code,
                "emergency_contact_name": diana_profile.emergency_contact_name,
                "emergency_contact_phone": diana_profile.emergency_contact_phone,
                "symptoms": "Recurring migraines with light sensitivity this week.",
                "current_medications": "Sumatriptan as needed",
                "allergies": "Shellfish",
                "insurance_provider": "Valley Care",
                "insurance_member_id": "VC-DIANA-1004",
                "accommodation_notes": "Prefers dimmed room lighting.",
                "additional_notes": "Missed work twice due to headaches.",
            },
        )

        PreCheckInRecord.objects.update_or_create(
            appointment=alice_followup_appointment,
            defaults={
                "phone_number": alice_profile.phone_number,
                "address_line_1": alice_profile.address_line_1,
                "city": alice_profile.city,
                "state": alice_profile.state,
                "postal_code": alice_profile.postal_code,
                "emergency_contact_name": alice_profile.emergency_contact_name,
                "emergency_contact_phone": alice_profile.emergency_contact_phone,
                "symptoms": "Continuing fatigue in the evenings and mild seasonal congestion.",
                "current_medications": "Cetirizine 10 mg daily, multivitamin",
                "allergies": "Penicillin",
                "insurance_provider": "Appalachian Health Plan",
                "insurance_member_id": "AHP-ALICE-1001",
                "accommodation_notes": "Prefers morning follow-up calls if rescheduled.",
                "additional_notes": "Would like to review recent lab results and next steps.",
            },
        )

        PreCheckInRecord.objects.update_or_create(
            appointment=alice_today_appointment,
            defaults={
                "phone_number": alice_profile.phone_number,
                "address_line_1": alice_profile.address_line_1,
                "city": alice_profile.city,
                "state": alice_profile.state,
                "postal_code": alice_profile.postal_code,
                "emergency_contact_name": alice_profile.emergency_contact_name,
                "emergency_contact_phone": alice_profile.emergency_contact_phone,
                "symptoms": "Fatigue over the last week with mild dizziness in the afternoon.",
                "current_medications": "Cetirizine 10 mg daily, multivitamin",
                "allergies": "Penicillin",
                "insurance_provider": "Appalachian Health Plan",
                "insurance_member_id": "AHP-ALICE-1001",
                "accommodation_notes": "Prefers printed after-visit summary.",
                "additional_notes": "Would like to review whether more labs are needed before the weekend.",
            },
        )

        PreCheckInRecord.objects.update_or_create(
            appointment=bob_today_appointment,
            defaults={
                "phone_number": bob_profile.phone_number,
                "address_line_1": bob_profile.address_line_1,
                "city": bob_profile.city,
                "state": bob_profile.state,
                "postal_code": bob_profile.postal_code,
                "emergency_contact_name": bob_profile.emergency_contact_name,
                "emergency_contact_phone": bob_profile.emergency_contact_phone,
                "symptoms": "Higher blood pressure readings at home and intermittent headaches.",
                "current_medications": "Lisinopril 10 mg daily",
                "allergies": "None reported",
                "insurance_provider": "Mountain State Health",
                "insurance_member_id": "MSH-BOB-1002",
                "accommodation_notes": "",
                "additional_notes": "Would like to confirm whether dosage adjustment is still needed.",
            },
        )

        # ------------------------------------------------------------------
        # Records
        # ------------------------------------------------------------------
        alice_record, _ = PatientRecord.objects.update_or_create(
            patient=alice_profile,
            defaults={
                "primary_provider": dr_smith_provider,
                "blood_type": "O+",
                "allergies": "Penicillin",
                "chronic_conditions": "Seasonal allergies",
                "general_notes": "Seeded demo patient record.",
            },
        )

        bob_record, _ = PatientRecord.objects.update_or_create(
            patient=bob_profile,
            defaults={
                "primary_provider": dr_lee_provider,
                "blood_type": "A-",
                "allergies": "",
                "chronic_conditions": "Hypertension",
                "general_notes": "Seeded demo patient record.",
            },
        )

        charlie_record, _ = PatientRecord.objects.update_or_create(
            patient=charlie_profile,
            defaults={
                "primary_provider": dr_smith_provider,
                "blood_type": "B+",
                "allergies": "Latex",
                "chronic_conditions": "Asthma",
                "general_notes": "Seeded patient currently checked in for same-day visit.",
            },
        )

        diana_record, _ = PatientRecord.objects.update_or_create(
            patient=diana_profile,
            defaults={
                "primary_provider": dr_lee_provider,
                "blood_type": "AB+",
                "allergies": "Shellfish",
                "chronic_conditions": "Migraine disorder",
                "general_notes": "Seeded waiting-room patient for nurse and front desk demo.",
            },
        )

        ethan_record, _ = PatientRecord.objects.update_or_create(
            patient=ethan_profile,
            defaults={
                "primary_provider": dr_smith_provider,
                "blood_type": "O-",
                "allergies": "Ibuprofen",
                "chronic_conditions": "Mild anxiety",
                "general_notes": "Seeded no-show and rejected-request patient history.",
            },
        )

        ClinicalNote.objects.update_or_create(
            patient_record=alice_record,
            title="Annual wellness note",
            defaults={
                "appointment": alice_appointment,
                "author": dr_smith_profile,
                "note_type": ClinicalNoteType.SOAP,
                "content": "Patient doing well overall. Routine follow-up in one year.",
            },
        )

        ClinicalNote.objects.update_or_create(
            patient_record=alice_record,
            title="Lab follow-up planning note",
            defaults={
                "appointment": alice_followup_appointment,
                "author": dr_lee_profile,
                "note_type": ClinicalNoteType.CONSULT,
                "content": "Patient requested review of wellness labs and ongoing fatigue. Follow-up visit scheduled with pre-check-in completed.",
            },
        )

        ClinicalNote.objects.update_or_create(
            patient_record=bob_record,
            title="Hypertension review",
            defaults={
                "appointment": bob_appointment,
                "author": dr_lee_profile,
                "note_type": ClinicalNoteType.CONSULT,
                "content": "Patient reports elevated home readings. Review medication adherence and consider dosage increase.",
            },
        )

        ClinicalNote.objects.update_or_create(
            patient_record=charlie_record,
            title="Asthma same-day assessment",
            defaults={
                "appointment": charlie_appointment,
                "author": dr_smith_profile,
                "note_type": ClinicalNoteType.SOAP,
                "content": "Patient checked in for same-day wheezing symptoms. Nebulizer response and discharge plan pending.",
            },
        )

        ClinicalNote.objects.update_or_create(
            patient_record=diana_record,
            title="Migraine follow-up prep",
            defaults={
                "appointment": diana_appointment,
                "author": dr_lee_profile,
                "note_type": ClinicalNoteType.GENERAL,
                "content": "Patient has recurring migraines and pre-check-in mentions light sensitivity. Review triggers and work accommodations.",
            },
        )

        VitalsRecord.objects.update_or_create(
            patient_record=alice_record,
            appointment=alice_appointment,
            recorded_at=self._dt(days=-1, hour=9, minute=15),
            defaults={
                "recorded_by": frontdesk_profile,
                "height_cm": Decimal("167.50"),
                "weight_kg": Decimal("63.20"),
                "temperature_c": Decimal("36.8"),
                "systolic_bp": 118,
                "diastolic_bp": 76,
                "pulse_bpm": 72,
                "respiratory_rate": 14,
                "oxygen_saturation": 98,
                "notes": "Vitals within normal range.",
            },
        )

        VitalsRecord.objects.update_or_create(
            patient_record=bob_record,
            appointment=bob_appointment,
            recorded_at=self._dt(days=-20, hour=10, minute=20),
            defaults={
                "recorded_by": nurse_jane_profile,
                "height_cm": Decimal("180.20"),
                "weight_kg": Decimal("88.40"),
                "temperature_c": Decimal("36.9"),
                "systolic_bp": 142,
                "diastolic_bp": 92,
                "pulse_bpm": 78,
                "respiratory_rate": 16,
                "oxygen_saturation": 97,
                "notes": "Home blood pressure trend is elevated.",
            },
        )

        VitalsRecord.objects.update_or_create(
            patient_record=charlie_record,
            appointment=charlie_appointment,
            recorded_at=self._dt(days=0, hour=15, minute=10),
            defaults={
                "recorded_by": nurse_jane_profile,
                "height_cm": Decimal("174.00"),
                "weight_kg": Decimal("79.60"),
                "temperature_c": Decimal("37.3"),
                "systolic_bp": 128,
                "diastolic_bp": 84,
                "pulse_bpm": 93,
                "respiratory_rate": 20,
                "oxygen_saturation": 95,
                "notes": "Shortness of breath improved after arrival, monitoring ongoing.",
            },
        )

        VitalsRecord.objects.update_or_create(
            patient_record=diana_record,
            appointment=diana_appointment,
            recorded_at=self._dt(days=0, hour=11, minute=5),
            defaults={
                "recorded_by": nurse_jane_profile,
                "height_cm": Decimal("165.00"),
                "weight_kg": Decimal("59.10"),
                "temperature_c": Decimal("36.7"),
                "systolic_bp": 116,
                "diastolic_bp": 74,
                "pulse_bpm": 70,
                "respiratory_rate": 14,
                "oxygen_saturation": 99,
                "notes": "Patient seated in waiting room; migraine symptoms active.",
            },
        )

        alice_lab_order, _ = LabOrder.objects.update_or_create(
            patient_record=alice_record,
            test_name="Complete Blood Count",
            defaults={
                "appointment": alice_appointment,
                "ordered_by": dr_smith_profile,
                "instructions": "Routine annual lab work.",
                "status": LabOrderStatus.COMPLETED,
            },
        )

        alice_followup_lab_order, _ = LabOrder.objects.update_or_create(
            patient_record=alice_record,
            test_name="Thyroid Stimulating Hormone",
            defaults={
                "appointment": alice_followup_appointment,
                "ordered_by": dr_lee_profile,
                "instructions": "Follow-up fatigue workup.",
                "status": LabOrderStatus.ORDERED,
            },
        )

        LabResult.objects.update_or_create(
            lab_order=alice_lab_order,
            defaults={
                "reviewed_by": dr_smith_profile,
                "result_summary": "CBC within normal limits.",
                "result_value": "Normal",
                "units": "",
                "reference_range": "Normal",
                "status": LabResultStatus.FINAL,
            },
        )

        bob_lab_order, _ = LabOrder.objects.update_or_create(
            patient_record=bob_record,
            test_name="Lipid Panel",
            defaults={
                "appointment": bob_appointment,
                "ordered_by": dr_lee_profile,
                "instructions": "Fasting lab order for chronic care follow-up.",
                "status": LabOrderStatus.ORDERED,
            },
        )

        charlie_lab_order, _ = LabOrder.objects.update_or_create(
            patient_record=charlie_record,
            test_name="Chest X-Ray Review",
            defaults={
                "appointment": charlie_appointment,
                "ordered_by": dr_smith_profile,
                "instructions": "Correlate with wheezing symptoms and oxygen saturation.",
                "status": LabOrderStatus.IN_PROGRESS,
            },
        )

        diana_lab_order, _ = LabOrder.objects.update_or_create(
            patient_record=diana_record,
            test_name="Vitamin D",
            defaults={
                "appointment": diana_appointment,
                "ordered_by": dr_lee_profile,
                "instructions": "Rule out deficiency contributing to fatigue and headaches.",
                "status": LabOrderStatus.COMPLETED,
            },
        )

        LabResult.objects.update_or_create(
            lab_order=diana_lab_order,
            defaults={
                "reviewed_by": dr_lee_profile,
                "result_summary": "Vitamin D mildly low. Consider supplementation.",
                "result_value": "24",
                "units": "ng/mL",
                "reference_range": "30-100",
                "status": LabResultStatus.FINAL,
            },
        )

        alice_prescription, _ = Prescription.objects.update_or_create(
            patient_record=alice_record,
            medication_name="Cetirizine",
            defaults={
                "appointment": alice_appointment,
                "prescribed_by": dr_smith_profile,
                "dosage": "10 mg",
                "frequency": "Once daily",
                "instructions": "Take once daily as needed for allergies.",
                "start_date": timezone.localdate(),
                "status": PrescriptionStatus.ACTIVE,
            },
        )

        alice_completed_prescription, _ = Prescription.objects.update_or_create(
            patient_record=alice_record,
            medication_name="Amoxicillin",
            defaults={
                "appointment": alice_appointment,
                "prescribed_by": dr_smith_profile,
                "dosage": "500 mg",
                "frequency": "Twice daily",
                "instructions": "Completed prior short course; kept for history demo.",
                "start_date": timezone.localdate() - timedelta(days=60),
                "end_date": timezone.localdate() - timedelta(days=53),
                "status": PrescriptionStatus.COMPLETED,
            },
        )

        Medication.objects.update_or_create(
            patient_record=alice_record,
            name="Cetirizine",
            defaults={
                "prescription": alice_prescription,
                "dosage": "10 mg",
                "frequency": "Once daily",
                "is_active": True,
                "notes": "Seeded active medication.",
            },
        )

        Medication.objects.update_or_create(
            patient_record=alice_record,
            name="Amoxicillin",
            defaults={
                "prescription": alice_completed_prescription,
                "dosage": "500 mg",
                "frequency": "Twice daily",
                "is_active": False,
                "notes": "Seeded completed medication history item.",
            },
        )

        bob_prescription, _ = Prescription.objects.update_or_create(
            patient_record=bob_record,
            medication_name="Lisinopril",
            defaults={
                "appointment": bob_appointment,
                "prescribed_by": dr_lee_profile,
                "dosage": "10 mg",
                "frequency": "Once daily",
                "instructions": "Take every morning and monitor blood pressure at home.",
                "start_date": timezone.localdate() - timedelta(days=90),
                "status": PrescriptionStatus.ACTIVE,
            },
        )

        Medication.objects.update_or_create(
            patient_record=bob_record,
            name="Lisinopril",
            defaults={
                "prescription": bob_prescription,
                "dosage": "10 mg",
                "frequency": "Once daily",
                "is_active": True,
                "notes": "Seeded chronic blood pressure medication.",
            },
        )

        diana_prescription, _ = Prescription.objects.update_or_create(
            patient_record=diana_record,
            medication_name="Sumatriptan",
            defaults={
                "appointment": diana_appointment,
                "prescribed_by": dr_lee_profile,
                "dosage": "50 mg",
                "frequency": "As needed",
                "instructions": "Take at migraine onset, no more than 2 doses in 24 hours.",
                "start_date": timezone.localdate() - timedelta(days=30),
                "status": PrescriptionStatus.ACTIVE,
            },
        )

        Medication.objects.update_or_create(
            patient_record=diana_record,
            name="Sumatriptan",
            defaults={
                "prescription": diana_prescription,
                "dosage": "50 mg",
                "frequency": "As needed",
                "is_active": True,
                "notes": "Seeded migraine rescue medication.",
            },
        )

        SupportingDocument.objects.update_or_create(
            patient_record=alice_record,
            title="Insurance Card Copy",
            defaults={
                "appointment": alice_appointment,
                "uploaded_by": frontdesk_profile,
                "document_type": SupportingDocumentType.PDF,
                "file_path": "seed/insurance_card_alice.pdf",
                "notes": "Sample uploaded document.",
            },
        )

        RecordFlag.objects.update_or_create(
            patient_record=alice_record,
            flag_type=RecordFlagType.ALLERGY,
            reason="Penicillin allergy",
            defaults={
                "created_by": dr_smith_profile,
                "is_active": True,
            },
        )

        MedicalSummary.objects.update_or_create(
            patient_record=alice_record,
            defaults={
                "summary_text": "Generally healthy patient with seasonal allergies.",
                "last_updated_by": dr_smith_profile,
            },
        )

        MedicalSummary.objects.update_or_create(
            patient_record=bob_record,
            defaults={
                "summary_text": "Hypertension follow-up patient.",
                "last_updated_by": dr_lee_profile,
            },
        )

        MedicalSummary.objects.update_or_create(
            patient_record=charlie_record,
            defaults={
                "summary_text": "Asthma patient with same-day respiratory follow-up.",
                "last_updated_by": dr_smith_profile,
            },
        )

        MedicalSummary.objects.update_or_create(
            patient_record=diana_record,
            defaults={
                "summary_text": "Migraine follow-up patient currently waiting for same-day appointment.",
                "last_updated_by": dr_lee_profile,
            },
        )

        MedicalSummary.objects.update_or_create(
            patient_record=ethan_record,
            defaults={
                "summary_text": "History includes missed visit and previously rejected travel-clearance request.",
                "last_updated_by": dr_smith_profile,
            },
        )

        # ------------------------------------------------------------------
        # Billing
        # ------------------------------------------------------------------
        alice_payment_method, _ = PaymentMethod.objects.update_or_create(
            patient=alice_profile,
            nickname="Alice Visa",
            defaults={
                "method_type": PaymentMethodType.CREDIT_CARD,
                "cardholder_name": "Alice Carter",
                "brand": "Visa",
                "last4": "1111",
                "expiration_month": 12,
                "expiration_year": 2028,
                "is_default": True,
                "is_active": True,
            },
        )

        bob_payment_method, _ = PaymentMethod.objects.update_or_create(
            patient=bob_profile,
            nickname="Bob Mastercard",
            defaults={
                "method_type": PaymentMethodType.CREDIT_CARD,
                "cardholder_name": "Bob Nguyen",
                "brand": "Mastercard",
                "last4": "2222",
                "expiration_month": 8,
                "expiration_year": 2027,
                "is_default": True,
                "is_active": True,
            },
        )

        charlie_payment_method, _ = PaymentMethod.objects.update_or_create(
            patient=charlie_profile,
            nickname="Charlie HSA",
            defaults={
                "method_type": PaymentMethodType.DEBIT_CARD,
                "cardholder_name": "Charlie Lopez",
                "brand": "Visa",
                "last4": "3333",
                "expiration_month": 4,
                "expiration_year": 2029,
                "is_default": True,
                "is_active": True,
            },
        )

        diana_payment_method, _ = PaymentMethod.objects.update_or_create(
            patient=diana_profile,
            nickname="Diana Discover",
            defaults={
                "method_type": PaymentMethodType.CREDIT_CARD,
                "cardholder_name": "Diana Brooks",
                "brand": "Discover",
                "last4": "4444",
                "expiration_month": 9,
                "expiration_year": 2028,
                "is_default": True,
                "is_active": True,
            },
        )

        alice_invoice, _ = Invoice.objects.update_or_create(
            invoice_number="INV-1001",
            defaults={
                "patient": alice_profile,
                "appointment": alice_appointment,
                "status": InvoiceStatus.PAID,
                "due_date": timezone.localdate() + timedelta(days=30),
                "notes": "Seeded paid invoice.",
            },
        )

        bob_invoice, _ = Invoice.objects.update_or_create(
            invoice_number="INV-1002",
            defaults={
                "patient": bob_profile,
                "appointment": bob_appointment,
                "status": InvoiceStatus.ISSUED,
                "due_date": timezone.localdate() + timedelta(days=14),
                "notes": "Seeded open invoice.",
            },
        )

        charlie_invoice, _ = Invoice.objects.update_or_create(
            invoice_number="INV-1003",
            defaults={
                "patient": charlie_profile,
                "appointment": charlie_appointment,
                "status": InvoiceStatus.ISSUED,
                "due_date": timezone.localdate() + timedelta(days=21),
                "notes": "Seeded checked-in visit invoice preview.",
            },
        )

        alice_open_invoice, _ = Invoice.objects.update_or_create(
            invoice_number="INV-1005",
            defaults={
                "patient": alice_profile,
                "appointment": alice_followup_appointment,
                "status": InvoiceStatus.ISSUED,
                "due_date": timezone.localdate() + timedelta(days=10),
                "notes": "Seeded upcoming visit invoice for patient billing demo.",
            },
        )

        diana_invoice, _ = Invoice.objects.update_or_create(
            invoice_number="INV-1004",
            defaults={
                "patient": diana_profile,
                "appointment": diana_appointment,
                "status": InvoiceStatus.OVERDUE,
                "due_date": timezone.localdate() - timedelta(days=5),
                "notes": "Seeded overdue invoice for front desk follow-up demo.",
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=alice_invoice,
            description="Office Visit",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("150.00"),
                "line_total": Decimal("150.00"),
                "service_date": timezone.localdate() - timedelta(days=1),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=alice_invoice,
            description="CBC Lab Panel",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("35.00"),
                "line_total": Decimal("35.00"),
                "service_date": timezone.localdate() - timedelta(days=1),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=bob_invoice,
            description="Follow-up Consultation",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("120.00"),
                "line_total": Decimal("120.00"),
                "service_date": timezone.localdate() + timedelta(days=2),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=charlie_invoice,
            description="Same-Day Visit",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("140.00"),
                "line_total": Decimal("140.00"),
                "service_date": timezone.localdate(),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=alice_open_invoice,
            description="Follow-up Office Visit",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("130.00"),
                "line_total": Decimal("130.00"),
                "service_date": timezone.localdate() + timedelta(days=6),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=alice_open_invoice,
            description="Pending thyroid lab order",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("28.00"),
                "line_total": Decimal("28.00"),
                "service_date": timezone.localdate() + timedelta(days=6),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=diana_invoice,
            description="Migraine Follow-up Visit",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("135.00"),
                "line_total": Decimal("135.00"),
                "service_date": timezone.localdate() - timedelta(days=6),
            },
        )

        InvoiceLineItem.objects.update_or_create(
            invoice=diana_invoice,
            description="Vitamin D Lab Review",
            defaults={
                "quantity": 1,
                "unit_price": Decimal("45.00"),
                "line_total": Decimal("45.00"),
                "service_date": timezone.localdate() - timedelta(days=6),
            },
        )

        self._refresh_invoice_totals(alice_invoice)
        self._refresh_invoice_totals(alice_open_invoice)
        self._refresh_invoice_totals(bob_invoice)
        self._refresh_invoice_totals(charlie_invoice)
        self._refresh_invoice_totals(diana_invoice)

        Payment.objects.update_or_create(
            invoice=alice_invoice,
            transaction_reference="TXN-INV-1001",
            defaults={
                "payment_method": alice_payment_method,
                "amount": alice_invoice.total_amount,
                "status": PaymentStatus.COMPLETED,
                "notes": "Seeded completed payment.",
            },
        )

        self._refresh_invoice_totals(alice_invoice)

        Payment.objects.update_or_create(
            invoice=charlie_invoice,
            transaction_reference="TXN-INV-1003-PARTIAL",
            defaults={
                "payment_method": charlie_payment_method,
                "amount": Decimal("40.00"),
                "status": PaymentStatus.COMPLETED,
                "notes": "Seeded partial payment for demo purposes.",
            },
        )

        self._refresh_invoice_totals(charlie_invoice)

        Payment.objects.update_or_create(
            invoice=diana_invoice,
            transaction_reference="TXN-INV-1004-PENDING",
            defaults={
                "payment_method": diana_payment_method,
                "amount": Decimal("25.00"),
                "status": PaymentStatus.FAILED,
                "notes": "Seeded failed payment attempt for billing demo.",
            },
        )

        # ------------------------------------------------------------------
        # Notifications
        # ------------------------------------------------------------------
        Notification.objects.update_or_create(
            recipient=alice_user,
            subject="Your wellness visit summary is available",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.READ,
                "message": "Your visit summary and billing details are now available.",
                "appointment": alice_appointment,
                "invoice": alice_invoice,
                "sent_at": timezone.now(),
                "read_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=alice_user,
            subject="Upcoming follow-up appointment confirmed",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_STATUS,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Your lab review follow-up with Dr. Maya Lee is scheduled and your pre-check-in is already on file.",
                "appointment": alice_followup_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=alice_user,
            subject="Today's care plan follow-up is scheduled",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_STATUS,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Your same-day follow-up with Dr. John Smith is on today's schedule and your pre-check-in details are ready.",
                "appointment": alice_today_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=alice_user,
            subject="Invoice INV-1005 is ready",
            defaults={
                "notification_type": NotificationType.BILLING_UPDATE,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.PENDING,
                "message": "A new invoice has been added for your follow-up appointment and is available in Billing.",
                "appointment": alice_followup_appointment,
                "invoice": alice_open_invoice,
            },
        )

        Notification.objects.update_or_create(
            recipient=alice_user,
            subject="One appointment request is still pending",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.PENDING,
                "message": "Your fatigue-related appointment request is still waiting for staff approval.",
                "appointment": None,
                "invoice": None,
            },
        )

        Notification.objects.update_or_create(
            recipient=bob_user,
            subject="Upcoming appointment reminder",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_REMINDER,
                "channel": NotificationChannel.EMAIL,
                "status": NotificationStatus.SENT,
                "message": "Reminder: you have an appointment scheduled in two days.",
                "appointment": bob_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=charlie_user,
            subject="You have been checked in",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_STATUS,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Front desk staff checked you in for today's visit.",
                "appointment": charlie_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=charlie_user,
            subject="Invoice INV-1003 is available",
            defaults={
                "notification_type": NotificationType.BILLING_UPDATE,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "A visit invoice with a partial payment example is now on your account.",
                "appointment": charlie_appointment,
                "invoice": charlie_invoice,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=diana_user,
            subject="Today’s appointment is ready for check-in",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_STATUS,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Your appointment is on today’s front desk queue and your pre-check-in has already been submitted.",
                "appointment": diana_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=ethan_user,
            subject="Appointment request update",
            defaults={
                "notification_type": NotificationType.APPOINTMENT_STATUS,
                "channel": NotificationChannel.EMAIL,
                "status": NotificationStatus.SENT,
                "message": "Your recent travel-clearance appointment request could not be scheduled and needs a different time slot.",
                "appointment": ethan_no_show_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=frontdesk_user,
            subject="Pending appointment request waiting",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.PENDING,
                "message": "Charlie Lopez has a pending appointment request awaiting approval.",
                "appointment": None,
                "invoice": None,
            },
        )

        Notification.objects.update_or_create(
            recipient=frontdesk_user,
            subject="Overdue invoice follow-up available",
            defaults={
                "notification_type": NotificationType.BILLING_UPDATE,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.PENDING,
                "message": "Diana Brooks has an overdue invoice that can be used for billing follow-up in the demo.",
                "appointment": diana_appointment,
                "invoice": diana_invoice,
            },
        )

        Notification.objects.update_or_create(
            recipient=nurse_jane_user,
            subject="Two patients ready for intake review",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Charlie Lopez is checked in and Diana Brooks is waiting with pre-check-in details available.",
                "appointment": charlie_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=bob_user,
            subject="Invoice INV-1002 is ready",
            defaults={
                "notification_type": NotificationType.BILLING_UPDATE,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.PENDING,
                "message": "A new invoice has been generated for your upcoming visit.",
                "appointment": bob_appointment,
                "invoice": bob_invoice,
            },
        )

        Notification.objects.update_or_create(
            recipient=dr_smith_user,
            subject="Today's doctor schedule is ready",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Charlie Lopez is checked in, Alice Carter is still waiting today, and Ethan Reed has a future follow-up scheduled.",
                "appointment": alice_today_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        Notification.objects.update_or_create(
            recipient=dr_lee_user,
            subject="Provider schedule has new demo activity",
            defaults={
                "notification_type": NotificationType.GENERAL,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "Bob Nguyen is scheduled for follow-up and Diana Brooks is waiting with migraines noted in pre-check-in.",
                "appointment": diana_appointment,
                "invoice": None,
                "sent_at": timezone.now(),
            },
        )

        self.stdout.write(self.style.SUCCESS("Development data seeded successfully."))
        self.stdout.write(self.style.SUCCESS(f"Demo password for all seeded users: {dev_password}"))
        self.stdout.write("Seeded users: admin, drsmith, drlee, nursejane, frontdesk, alice, bob, charlie, diana, ethan")
        self.stdout.write("Admin login: admin / DevPass123! -> dashboard admin portal -> Django admin link")

    def _upsert_user(
        self,
        username,
        email,
        password,
        is_staff=False,
        is_superuser=False,
        role=User.Role.PATIENT,
        first_name="",
        last_name="",
    ):
        user, _ = User.objects.get_or_create(username=username)

        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True
        if hasattr(user, "role"):
            user.role = role

        if hasattr(user, "first_name"):
            user.first_name = first_name
        if hasattr(user, "last_name"):
            user.last_name = last_name

        user.set_password(password)
        user.save()
        return user

    def _dt(self, days=0, hour=9, minute=0):
        base = timezone.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        return base + timedelta(days=days)

    def _refresh_invoice_totals(self, invoice):
        subtotal = sum(
            (line.line_total for line in invoice.line_items.all()),
            Decimal("0.00"),
        )
        tax_amount = Decimal("0.00")
        total_amount = subtotal + tax_amount
        paid_amount = sum(
            (
                payment.amount
                for payment in invoice.payments.filter(status=PaymentStatus.COMPLETED)
            ),
            Decimal("0.00"),
        )
        balance_due = total_amount - paid_amount

        if balance_due <= Decimal("0.00"):
            status = InvoiceStatus.PAID
            balance_due = Decimal("0.00")
        elif paid_amount > Decimal("0.00"):
            status = InvoiceStatus.PARTIALLY_PAID
        else:
            status = invoice.status if invoice.status == InvoiceStatus.ISSUED else InvoiceStatus.ISSUED

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        invoice.balance_due = balance_due
        invoice.status = status
        invoice.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "balance_due",
                "status",
                "updated_at",
            ]
        )
