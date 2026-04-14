from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Invoice


@login_required
def invoice_list(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    if not patient_profile:
        return render(request, "billing/invoice_list.html", {
            "invoices": [],
            "profile_missing": True,
        })

    invoices = (
        Invoice.objects
        .filter(patient=patient_profile)
        .order_by("-issued_at", "due_date")
    )

    return render(request, "billing/invoice_list.html", {
        "invoices": invoices,
        "profile_missing": False,
    })