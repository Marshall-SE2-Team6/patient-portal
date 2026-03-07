from django.contrib import admin

from .models import PatientProfile, StaffProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone_number", "date_of_birth", "created_at")
    search_fields = ("user__username", "user__email", "phone_number")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "staff_role", "department", "is_active_staff")
    search_fields = ("user__username", "user__email", "department", "employee_id")
    list_filter = ("staff_role", "is_active_staff")
