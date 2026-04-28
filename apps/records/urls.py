from django.urls import path

from . import views

app_name = "records"

urlpatterns = [
    path("records/", views.my_records, name="my_records"),
    path("records/detail/", views.patient_record_detail, name="patient_record_detail"),
]
