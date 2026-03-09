from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.billing.models import Invoice
from apps.records.models import LabResult
from apps.scheduling.models import Appointment

from .forms import SignUpForm, ProfileForm


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


@login_required
def dashboard(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    upcoming_appointments = []
    recent_lab_results = []
    open_invoices = []

    if patient_profile:
        upcoming_appointments = (
            Appointment.objects
            .filter(
                patient=patient_profile,
                scheduled_start__gte=timezone.now(),
            )
            .select_related("provider__staff_profile__user")
            .order_by("scheduled_start")[:5]
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
        "recent_lab_results": recent_lab_results,
        "open_invoices": open_invoices,
    }

    return render(request, "dashboard.html", context)


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