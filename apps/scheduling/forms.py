from django import forms
from apps.scheduling.models import Appointment, Provider


class AppointmentRequestForm(forms.ModelForm):
    scheduled_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    scheduled_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )

    class Meta:
        model = Appointment
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