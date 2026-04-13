from django.urls import path
from . import views

urlpatterns = [
    path("appointments/request/", views.request_appointment, name="request_appointment"),
    path("appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),
]