from django.urls import path

from . import views

app_name = "records"

urlpatterns = [
    path("records/", views.my_records, name="my_records"),
]
