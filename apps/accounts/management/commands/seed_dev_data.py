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
            first_name="John",
            last_name="Smith",
        )

        dr_lee_user = self._upsert_user(
            username="drlee",
            email="drlee@patientportal.local",
            password=dev_password,
            is_staff=True,
            first_name="Maya",
            last_name="Lee",
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

        AvailabilitySlot.objects.get_or_create(
            provider=dr_smith_provider,
            start_time=slot_1_start,
            end_time=slot_1_end,
            defaults={"is_booked": True, "notes": "Seeded slot"},
        )

        AvailabilitySlot.objects.get_or_create(
            provider=dr_smith_provider,
            start_time=slot_2_start,
            end_time=slot_2_end,
            defaults={"is_booked": False, "notes": "Seeded slot"},
        )

        AvailabilitySlot.objects.get_or_create(
            provider=dr_lee_provider,
            start_time=slot_3_start,
            end_time=slot_3_end,
            defaults={"is_booked": True, "notes": "Seeded slot"},
        )

        # ------------------------------------------------------------------
        # Appointment Requests + Appointments
        # ------------------------------------------------------------------
        alice_request, _ = AppointmentRequest.objects.update_or_create(
            patient=alice_profile,
            preferred_provider=dr_smith_provider,
            requested_start=self._dt(days=-1, hour=9),
            defaults={
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
                "requested_end": self._dt(days=2, hour=14),
                "reason": "Blood pressure follow-up",
                "status": AppointmentRequestStatus.APPROVED,
            },
        )

        alice_appointment, _ = Appointment.objects.update_or_create(
            patient=alice_profile,
            provider=dr_smith_provider,
            scheduled_start=self._dt(days=-1, hour=9),
            defaults={
                "appointment_request": alice_request,
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
                "scheduled_end": self._dt(days=2, hour=14),
                "reason": "Blood pressure follow-up",
                "notes": "Upcoming seeded appointment.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )

        CheckInRecord.objects.update_or_create(
            appointment=alice_appointment,
            defaults={
                "checked_in_by": frontdesk_profile,
                "notes": "Patient arrived on time.",
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

        self._refresh_invoice_totals(alice_invoice)
        self._refresh_invoice_totals(bob_invoice)

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
            subject="Daily seeded system notice",
            defaults={
                "notification_type": NotificationType.SYSTEM,
                "channel": NotificationChannel.IN_APP,
                "status": NotificationStatus.SENT,
                "message": "This is a seeded system notification for staff demo purposes.",
                "sent_at": timezone.now(),
            },
        )

        self.stdout.write(self.style.SUCCESS("Development data seeded successfully."))
        self.stdout.write(self.style.SUCCESS(f"Demo password for all seeded users: {dev_password}"))
        self.stdout.write("Seeded users: admin, drsmith, drlee, frontdesk, alice, bob")

    def _upsert_user(
        self,
        username,
        email,
        password,
        is_staff=False,
        is_superuser=False,
        first_name="",
        last_name="",
    ):
        user, _ = User.objects.get_or_create(username=username)

        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True

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