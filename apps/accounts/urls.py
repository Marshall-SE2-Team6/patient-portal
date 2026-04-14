from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/patient/", views.patient_dashboard, name="patient_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
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