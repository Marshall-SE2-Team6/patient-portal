from django.urls import path
from . import views

urlpatterns = [
    path("appointments/request/", views.request_appointment, name="request_appointment"),
    path("appointments/<int:appointment_id>/pre-check-in/", views.pre_check_in, name="pre_check_in"),
    path("appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),
    path('appointments/', views.my_appointments, name='my_appointments'),
]
