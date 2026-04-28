from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.urls import reverse_lazy

from apps.billing.models import Invoice
from apps.notifications.models import Notification
from apps.profiles.models import PatientProfile, StaffRole
from apps.records.models import ClinicalNote, LabOrder, LabResult, PatientRecord, VitalsRecord, Prescription
from apps.scheduling.models import Appointment, AppointmentRequest, AppointmentRequestStatus, AppointmentStatus, Provider

from .forms import (
    AdminInvoiceForm,
    ClinicalNoteForm,
    LabOrderForm,
    LabResultForm,
    ProfileForm,
    SignUpForm,
    VitalsRecordForm,
)


def _staff_redirect_name(user):
    if user.is_superuser:
        return "admin_dashboard"
    staff_profile = getattr(user, "staff_profile", None)
    if staff_profile and staff_profile.staff_role == StaffRole.PHYSICIAN:
        return "doctor_dashboard"
    if staff_profile and staff_profile.staff_role == StaffRole.NURSE:
        return "nurse_dashboard"
    if staff_profile and staff_profile.staff_role == StaffRole.RECEPTIONIST:
        return "receptionist_dashboard"
    return "admin_dashboard"


def _is_admin_portal_user(user):
    if user.is_superuser:
        return True
    staff_profile = getattr(user, "staff_profile", None)
    if not staff_profile:
        return bool(user.is_staff)
    return staff_profile.staff_role == StaffRole.ADMIN


def _is_receptionist_user(user):
    staff_profile = getattr(user, "staff_profile", None)
    return bool(staff_profile and staff_profile.staff_role == StaffRole.RECEPTIONIST)


def _can_access_staff_billing(user):
    return _is_admin_portal_user(user) or _is_receptionist_user(user)


def _can_delete_staff_invoice(user):
    return _is_admin_portal_user(user)


def _staff_portal_context(user):
    if _is_receptionist_user(user):
        return {
            "portal_label": "Front Desk Portal",
            "portal_title": "Front Desk",
            "portal_subtitle": "Manage arrivals, requests, and billing follow-up",
            "home_url": "receptionist_dashboard",
            "show_admin_link": False,
            "can_delete_invoices": False,
        }
    return {
        "portal_label": "Admin Portal",
        "portal_title": "Administrator",
        "portal_subtitle": "Manage the portal from an administrator view",
        "home_url": "admin_dashboard",
        "show_admin_link": True,
        "can_delete_invoices": True,
    }


def _staff_can_manage_request(user, appointment_request):
    staff_profile = getattr(user, "staff_profile", None)
    if user.is_superuser:
        return True
    if not staff_profile:
        return bool(user.is_staff)
    if staff_profile.staff_role == StaffRole.PHYSICIAN:
        provider = getattr(staff_profile, "provider_profile", None)
        return provider is not None and appointment_request.preferred_provider_id == provider.id
    return staff_profile.staff_role in {StaffRole.RECEPTIONIST, StaffRole.ADMIN}


class PortalPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Password change is done.")
        return response


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.first_name = form.cleaned_data["first_name"]
                user.last_name = form.cleaned_data["last_name"]
                user.role = user.Role.PATIENT
                user.save()

                PatientProfile.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get("phone_number", ""),
                    date_of_birth=form.cleaned_data.get("date_of_birth"),
                    address_line_1=form.cleaned_data.get("address", ""),
                )

                login(request, user)
                return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


@login_required
def dashboard(request):
    staff_profile = getattr(request.user, "staff_profile", None)

    if staff_profile or request.user.is_staff or request.user.is_superuser:
        return redirect(_staff_redirect_name(request.user))

    patient_profile = getattr(request.user, "patient_profile", None)

    upcoming_appointments = []
    pending_appointment_requests = []
    recent_lab_results = []
    open_invoices = []
    recent_notifications = []

    if patient_profile:
        upcoming_appointments = (
            Appointment.objects
            .filter(
                patient=patient_profile,
                scheduled_start__gte=timezone.now(),
            )
            .select_related("provider__staff_profile__user", "pre_check_in_record")
            .order_by("scheduled_start")[:5]
        )

        pending_appointment_requests = (
            AppointmentRequest.objects
            .filter(
                patient=patient_profile,
                status=AppointmentRequestStatus.PENDING,
            )
            .select_related("preferred_provider__staff_profile__user")
            .order_by("-created_at")[:5]
        )

        recent_lab_results = (
            LabResult.objects
            .filter(lab_order__patient_record__patient=patient_profile)
            .select_related("lab_order")
            .order_by("-resulted_at")[:5]
        )

        open_invoices = (
            Invoice.objects
            .filter(patient=patient_profile)
            .exclude(status="paid")
            .order_by("due_date", "-issued_at")[:5]
        )

        recent_notifications = (
            Notification.objects
            .filter(recipient=request.user)
            .order_by("-created_at")[:5]
        )

    context = {
        "patient_profile": patient_profile,
        "upcoming_appointments": upcoming_appointments,
        "pending_appointment_requests": pending_appointment_requests,
        "recent_lab_results": recent_lab_results,
        "open_invoices": open_invoices,
        "recent_notifications": recent_notifications,
    }

    return render(request, "dashboard.html", context)

@login_required
def patient_dashboard(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    upcoming_appointments = []
    pending_appointment_requests = []
    recent_lab_results = []
    open_invoices = []
    recent_notifications = []

    if patient_profile:
        upcoming_appointments = (
            Appointment.objects
            .filter(
                patient=patient_profile,
                scheduled_start__gte=timezone.now(),
            )
            .select_related("provider__staff_profile__user", "pre_check_in_record")
            .order_by("scheduled_start")[:5]
        )

        pending_appointment_requests = (
            AppointmentRequest.objects
            .filter(
                patient=patient_profile,
                status=AppointmentRequestStatus.PENDING,
            )
            .select_related("preferred_provider__staff_profile__user")
            .order_by("-created_at")[:5]
        )

        recent_lab_results = (
            LabResult.objects
            .filter(lab_order__patient_record__patient=patient_profile)
            .select_related("lab_order")
            .order_by("-resulted_at")[:5]
        )

        open_invoices = (
            Invoice.objects
            .filter(patient=patient_profile)
            .exclude(status="paid")
            .order_by("due_date", "-issued_at")[:5]
        )

        recent_notifications = (
            Notification.objects
            .filter(recipient=request.user)
            .order_by("-created_at")[:5]
        )

    context = {
        "patient_profile": patient_profile,
        "upcoming_appointments": upcoming_appointments,
        "pending_appointment_requests": pending_appointment_requests,
        "recent_lab_results": recent_lab_results,
        "open_invoices": open_invoices,
        "recent_notifications": recent_notifications,
    }

    return render(request, "dashboard.html", context)


@login_required
def admin_dashboard(request):
    if not _is_admin_portal_user(request.user):
        return redirect("dashboard")

    staff_profile = getattr(request.user, "staff_profile", None)
    if staff_profile and staff_profile.staff_role == StaffRole.NURSE:
        return redirect("nurse_dashboard")

    pending_appointment_requests = (
        AppointmentRequest.objects
        .filter(status=AppointmentRequestStatus.PENDING)
        .select_related("patient__user", "preferred_provider__staff_profile__user")
        .order_by("requested_start", "created_at")
    )
    upcoming_appointments = (
        Appointment.objects
        .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
        .order_by("scheduled_start")[:10]
    )

    context = {
        "admin_user": request.user,
        "pending_appointment_requests": pending_appointment_requests,
        "upcoming_appointments": upcoming_appointments,
        **_staff_portal_context(request.user),
    }

    return render(request, "dashboard_admin.html", context)


@login_required
def receptionist_dashboard(request):
    if not _is_receptionist_user(request.user):
        return redirect(_staff_redirect_name(request.user))

    today = timezone.localdate()
    todays_appointments = (
        Appointment.objects
        .filter(scheduled_start__date=today)
        .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
        .order_by("scheduled_start")
    )
    pending_appointment_requests = (
        AppointmentRequest.objects
        .filter(status=AppointmentRequestStatus.PENDING)
        .select_related("patient__user", "preferred_provider__staff_profile__user")
        .order_by("requested_start", "created_at")
    )
    outstanding_invoices = (
        Invoice.objects
        .exclude(status="paid")
        .select_related("patient__user", "appointment")
        .order_by("due_date", "-issued_at")[:6]
    )

    arrival_queue = todays_appointments.exclude(
        status__in=[AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]
    )
    checked_in_count = arrival_queue.filter(status=AppointmentStatus.CHECKED_IN).count()
    waiting_count = arrival_queue.filter(status=AppointmentStatus.SCHEDULED).count()

    return render(request, "dashboard_receptionist.html", {
        "staff_user": request.user,
        "arrival_queue": arrival_queue,
        "checked_in_count": checked_in_count,
        "waiting_count": waiting_count,
        "pending_request_count": pending_appointment_requests.count(),
        "pending_appointment_requests": pending_appointment_requests[:6],
        "outstanding_invoices": outstanding_invoices,
    })


@login_required
def nurse_dashboard(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    if not staff_profile or staff_profile.staff_role != StaffRole.NURSE:
        return redirect(_staff_redirect_name(request.user))

    today = timezone.localdate()
    todays_appointments = (
        Appointment.objects
        .filter(scheduled_start__date=today)
        .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
        .order_by("scheduled_start")
    )
    checked_in_count = todays_appointments.filter(status="checked_in").count()
    upcoming_count = todays_appointments.exclude(status="cancelled").count()
    patient_count = (
        PatientProfile.objects
        .filter(appointments__scheduled_start__date__gte=today)
        .distinct()
        .count()
    )

    return render(request, "dashboard_nurse.html", {
        "staff_user": request.user,
        "todays_appointments": todays_appointments[:8],
        "checked_in_count": checked_in_count,
        "upcoming_count": upcoming_count,
        "patient_count": patient_count,
    })


@login_required
def profile(request):
    return render(request, "profile.html")


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "edit_profile.html", {"form": form})

@login_required
def admin_profile(request):
    if not _can_access_staff_billing(request.user):
        return redirect("dashboard")

    return render(request, "admin_profile.html", {
        "admin_user": request.user,
        **_staff_portal_context(request.user),
    })


@login_required
def admin_billing(request):
    if not _can_access_staff_billing(request.user):
        return redirect("dashboard")

    invoices = (
        Invoice.objects
        .select_related("patient__user")
        .order_by("due_date", "-issued_at")
    )

    context = {
        "invoices": invoices,
        **_staff_portal_context(request.user),
    }

    return render(request, "admin_billing.html", context)


@login_required
def admin_create_invoice(request):
    if not _can_access_staff_billing(request.user):
        return redirect("dashboard")

    if request.method == "POST":
        form = AdminInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Invoice created successfully.")
            return redirect("admin_billing")
    else:
        form = AdminInvoiceForm()

    return render(request, "admin_create_invoice.html", {
        "form": form,
        **_staff_portal_context(request.user),
    })

from django.shortcuts import get_object_or_404


@login_required
def admin_delete_invoice(request, invoice_id):
    if not _can_delete_staff_invoice(request.user):
        return redirect("dashboard")

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == "POST":
        invoice.delete()
        messages.success(request, "Invoice deleted successfully.")
        return redirect("admin_billing")

    return render(request, "admin_confirm_delete.html", {
        "invoice": invoice,
        **_staff_portal_context(request.user),
    })

@login_required
def doctor_dashboard(request):
    staff_profile = getattr(request.user, "staff_profile", None)

    if not staff_profile:
        return render(request, "dashboard_doctor.html", {
            "provider": None,
            "appointments": [],
            "profile_missing": True,
        })

    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return render(request, "dashboard_doctor.html", {
            "provider": None,
            "appointments": [],
            "profile_missing": True,
        })

    appointments = (
        Appointment.objects
        .filter(provider=provider)
        .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
        .order_by("scheduled_start")
    )

    pending_appointment_requests = (
        AppointmentRequest.objects
        .filter(
            preferred_provider=provider,
            status=AppointmentRequestStatus.PENDING,
        )
        .select_related("patient__user", "preferred_provider__staff_profile__user")
        .order_by("requested_start", "created_at")
    )

    upcoming_count = appointments.filter(
        scheduled_start__gte=timezone.now()
    ).count()

    context = {
        "provider": provider,
        "appointments": appointments,
        "pending_appointment_requests": pending_appointment_requests,
        "upcoming_count": upcoming_count,
        "profile_missing": False,
    }

    return render(request, "dashboard_doctor.html", context)

@login_required
def doctor_appointments(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    appointments = []

    if provider:
        appointments = (
            Appointment.objects
            .filter(provider=provider)
            .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
            .order_by("scheduled_start")
        )

    return render(request, "doctor_appointments.html", {
        "appointments": appointments,
        "provider": provider,
    })


@login_required
def approve_appointment_request(request, request_id):
    if request.method != "POST":
        return redirect(_staff_redirect_name(request.user))

    appointment_request = get_object_or_404(
        AppointmentRequest.objects.select_related("preferred_provider"),
        id=request_id,
    )

    if not _staff_can_manage_request(request.user, appointment_request):
        messages.error(request, "You do not have permission to approve this appointment request.")
        return redirect(_staff_redirect_name(request.user))

    if appointment_request.status != AppointmentRequestStatus.PENDING:
        messages.info(request, "This appointment request has already been reviewed.")
        return redirect(request.POST.get("next") or reverse_lazy(_staff_redirect_name(request.user)))

    try:
        appointment_request.approve()
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Appointment request approved and scheduled successfully.")

    return redirect(request.POST.get("next") or reverse_lazy(_staff_redirect_name(request.user)))


@login_required
def reject_appointment_request(request, request_id):
    if request.method != "POST":
        return redirect(_staff_redirect_name(request.user))

    appointment_request = get_object_or_404(AppointmentRequest, id=request_id)

    if not _staff_can_manage_request(request.user, appointment_request):
        messages.error(request, "You do not have permission to reject this appointment request.")
        return redirect(_staff_redirect_name(request.user))

    if appointment_request.status != AppointmentRequestStatus.PENDING:
        messages.info(request, "This appointment request has already been reviewed.")
        return redirect(request.POST.get("next") or reverse_lazy(_staff_redirect_name(request.user)))

    appointment_request.reject()
    messages.success(request, "Appointment request rejected.")
    return redirect(request.POST.get("next") or reverse_lazy(_staff_redirect_name(request.user)))

@login_required
def doctor_appointment_detail(request, appointment_id):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return redirect("doctor_dashboard")

    appointment = (
        Appointment.objects
        .select_related(
            "patient__user",
            "provider__staff_profile__user",
            "pre_check_in_record",
        )
        .filter(
            id=appointment_id,
            provider=provider,
        )
        .first()
    )

    if not appointment:
        return redirect("doctor_appointments")

    return render(
        request,
        "doctor_appointment_detail.html",
        {
            "appointment": appointment,
            "provider": provider,
            "pre_check_in": getattr(appointment, "pre_check_in_record", None),
        },
    )


@login_required
def doctor_records(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return render(request, "doctor_records.html", {
            "provider": None,
            "records": [],
            "all_patients": [],
        })

    if request.method == "POST":
        patient_id = request.POST.get("patient_id")

        if patient_id:
            patient = PatientProfile.objects.get(id=patient_id)
            provider.patients.add(patient)
            return redirect("doctor_records")

    patients = provider.patients.select_related("user").all().order_by("user__last_name")

    records = []

    for patient in patients:
        patient_record, created = PatientRecord.objects.get_or_create(
            patient=patient,
            defaults={"primary_provider": provider},
        )

        latest_vitals = patient_record.vitals_records.order_by("-recorded_at").first()

        age = None
        if patient.date_of_birth:
            today = timezone.now().date()
            age = today.year - patient.date_of_birth.year - (
                    (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )

        records.append({
            "patient": patient,
            "age": age,
            "latest_vitals": latest_vitals,
        })

    all_patients = (
        PatientProfile.objects
        .select_related("user")
        .exclude(id__in=provider.patients.values_list("id", flat=True))
        .order_by("user__last_name")
    )

    return render(request, "doctor_records.html", {
        "provider": provider,
        "records": records,
        "all_patients": all_patients,
    })


@login_required
def nurse_records(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    if not staff_profile or staff_profile.staff_role != StaffRole.NURSE:
        return redirect(_staff_redirect_name(request.user))

    patients = (
        PatientProfile.objects
        .filter(appointments__isnull=False)
        .select_related("user")
        .distinct()
        .order_by("user__last_name", "user__first_name")
    )

    records = []
    for patient in patients:
        patient_record = PatientRecord.objects.filter(patient=patient).first()
        latest_vitals = patient_record.vitals_records.order_by("-recorded_at").first() if patient_record else None
        latest_appointment = (
            patient.appointments
            .select_related("provider__staff_profile__user", "pre_check_in_record")
            .exclude(status="cancelled")
            .order_by("-scheduled_start")
            .first()
        )
        age = None
        if patient.date_of_birth:
            today = timezone.now().date()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )

        records.append({
            "patient": patient,
            "record": patient_record,
            "latest_vitals": latest_vitals,
            "latest_appointment": latest_appointment,
            "age": age,
        })

    return render(request, "nurse_records.html", {
        "records": records,
    })


@login_required
def nurse_patient_record_detail(request, patient_id):
    staff_profile = getattr(request.user, "staff_profile", None)
    if not staff_profile or staff_profile.staff_role != StaffRole.NURSE:
        return redirect(_staff_redirect_name(request.user))

    patient = get_object_or_404(PatientProfile.objects.select_related("user"), id=patient_id)
    record, _ = PatientRecord.objects.get_or_create(patient=patient)

    vitals_form = VitalsRecordForm(request.POST or None, prefix="vitals")
    if request.method == "POST":
        if vitals_form.is_valid():
            vitals = vitals_form.save(commit=False)
            vitals.patient_record = record
            vitals.recorded_by = staff_profile
            latest_appointment = (
                patient.appointments
                .exclude(status="cancelled")
                .order_by("-scheduled_start")
                .first()
            )
            if latest_appointment:
                vitals.appointment = latest_appointment
            vitals.save()
            messages.success(request, "Vitals recorded successfully.")
            return redirect("nurse_patient_record_detail", patient_id=patient.id)

    latest_vitals = record.vitals_records.select_related("recorded_by__user").order_by("-recorded_at").first()
    prescriptions = record.prescriptions.select_related("prescribed_by__user").order_by("-created_at")
    clinical_notes = record.clinical_notes.select_related("author__user").order_by("-updated_at")
    lab_orders = record.lab_orders.select_related("ordered_by__user").order_by("-ordered_at")
    latest_appointment = (
        patient.appointments
        .select_related("provider__staff_profile__user", "pre_check_in_record")
        .exclude(status="cancelled")
        .order_by("-scheduled_start")
        .first()
    )

    age = None
    if patient.date_of_birth:
        today = timezone.now().date()
        age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

    return render(request, "nurse_patient_record_detail.html", {
        "patient": patient,
        "record": record,
        "latest_vitals": latest_vitals,
        "prescriptions": prescriptions,
        "clinical_notes": clinical_notes,
        "lab_orders": lab_orders,
        "latest_appointment": latest_appointment,
        "vitals_form": vitals_form,
        "age": age,
    })

@login_required
def doctor_patient_record_detail(request, patient_id):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return redirect("doctor_dashboard")

    patient = provider.patients.select_related("user").filter(id=patient_id).first()

    if not patient:
        return redirect("doctor_records")

    record, created = PatientRecord.objects.get_or_create(
        patient=patient,
        defaults={"primary_provider": provider},
    )

    note_form = ClinicalNoteForm(prefix="note")
    lab_order_form = LabOrderForm(prefix="lab-order")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_record":
            date_of_birth = request.POST.get("date_of_birth")

            if date_of_birth:
                patient.date_of_birth = date_of_birth
                patient.save()

            record.blood_type = request.POST.get("blood_type", "")
            record.allergies = request.POST.get("allergies", "")
            record.chronic_conditions = request.POST.get("chronic_conditions", "")
            record.general_notes = request.POST.get("general_notes", "")
            record.primary_provider = provider
            record.save()

            height_cm = request.POST.get("height_cm")
            weight_kg = request.POST.get("weight_kg")

            if height_cm or weight_kg:
                VitalsRecord.objects.create(
                    patient_record=record,
                    recorded_by=staff_profile,
                    height_cm=height_cm or None,
                    weight_kg=weight_kg or None,
                )

            medication_name = request.POST.get("medication_name")

            if medication_name:
                Prescription.objects.create(
                    patient_record=record,
                    prescribed_by=staff_profile,
                    medication_name=medication_name,
                    dosage=request.POST.get("dosage", ""),
                    frequency=request.POST.get("frequency", ""),
                    instructions=request.POST.get("instructions", ""),
                )

            messages.success(request, "Patient record updated.")
            return redirect("doctor_patient_record_detail", patient_id=patient.id)

        if action == "add_note":
            note_form = ClinicalNoteForm(request.POST, prefix="note")
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.patient_record = record
                note.author = staff_profile
                note.save()
                messages.success(request, "Clinical note added.")
                return redirect("doctor_patient_record_detail", patient_id=patient.id)

        if action == "add_lab_order":
            lab_order_form = LabOrderForm(request.POST, prefix="lab-order")
            if lab_order_form.is_valid():
                lab_order = lab_order_form.save(commit=False)
                lab_order.patient_record = record
                lab_order.ordered_by = staff_profile
                lab_order.save()
                messages.success(request, "Lab order created.")
                return redirect("doctor_patient_record_detail", patient_id=patient.id)

        if action == "review_lab_result":
            lab_order = get_object_or_404(LabOrder, id=request.POST.get("lab_order_id"), patient_record=record)
            result_instance = getattr(lab_order, "result", None)
            result_form = LabResultForm(request.POST, instance=result_instance, prefix=f"lab-result-{lab_order.id}")
            if result_form.is_valid():
                result = result_form.save(commit=False)
                result.lab_order = lab_order
                result.reviewed_by = staff_profile
                result.save()
                messages.success(request, "Lab result saved and reviewed.")
                return redirect("doctor_patient_record_detail", patient_id=patient.id)

    latest_vitals = record.vitals_records.order_by("-recorded_at").first()
    prescriptions = record.prescriptions.order_by("-created_at")
    clinical_notes = record.clinical_notes.select_related("author__user").order_by("-updated_at")
    lab_orders = record.lab_orders.select_related("ordered_by__user").prefetch_related("result").order_by("-ordered_at")

    age = None
    if patient.date_of_birth:
        today = timezone.now().date()
        age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

    return render(request, "doctor_patient_record_detail.html", {
        "patient": patient,
        "record": record,
        "latest_vitals": latest_vitals,
        "prescriptions": prescriptions,
        "clinical_notes": clinical_notes,
        "lab_orders": lab_orders,
        "note_form": note_form,
        "lab_order_form": lab_order_form,
        "lab_result_statuses": LabResult._meta.get_field("status").choices,
        "provider": provider,
        "age": age,
    })


@login_required
def doctor_billing(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return render(request, "doctor_billing.html", {
            "provider": None,
            "invoices": [],
        })

    invoices = (
        Invoice.objects
        .filter(patient__in=provider.patients.all())
        .select_related("patient__user", "appointment")
        .order_by("-issued_at")
    )

    return render(request, "doctor_billing.html", {
        "provider": provider,
        "invoices": invoices,
    })

@login_required
def doctor_edit_prescription(request, patient_id, prescription_id):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return redirect("doctor_dashboard")

    patient = provider.patients.filter(id=patient_id).first()

    if not patient:
        return redirect("doctor_records")

    prescription = Prescription.objects.filter(
        id=prescription_id,
        patient_record__patient=patient,
    ).first()

    if not prescription:
        return redirect("doctor_patient_record_detail", patient_id=patient.id)

    if request.method == "POST":
        prescription.medication_name = request.POST.get("medication_name", "")
        prescription.dosage = request.POST.get("dosage", "")
        prescription.frequency = request.POST.get("frequency", "")
        prescription.instructions = request.POST.get("instructions", "")
        prescription.status = request.POST.get("status", prescription.status)
        prescription.save()

        return redirect("doctor_patient_record_detail", patient_id=patient.id)

    return render(request, "doctor_edit_prescription.html", {
        "patient": patient,
        "prescription": prescription,
    })


@login_required
def doctor_edit_clinical_note(request, patient_id, note_id):
    staff_profile = getattr(request.user, "staff_profile", None)
    provider = getattr(staff_profile, "provider_profile", None)

    if not provider:
        return redirect("doctor_dashboard")

    patient = provider.patients.filter(id=patient_id).first()
    if not patient:
        return redirect("doctor_records")

    note = ClinicalNote.objects.filter(
        id=note_id,
        patient_record__patient=patient,
    ).first()
    if not note:
        return redirect("doctor_patient_record_detail", patient_id=patient.id)

    form = ClinicalNoteForm(request.POST or None, instance=note, prefix="note")
    if request.method == "POST" and form.is_valid():
        updated_note = form.save(commit=False)
        updated_note.author = staff_profile
        updated_note.save()
        messages.success(request, "Clinical note updated.")
        return redirect("doctor_patient_record_detail", patient_id=patient.id)

    return render(request, "doctor_edit_clinical_note.html", {
        "patient": patient,
        "note": note,
        "form": form,
    })
