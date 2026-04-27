from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.scheduling.models import Appointment, AppointmentRequestStatus
from apps.scheduling.models.appointment import AppointmentStatus

from .forms import AppointmentRequestForm, PreCheckInForm


@login_required
def request_appointment(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    if not patient_profile:
        return render(request, "scheduling/request_appointment.html", {
            "form": None,
            "profile_missing": True,
        })

    if request.method == "POST":
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            appointment_request = form.save(patient=patient_profile)
            provider = appointment_request.preferred_provider
            if provider:
                provider.patients.add(patient_profile)
            messages.success(
                request,
                "Your appointment request was sent. It will stay pending until a doctor or receptionist approves it.",
            )
            return redirect("my_appointments")
    else:
        form = AppointmentRequestForm()

    return render(request, "scheduling/request_appointment.html", {
        "form": form,
        "profile_missing": False,
    })

@login_required
def my_appointments(request):
    patient_profile = getattr(request.user, 'patient_profile', None)

    if not patient_profile:
        return render(request, 'scheduling/my_appointments.html', {
            'appointments': [],
            'profile_missing': True,
        })

    appointments = (
        patient_profile.appointments
        .select_related("provider__staff_profile__user", "pre_check_in_record")
        .order_by("-scheduled_start")
    )
    pending_requests = (
        patient_profile.appointment_requests
        .select_related("preferred_provider__staff_profile__user")
        .filter(status=AppointmentRequestStatus.PENDING)
        .order_by("-created_at")
    )
    now = timezone.now()

    for appointment in appointments:
        if appointment.scheduled_end and appointment.scheduled_end < now:
            appointment.display_status = "Completed"
        else:
            appointment.display_status = appointment.status.capitalize()

    return render(request, 'scheduling/my_appointments.html', {
        'appointments': appointments,
        'pending_requests': pending_requests,
        'profile_missing': False,
    })

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "provider__staff_profile__user",
            "pre_check_in_record",
        ),
        id=appointment_id,
        patient=request.user.patient_profile,
    )

    return render(request, "scheduling/appointment_detail.html", {
        "appointment": appointment,
        "pre_check_in": getattr(appointment, "pre_check_in_record", None),
    })


@login_required
def pre_check_in(request, appointment_id):
    patient_profile = getattr(request.user, "patient_profile", None)

    if not patient_profile:
        messages.error(request, "You need a patient profile before using pre-check-in.")
        return redirect("my_appointments")

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "provider__staff_profile__user",
            "pre_check_in_record",
        ),
        id=appointment_id,
        patient=patient_profile,
    )

    if not appointment.can_pre_check_in:
        messages.error(
            request,
            "Pre-check-in is only available for scheduled visits that have not ended yet.",
        )
        return redirect("appointment_detail", appointment_id=appointment.id)

    record = getattr(appointment, "pre_check_in_record", None)

    if request.method == "POST":
        form = PreCheckInForm(
            request.POST,
            instance=record,
            patient_profile=patient_profile,
        )
        is_new_record = record is None

        if form.is_valid():
            form.save(appointment=appointment, patient_profile=patient_profile)
            messages.success(
                request,
                "Pre-check-in submitted successfully."
                if is_new_record
                else "Pre-check-in updated successfully.",
            )
            return redirect("appointment_detail", appointment_id=appointment.id)
    else:
        form = PreCheckInForm(instance=record, patient_profile=patient_profile)

    return render(
        request,
        "scheduling/pre_check_in.html",
        {
            "appointment": appointment,
            "form": form,
            "pre_check_in": record,
        },
    )
