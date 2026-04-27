from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.profiles.models import StaffRole
from apps.scheduling.models import Appointment, AppointmentRequestStatus
from apps.scheduling.models.appointment import AppointmentStatus

from .forms import (
    AppointmentRequestForm,
    AppointmentRescheduleForm,
    PreCheckInForm,
    StaffScheduleAppointmentForm,
)


def _staff_profile(user):
    return getattr(user, "staff_profile", None)


def _is_non_physician_staff(user):
    staff_profile = _staff_profile(user)
    return bool(
        user.is_superuser
        or (
            staff_profile
            and staff_profile.staff_role in {
                StaffRole.RECEPTIONIST,
                StaffRole.NURSE,
                StaffRole.ADMIN,
            }
        )
        or (user.is_staff and not staff_profile)
    )


def _can_check_in(user):
    staff_profile = _staff_profile(user)
    return bool(
        user.is_superuser
        or (
            staff_profile
            and staff_profile.staff_role in {
                StaffRole.RECEPTIONIST,
                StaffRole.NURSE,
            }
        )
    )


def _actor_label(user):
    staff_profile = _staff_profile(user)
    if not staff_profile:
        return "Patient"
    return {
        StaffRole.PHYSICIAN: "Doctor",
        StaffRole.NURSE: "Nurse",
        StaffRole.RECEPTIONIST: "Receptionist",
        StaffRole.ADMIN: "Staff",
    }.get(staff_profile.staff_role, "Staff")


def _staff_can_access_appointment(user, appointment):
    if user.is_superuser:
        return True

    staff_profile = _staff_profile(user)
    if not staff_profile:
        return bool(user.is_staff)

    if staff_profile.staff_role == StaffRole.PHYSICIAN:
        provider = getattr(staff_profile, "provider_profile", None)
        return provider is not None and appointment.provider_id == provider.id

    return staff_profile.staff_role in {
        StaffRole.RECEPTIONIST,
        StaffRole.NURSE,
        StaffRole.ADMIN,
    }


@login_required
def request_appointment(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    if not patient_profile:
        return render(request, "scheduling/request_appointment.html", {
            "form": None,
            "profile_missing": True,
        })

    selected_provider = request.POST.get("provider") if request.method == "POST" else request.GET.get("provider")

    if request.method == "POST":
        form = AppointmentRequestForm(request.POST, selected_provider=selected_provider)
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
        form = AppointmentRequestForm(selected_provider=selected_provider)

    available_slots = form.fields["requested_slot"].queryset[:10] if form else []

    return render(request, "scheduling/request_appointment.html", {
        "form": form,
        "profile_missing": False,
        "available_slots": available_slots,
        "selected_provider": selected_provider,
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
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient__user", "availability_slot", "provider__staff_profile__user"),
        id=appointment_id,
    )

    is_patient_owner = getattr(request.user, "patient_profile", None) == appointment.patient
    if not (is_patient_owner or _staff_can_access_appointment(request.user, appointment)):
        messages.error(request, "You do not have permission to reschedule this appointment.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AppointmentRescheduleForm(request.POST, appointment=appointment)
        if form.is_valid():
            try:
                appointment.reschedule_to_slot(
                    form.cleaned_data["slot"],
                    actor_label=_actor_label(request.user),
                )
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Appointment rescheduled successfully.")
                if is_patient_owner:
                    return redirect("appointment_detail", appointment_id=appointment.id)
                return redirect("staff_appointments")
    else:
        form = AppointmentRescheduleForm(appointment=appointment)

    return render(request, "scheduling/reschedule_appointment.html", {
        "appointment": appointment,
        "form": form,
        "is_patient_owner": is_patient_owner,
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient__user"),
        id=appointment_id,
    )
    is_patient_owner = getattr(request.user, "patient_profile", None) == appointment.patient

    if request.method != "POST":
        if is_patient_owner:
            return redirect("appointment_detail", appointment_id=appointment.id)
        return redirect("staff_appointments")

    if not (is_patient_owner or _staff_can_access_appointment(request.user, appointment)):
        messages.error(request, "You do not have permission to cancel this appointment.")
        return redirect("dashboard")

    try:
        appointment.cancel(actor_label=_actor_label(request.user))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Appointment cancelled successfully.")

    if is_patient_owner:
        return redirect("my_appointments")
    return redirect("staff_appointments")


@login_required
def staff_appointments(request):
    if not _is_non_physician_staff(request.user):
        return redirect("dashboard")

    appointments = (
        Appointment.objects
        .select_related("patient__user", "provider__staff_profile__user", "pre_check_in_record")
        .order_by("scheduled_start")
    )

    return render(request, "scheduling/staff_appointments.html", {
        "appointments": appointments,
    })


@login_required
def staff_schedule_appointment(request):
    if not _is_non_physician_staff(request.user):
        return redirect("dashboard")

    if request.method == "POST":
        form = StaffScheduleAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, "Appointment scheduled successfully.")
            return redirect("staff_appointments")
    else:
        form = StaffScheduleAppointmentForm()

    return render(request, "scheduling/staff_schedule_appointment.html", {
        "form": form,
    })


@login_required
def check_in_appointment(request, appointment_id):
    if request.method != "POST":
        return redirect("staff_appointments")

    appointment = get_object_or_404(Appointment, id=appointment_id)
    if not _can_check_in(request.user):
        messages.error(request, "Only reception or nursing staff can check in patients.")
        return redirect("dashboard")

    try:
        appointment.check_in(actor_label=_actor_label(request.user))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        check_in_record = getattr(appointment, "check_in_record", None)
        if not check_in_record:
            from apps.scheduling.models import CheckInRecord

            CheckInRecord.objects.get_or_create(
                appointment=appointment,
                defaults={"checked_in_by": _staff_profile(request.user)},
            )
        messages.success(request, "Patient checked in successfully.")

    return redirect("staff_appointments")


@login_required
def complete_appointment(request, appointment_id):
    if request.method != "POST":
        return redirect("dashboard")

    appointment = get_object_or_404(Appointment, id=appointment_id)
    if not _staff_can_access_appointment(request.user, appointment):
        messages.error(request, "You do not have permission to update this appointment.")
        return redirect("dashboard")

    try:
        appointment.complete(actor_label=_actor_label(request.user))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Appointment marked as completed.")

    return redirect("doctor_appointments" if _staff_profile(request.user) and _staff_profile(request.user).staff_role == StaffRole.PHYSICIAN else "staff_appointments")


@login_required
def mark_no_show_appointment(request, appointment_id):
    if request.method != "POST":
        return redirect("dashboard")

    appointment = get_object_or_404(Appointment, id=appointment_id)
    if not _staff_can_access_appointment(request.user, appointment):
        messages.error(request, "You do not have permission to update this appointment.")
        return redirect("dashboard")

    try:
        appointment.mark_no_show(actor_label=_actor_label(request.user))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Appointment marked as no-show.")

    return redirect("doctor_appointments" if _staff_profile(request.user) and _staff_profile(request.user).staff_role == StaffRole.PHYSICIAN else "staff_appointments")


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
