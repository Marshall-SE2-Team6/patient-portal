from django.urls import path
from . import views

urlpatterns = [
    path("appointments/request/", views.request_appointment, name="request_appointment"),
    path("appointments/staff/", views.staff_appointments, name="staff_appointments"),
    path("appointments/staff/schedule/", views.staff_schedule_appointment, name="staff_schedule_appointment"),
    path("appointments/<int:appointment_id>/pre-check-in/", views.pre_check_in, name="pre_check_in"),
    path("appointments/<int:appointment_id>/reschedule/", views.reschedule_appointment, name="reschedule_appointment"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="cancel_appointment"),
    path("appointments/<int:appointment_id>/check-in/", views.check_in_appointment, name="check_in_appointment"),
    path("appointments/<int:appointment_id>/complete/", views.complete_appointment, name="complete_appointment"),
    path("appointments/<int:appointment_id>/no-show/", views.mark_no_show_appointment, name="mark_no_show_appointment"),
    path("appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),
    path('appointments/', views.my_appointments, name='my_appointments'),
]
