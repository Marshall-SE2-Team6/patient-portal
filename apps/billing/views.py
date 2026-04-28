from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PaymentSubmissionForm
from .models import Invoice


@login_required
def invoice_list(request):
    patient_profile = getattr(request.user, "patient_profile", None)

    if not patient_profile:
        return render(request, "billing/invoice_list.html", {
            "invoice_rows": [],
            "profile_missing": True,
        })

    invoices = (
        Invoice.objects
        .filter(patient=patient_profile)
        .prefetch_related("line_items", "payments__payment_method")
        .order_by("-issued_at", "due_date")
    )

    invoice_rows = [
        {
            "invoice": invoice,
            "payment_form": PaymentSubmissionForm(
                invoice=invoice,
                patient=patient_profile,
                prefix=f"invoice-{invoice.id}",
            ),
        }
        for invoice in invoices
    ]

    return render(request, "billing/invoice_list.html", {
        "invoice_rows": invoice_rows,
        "profile_missing": False,
    })


@login_required
def pay_invoice(request, invoice_id):
    patient_profile = getattr(request.user, "patient_profile", None)
    if request.method != "POST" or not patient_profile:
        return redirect("billing:invoice_list")

    invoice = get_object_or_404(
        Invoice.objects.prefetch_related("line_items", "payments"),
        id=invoice_id,
        patient=patient_profile,
    )

    form = PaymentSubmissionForm(
        request.POST,
        invoice=invoice,
        patient=patient_profile,
        prefix=f"invoice-{invoice.id}",
    )

    if form.is_valid():
        form.save()
        invoice.refresh_totals()
        messages.success(request, f"Payment recorded for invoice {invoice.invoice_number}.")
    else:
        messages.error(request, "We could not process that payment. Please review the form and try again.")

    invoices = (
        Invoice.objects
        .filter(patient=patient_profile)
        .prefetch_related("line_items", "payments__payment_method")
        .order_by("-issued_at", "due_date")
    )
    invoice_rows = []
    for current_invoice in invoices:
        payment_form = form if current_invoice.id == invoice.id else PaymentSubmissionForm(
            invoice=current_invoice,
            patient=patient_profile,
            prefix=f"invoice-{current_invoice.id}",
        )
        invoice_rows.append({
            "invoice": current_invoice,
            "payment_form": payment_form,
        })

    return render(request, "billing/invoice_list.html", {
        "invoice_rows": invoice_rows,
        "profile_missing": False,
    })
