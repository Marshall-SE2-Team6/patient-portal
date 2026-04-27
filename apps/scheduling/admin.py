from django.contrib import admin

from .models import (
    Appointment,
    AppointmentRequest,
    AvailabilitySlot,
    CheckInRecord,
    PreCheckInRecord,
    Provider,
)


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("id", "staff_profile", "specialty", "accepts_new_patients")
    search_fields = (
        "staff_profile__user__username",
        "staff_profile__user__email",
        "specialty",
    )
    list_filter = ("accepts_new_patients",)


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "start_time", "end_time", "is_booked")
    list_filter = ("is_booked",)
    search_fields = ("provider__staff_profile__user__username",)


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "preferred_provider", "status", "created_at", "linked_appointment")
    list_editable = ("status",)
    list_filter = ("status",)
    search_fields = (
        "patient__user__username",
        "preferred_provider__staff_profile__user__username",
    )

    def linked_appointment(self, obj):
        return getattr(obj, "appointment", None)

    def save_model(self, request, obj, form, change):
        if obj.status == "approved":
            obj.approve()
            return
        if obj.status == "rejected":
            obj.reject()
            return
        if obj.status == "cancelled":
            obj.cancel()
            return

        super().save_model(request, obj, form, change)

admin.site.register(Appointment)


@admin.register(PreCheckInRecord)
class PreCheckInRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "phone_number", "insurance_provider", "updated_at")
    search_fields = (
        "appointment__patient__user__username",
        "appointment__provider__staff_profile__user__username",
        "phone_number",
        "insurance_provider",
    )


@admin.register(CheckInRecord)
class CheckInRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "checked_in_at", "checked_in_by")
    search_fields = (
        "appointment__patient__user__username",
        "checked_in_by__user__username",
    )
