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

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


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
