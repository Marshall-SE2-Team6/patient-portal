from django.contrib import admin

from .models import (
    Appointment,
    AppointmentRequest,
    AvailabilitySlot,
    CheckInRecord,
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
    list_display = ("id", "patient", "preferred_provider", "status", "created_at")
    list_filter = ("status",)
    search_fields = (
        "patient__user__username",
        "preferred_provider__staff_profile__user__username",
    )

admin.site.register(Appointment)

@admin.register(CheckInRecord)
class CheckInRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "checked_in_at", "checked_in_by")
    search_fields = (
        "appointment__patient__user__username",
        "checked_in_by__user__username",
    )
