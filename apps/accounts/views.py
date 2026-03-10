from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import transaction
from django.urls import reverse_lazy

from apps.billing.models import Invoice
from apps.records.models import LabResult
from apps.scheduling.models import Appointment
from apps.profiles.models import PatientProfile

from .forms import SignUpForm, ProfileForm


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