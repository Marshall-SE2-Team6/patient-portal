from django import forms

from apps.scheduling.models import AppointmentRequest, PreCheckInRecord, Provider


class AppointmentRequestForm(forms.ModelForm):
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.none(),
        label="Provider",
    )
    scheduled_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    scheduled_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = AppointmentRequest
        fields = ["provider", "scheduled_start", "scheduled_end", "reason", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provider"].queryset = Provider.objects.filter(accepts_new_patients=True)

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("scheduled_start")
        end = cleaned_data.get("scheduled_end")

        if start and end and end <= start:
            raise forms.ValidationError("Appointment end time must be after the start time.")

        return cleaned_data

    def save(self, commit=True, *, patient=None):
        appointment_request = super().save(commit=False)
        appointment_request.patient = patient
        appointment_request.preferred_provider = self.cleaned_data["provider"]
        appointment_request.requested_start = self.cleaned_data["scheduled_start"]
        appointment_request.requested_end = self.cleaned_data["scheduled_end"]

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
