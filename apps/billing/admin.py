from django.contrib import admin

from .models import Invoice, InvoiceLineItem, Payment, PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "method_type", "nickname", "last4", "is_default", "is_active")
    list_filter = ("method_type", "is_default", "is_active")
    search_fields = ("patient__user__username", "patient__user__email", "nickname", "last4")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice_number",
        "patient",
        "appointment",
        "status",
        "total_amount",
        "balance_due",
        "due_date",
    )
    list_filter = ("status",)
    search_fields = (
        "invoice_number",
        "patient__user__username",
        "patient__user__email",
    )


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "description", "quantity", "unit_price", "line_total")
    search_fields = ("invoice__invoice_number", "description")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "payment_method", "amount", "status", "payment_date")
    list_filter = ("status",)
    search_fields = ("invoice__invoice_number", "transaction_reference")
