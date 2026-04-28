from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from apps.billing.models import Invoice
from apps.records.models import ClinicalNote, LabOrder, LabResult, Prescription, VitalsRecord

User = get_user_model()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    address = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "date_of_birth",
            "address",
            "password1",
            "password2",
        )


class ProfileForm(UserChangeForm):
    password = None
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    address_line_1 = forms.CharField(max_length=255, required=False)
    address_line_2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=50, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    emergency_contact_name = forms.CharField(max_length=255, required=False)
    emergency_contact_phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "emergency_contact_name",
            "emergency_contact_phone",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patient_profile = getattr(self.instance, "patient_profile", None)
        if patient_profile:
            self.fields["phone_number"].initial = patient_profile.phone_number
            self.fields["date_of_birth"].initial = patient_profile.date_of_birth
            self.fields["address_line_1"].initial = patient_profile.address_line_1
            self.fields["address_line_2"].initial = patient_profile.address_line_2
            self.fields["city"].initial = patient_profile.city
            self.fields["state"].initial = patient_profile.state
            self.fields["postal_code"].initial = patient_profile.postal_code
            self.fields["emergency_contact_name"].initial = patient_profile.emergency_contact_name
            self.fields["emergency_contact_phone"].initial = patient_profile.emergency_contact_phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        patient_profile = getattr(user, "patient_profile", None)
        if patient_profile:
            patient_profile.phone_number = self.cleaned_data.get("phone_number", "")
            patient_profile.date_of_birth = self.cleaned_data.get("date_of_birth")
            patient_profile.address_line_1 = self.cleaned_data.get("address_line_1", "")
            patient_profile.address_line_2 = self.cleaned_data.get("address_line_2", "")
            patient_profile.city = self.cleaned_data.get("city", "")
            patient_profile.state = self.cleaned_data.get("state", "")
            patient_profile.postal_code = self.cleaned_data.get("postal_code", "")
            patient_profile.emergency_contact_name = self.cleaned_data.get("emergency_contact_name", "")
            patient_profile.emergency_contact_phone = self.cleaned_data.get("emergency_contact_phone", "")
            patient_profile.save()
        return user


class AdminInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = (
            "patient",
            "appointment",
            "invoice_number",
            "status",
            "due_date",
            "subtotal",
            "tax_amount",
            "total_amount",
            "balance_due",
            "notes",
        )
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ClinicalNoteForm(forms.ModelForm):
    class Meta:
        model = ClinicalNote
        fields = ("title", "note_type", "content")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")


class LabOrderForm(forms.ModelForm):
    class Meta:
        model = LabOrder
        fields = ("test_name", "instructions", "status")
        widgets = {
            "instructions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")


class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ("result_summary", "result_value", "units", "reference_range", "status")
        widgets = {
            "result_summary": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")


class VitalsRecordForm(forms.ModelForm):
    class Meta:
        model = VitalsRecord
        fields = (
            "height_cm",
            "weight_kg",
            "temperature_c",
            "systolic_bp",
            "diastolic_bp",
            "pulse_bpm",
            "respiratory_rate",
            "oxygen_saturation",
            "notes",
        )
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "portal-form-input")
