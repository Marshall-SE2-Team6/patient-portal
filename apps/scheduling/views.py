from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from apps.scheduling.models import Appointment
from apps.scheduling.models.appointment import AppointmentStatus
from .forms import AppointmentRequestForm


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
            appointment = form.save(commit=False)
            appointment.patient = patient_profile
            appointment.status = AppointmentStatus.SCHEDULED
            appointment.reminder_sent = False
            appointment.save()
            return redirect("dashboard")
    else:
        form = AppointmentRequestForm()

    return render(request, "scheduling/request_appointment.html", {
        "form": form,
        "profile_missing": False,
    })


@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user.patient_profile,
    )

    return render(request, "scheduling/appointment_detail.html", {
        "appointment": appointment
    })