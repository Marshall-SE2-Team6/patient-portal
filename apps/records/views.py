from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import ClinicalNote, LabResult, Prescription


@login_required
def my_records(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_dashboard")

    patient_profile = getattr(request.user, "patient_profile", None)
    patient_record = getattr(patient_profile, "record", None) if patient_profile else None

    lab_results = []
    prescriptions = []
    clinical_notes = []
    if patient_record:
        lab_results = (
            LabResult.objects
            .filter(lab_order__patient_record=patient_record)
            .select_related("lab_order", "reviewed_by__user")
            .order_by("-resulted_at")
        )
        prescriptions = (
            Prescription.objects
            .filter(patient_record=patient_record)
            .select_related("prescribed_by__user")
            .order_by("-created_at")
        )
        clinical_notes = (
            ClinicalNote.objects
            .filter(patient_record=patient_record)
            .select_related("author__user")
            .order_by("-updated_at")
        )

    context = {
        "patient_profile": patient_profile,
        "patient_record": patient_record,
        "lab_results": lab_results,
        "prescriptions": prescriptions,
        "clinical_notes": clinical_notes,
    }
    return render(request, "records/my_records.html", context)
