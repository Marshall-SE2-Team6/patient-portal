from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.urls import reverse_lazy

from apps.billing.models import Invoice
from apps.profiles.models import PatientProfile, StaffRole
from apps.records.models import LabResult, PatientRecord, VitalsRecord, Prescription
from apps.scheduling.models import Appointment, AppointmentRequest, AppointmentRequestStatus, Provider
from apps.records.models import PatientRecord

from .forms import SignUpForm, ProfileForm, AdminInvoiceForm


def _staff_redirect_name(user):
    staff_profile = getattr(user, "staff_profile", None)
    if staff_profile and staff_profile.staff_role == StaffRole.PHYSICIAN:
        return "doctor_dashboard"
    return "admin_dashboard"


def _staff_can_manage_request(user, appointment_request):
    staff_profile = getattr(user, "staff_profile", None)
    if user.is_superuser:
        return True
    if not staff_profile:
        return bool(user.is_staff)
    if staff_profile.staff_role == StaffRole.PHYSICIAN:
        provider = getattr(staff_profile, "provider_profile", None)
        return provider is not None and appointment_request.preferred_provider_id == provider.id
    return True


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

    if staff_profile:
        if staff_profile.staff_role == "physician":
            return redirect("doctor_dashboard")
        return redirect("admin_dashboard")

    patient_profile = getattr(request.user, "patient_profile", None)

    upcoming_appointments = []
    pending_appointment_requests = []
    recent_lab_results = []
    open_invoices = []

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

    context = {
        "patient_profile": patient_profile,
        "upcoming_appointments": upcoming_appointments,
        "pending_appointment_requests": pending_appointment_requests,
        "recent_lab_results": recent_lab_results,
        "open_invoices": open_invoices,
    }

    return render(request, "dashboard.html", context)

@login_required
def patient_dashboard(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    upcoming_appointments = []
    pending_appointment_requests = []
    recent_lab_results = []
    open_invoices = []

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

    context = {
        "patient_profile": patient_profile,
        "upcoming_appointments": upcoming_appointments,
        "pending_appointment_requests": pending_appointment_requests,
        "recent_lab_results": recent_lab_results,
        "open_invoices": open_invoices,
    }

    return render(request, "dashboard.html", context)


@login_required
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    pending_appointment_requests = (
        AppointmentRequest.objects
        .filter(status=AppointmentRequestStatus.PENDING)
        .select_related("patient__user", "preferred_provider__staff_profile__user")
        .order_by("requested_start", "created_at")
    )

    context = {
        "admin_user": request.user,
        "pending_appointment_requests": pending_appointment_requests,
    }

    return render(request, "dashboard_admin.html", context)


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
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    return render(request, "admin_profile.html", {"admin_user": request.user})


@login_required
def admin_billing(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    invoices = (
        Invoice.objects
        .select_related("patient__user")
        .order_by("due_date", "-issued_at")
    )

    context = {
        "invoices": invoices,
    }

    return render(request, "admin_billing.html", context)


@login_required
def admin_create_invoice(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    if request.method == "POST":
        form = AdminInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Invoice created successfully.")
            return redirect("admin_billing")
    else:
        form = AdminInvoiceForm()

    return render(request, "admin_create_invoice.html", {"form": form})

from django.shortcuts import get_object_or_404


@login_required
def admin_delete_invoice(request, invoice_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == "POST":
        invoice.delete()
        messages.success(request, "Invoice deleted successfully.")
        return redirect("admin_billing")

    return render(request, "admin_confirm_delete.html", {
        "invoice": invoice
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

    if request.method == "POST":
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

        return redirect("doctor_patient_record_detail", patient_id=patient.id)

    latest_vitals = record.vitals_records.order_by("-recorded_at").first()
    prescriptions = record.prescriptions.order_by("-created_at")

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
