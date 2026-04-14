from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.urls import reverse_lazy

from apps.billing.models import Invoice
from apps.records.models import LabResult
from apps.scheduling.models import Appointment
from apps.profiles.models import PatientProfile

from .forms import SignUpForm, ProfileForm, AdminInvoiceForm


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
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_dashboard")

    return redirect("patient_dashboard")


@login_required
def patient_dashboard(request):
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
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")

    context = {
        "admin_user": request.user,
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