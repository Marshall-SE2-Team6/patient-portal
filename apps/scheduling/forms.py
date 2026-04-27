from django import forms
from django.db import models

from django.utils import timezone

from apps.profiles.models import PatientProfile
from apps.scheduling.models import Appointment, AppointmentRequest, AvailabilitySlot, PreCheckInRecord, Provider


class AppointmentRequestForm(forms.ModelForm):
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.none(),
        label="Provider",
    )
    requested_slot = forms.ModelChoiceField(
        queryset=AvailabilitySlot.objects.none(),
        label="Available Time",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = AppointmentRequest
        fields = ["provider", "requested_slot", "reason", "notes"]

    def __init__(self, *args, selected_provider=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provider"].queryset = Provider.objects.filter(accepts_new_patients=True)
        slot_queryset = AvailabilitySlot.objects.none()
        provider_id = None

        if selected_provider:
            try:
                provider_id = int(selected_provider)
            except (TypeError, ValueError):
                provider_id = None

        if provider_id:
            slot_queryset = (
                AvailabilitySlot.objects
                .filter(
                    provider_id=provider_id,
                    is_booked=False,
                    start_time__gte=timezone.now(),
                )
                .select_related("provider__staff_profile__user")
                .order_by("start_time")
            )
            self.initial.setdefault("provider", provider_id)

        self.fields["requested_slot"].queryset = slot_queryset

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")
        self.fields["requested_slot"].label_from_instance = (
            lambda slot: (
                f"Dr. {slot.provider.staff_profile.user.first_name} "
                f"{slot.provider.staff_profile.user.last_name} - "
                f"{slot.start_time.strftime('%b %d, %Y %I:%M %p')}"
            )
        )
        self.fields["requested_slot"].empty_label = "Select an available time"

    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get("provider")
        slot = cleaned_data.get("requested_slot")

        if slot and slot.is_booked:
            raise forms.ValidationError("That time slot was just booked. Please choose another one.")
        if provider and slot and slot.provider_id != provider.id:
            raise forms.ValidationError("Please choose a time slot that belongs to the selected provider.")

        return cleaned_data

    def save(self, commit=True, *, patient=None):
        appointment_request = super().save(commit=False)
        appointment_request.patient = patient
        appointment_request.preferred_provider = self.cleaned_data["provider"]
        appointment_request.requested_slot = self.cleaned_data["requested_slot"]
        appointment_request.requested_start = self.cleaned_data["requested_slot"].start_time
        appointment_request.requested_end = self.cleaned_data["requested_slot"].end_time

        notes = self.cleaned_data.get("notes", "").strip()
        reason = self.cleaned_data.get("reason", "").strip()
        if notes:
            appointment_request.reason = (
                f"{reason}\n\nPatient notes: {notes}" if reason else f"Patient notes: {notes}"
            )
        else:
            appointment_request.reason = reason

        if commit:
            appointment_request.save()

        return appointment_request


class AppointmentRescheduleForm(forms.Form):
    slot = forms.ModelChoiceField(
        queryset=AvailabilitySlot.objects.none(),
        label="New Available Time",
    )

    def __init__(self, *args, appointment=None, **kwargs):
        self.appointment = appointment
        super().__init__(*args, **kwargs)
        slot_queryset = (
            AvailabilitySlot.objects
            .filter(is_booked=False, start_time__gte=timezone.now())
            .select_related("provider__staff_profile__user")
            .order_by("start_time")
        )

        if appointment and appointment.availability_slot_id:
            slot_queryset = AvailabilitySlot.objects.filter(
                models.Q(pk=appointment.availability_slot_id) |
                models.Q(is_booked=False, start_time__gte=timezone.now())
            ).select_related("provider__staff_profile__user").order_by("start_time")

        self.fields["slot"].queryset = slot_queryset
        self.fields["slot"].widget.attrs.setdefault("class", "portal-form-input")
        self.fields["slot"].label_from_instance = (
            lambda slot: (
                f"Dr. {slot.provider.staff_profile.user.first_name} "
                f"{slot.provider.staff_profile.user.last_name} - "
                f"{slot.start_time.strftime('%b %d, %Y %I:%M %p')}"
            )
        )


class StaffScheduleAppointmentForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=PatientProfile.objects.none())
    slot = forms.ModelChoiceField(queryset=AvailabilitySlot.objects.none(), label="Available Time")
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = PatientProfile.objects.select_related("user").order_by("user__last_name", "user__first_name")
        self.fields["slot"].queryset = (
            AvailabilitySlot.objects
            .filter(is_booked=False, start_time__gte=timezone.now())
            .select_related("provider__staff_profile__user")
            .order_by("start_time")
        )

        self.fields["patient"].label_from_instance = (
            lambda patient: f"{patient.user.first_name} {patient.user.last_name} ({patient.user.username})"
        )
        self.fields["slot"].label_from_instance = (
            lambda slot: (
                f"Dr. {slot.provider.staff_profile.user.first_name} "
                f"{slot.provider.staff_profile.user.last_name} - "
                f"{slot.start_time.strftime('%b %d, %Y %I:%M %p')}"
            )
        )

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")

    def clean_slot(self):
        slot = self.cleaned_data["slot"]
        if slot.is_booked:
            raise forms.ValidationError("That time slot is no longer available.")
        return slot

    def save(self):
        slot = self.cleaned_data["slot"]
        appointment = Appointment.objects.create(
            patient=self.cleaned_data["patient"],
            provider=slot.provider,
            availability_slot=slot,
            scheduled_start=slot.start_time,
            scheduled_end=slot.end_time,
            reason=self.cleaned_data["reason"].strip(),
            notes=self.cleaned_data["notes"].strip(),
        )
        slot.is_booked = True
        slot.save(update_fields=["is_booked"])
        slot.provider.patients.add(self.cleaned_data["patient"])
        appointment.send_notification(
            subject="Appointment Scheduled",
            message=(
                f"Your appointment is scheduled for "
                f"{appointment.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}."
            ),
            notification_type="appointment_status",
        )
        return appointment


class PreCheckInForm(forms.ModelForm):
    class Meta:
        model = PreCheckInRecord
        fields = [
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "emergency_contact_name",
            "emergency_contact_phone",
            "symptoms",
            "current_medications",
            "allergies",
            "insurance_provider",
            "insurance_member_id",
            "accommodation_notes",
            "additional_notes",
        ]
        widgets = {
            "symptoms": forms.Textarea(attrs={"rows": 3}),
            "current_medications": forms.Textarea(attrs={"rows": 3}),
            "allergies": forms.Textarea(attrs={"rows": 3}),
            "accommodation_notes": forms.Textarea(attrs={"rows": 3}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "phone_number": "Best phone number",
            "emergency_contact_name": "Emergency contact name",
            "emergency_contact_phone": "Emergency contact phone",
            "symptoms": "Current symptoms or concerns",
            "current_medications": "Current medications",
            "insurance_provider": "Insurance provider",
            "insurance_member_id": "Insurance member ID",
            "accommodation_notes": "Accessibility or accommodation needs",
            "additional_notes": "Anything else the clinic should know",
        }

    def __init__(self, *args, patient_profile=None, **kwargs):
        self.patient_profile = patient_profile
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")

        if patient_profile and not self.instance.pk:
            self.initial.setdefault("phone_number", patient_profile.phone_number)
            self.initial.setdefault("address_line_1", patient_profile.address_line_1)
            self.initial.setdefault("address_line_2", patient_profile.address_line_2)
            self.initial.setdefault("city", patient_profile.city)
            self.initial.setdefault("state", patient_profile.state)
            self.initial.setdefault("postal_code", patient_profile.postal_code)
            self.initial.setdefault("emergency_contact_name", patient_profile.emergency_contact_name)
            self.initial.setdefault("emergency_contact_phone", patient_profile.emergency_contact_phone)

    def save(self, commit=True, *, appointment=None, patient_profile=None):
        record = super().save(commit=False)
        if appointment is not None:
            record.appointment = appointment

        profile = patient_profile or self.patient_profile
        if profile is not None:
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.address_line_1 = self.cleaned_data["address_line_1"]
            profile.address_line_2 = self.cleaned_data["address_line_2"]
            profile.city = self.cleaned_data["city"]
            profile.state = self.cleaned_data["state"]
            profile.postal_code = self.cleaned_data["postal_code"]
            profile.emergency_contact_name = self.cleaned_data["emergency_contact_name"]
            profile.emergency_contact_phone = self.cleaned_data["emergency_contact_phone"]

            if commit:
                profile.save()

        if commit:
            record.save()

        return record
