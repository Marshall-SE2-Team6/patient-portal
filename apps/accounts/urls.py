from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/patient/", views.patient_dashboard, name="patient_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/front-desk/", views.receptionist_dashboard, name="receptionist_dashboard"),
    path("dashboard/doctor/", views.doctor_dashboard, name="doctor_dashboard"),
    path("dashboard/nurse/", views.nurse_dashboard, name="nurse_dashboard"),
    path("dashboard/appointment-requests/<int:request_id>/approve/", views.approve_appointment_request, name="approve_appointment_request"),
    path("dashboard/appointment-requests/<int:request_id>/reject/", views.reject_appointment_request, name="reject_appointment_request"),
    path("dashboard/doctor/appointments/", views.doctor_appointments, name="doctor_appointments"),
    path("dashboard/doctor/appointments/<int:appointment_id>/", views.doctor_appointment_detail, name="doctor_appointment_detail"),
    path("dashboard/doctor/records/", views.doctor_records, name="doctor_records"),
    path("dashboard/doctor/records/<int:patient_id>/", views.doctor_patient_record_detail, name="doctor_patient_record_detail"),
    path("dashboard/doctor/records/<int:patient_id>/prescriptions/<int:prescription_id>/edit/", views.doctor_edit_prescription, name="doctor_edit_prescription"),
    path("dashboard/doctor/records/<int:patient_id>/notes/<int:note_id>/edit/", views.doctor_edit_clinical_note, name="doctor_edit_clinical_note"),
    path("dashboard/nurse/records/", views.nurse_records, name="nurse_records"),
    path("dashboard/nurse/records/<int:patient_id>/", views.nurse_patient_record_detail, name="nurse_patient_record_detail"),
    path("dashboard/doctor/billing/", views.doctor_billing, name="doctor_billing"),
    path("profile/", views.profile, name="profile"),
    path("admin-portal/profile/", views.admin_profile, name="admin_profile"),
    path("admin-portal/billing/", views.admin_billing, name="admin_billing"),
    path("admin-portal/billing/create/", views.admin_create_invoice, name="admin_create_invoice"),
    path("admin-portal/billing/delete/<int:invoice_id>/", views.admin_delete_invoice, name="admin_delete_invoice"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("signup/", views.signup, name="signup"),

    path(
        "accounts/password_change/",
        views.PortalPasswordChangeView.as_view(),
        name="password_change",
    ),
]
