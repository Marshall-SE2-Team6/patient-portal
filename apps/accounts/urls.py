from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("signup/", views.signup, name="signup"),

    path(
        "accounts/password_change/",
        views.PortalPasswordChangeView.as_view(),
        name="password_change",
    ),
]