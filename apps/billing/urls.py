from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("billing/", views.invoice_list, name="invoice_list"),
    path("billing/<int:invoice_id>/pay/", views.pay_invoice, name="pay_invoice"),
]
