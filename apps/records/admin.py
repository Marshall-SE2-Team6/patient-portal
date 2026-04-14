from django.contrib import admin
from .models import Appointment

from .models import (
    ClinicalNote,
    LabOrder,
    LabResult,
    MedicalSummary,
    Medication,
    PatientRecord,
    Prescription,
    RecordFlag,
    SupportingDocument,
    VitalsRecord,
)


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "primary_provider", "created_at")
    search_fields = ("patient__user__username", "patient__user__email")


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "title", "note_type", "author", "created_at")
    list_filter = ("note_type",)
    search_fields = ("title", "patient_record__patient__user__username")


@admin.register(VitalsRecord)
class VitalsRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "recorded_at", "recorded_by")
    search_fields = ("patient_record__patient__user__username",)


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "test_name", "status", "ordered_by", "ordered_at")
    list_filter = ("status",)
    search_fields = ("test_name", "patient_record__patient__user__username")


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("id", "lab_order", "status", "reviewed_by", "resulted_at")
    list_filter = ("status",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "medication_name", "status", "prescribed_by")
    list_filter = ("status",)
    search_fields = ("medication_name", "patient_record__patient__user__username")


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "patient_record__patient__user__username")


@admin.register(SupportingDocument)
class SupportingDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "title", "document_type", "uploaded_at")
    list_filter = ("document_type",)
    search_fields = ("title", "patient_record__patient__user__username")


@admin.register(RecordFlag)
class RecordFlagAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "flag_type", "is_active", "created_at")
    list_filter = ("flag_type", "is_active")


@admin.register(MedicalSummary)
class MedicalSummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_record", "last_updated_by", "updated_at")

admin.site.register(Appointment)