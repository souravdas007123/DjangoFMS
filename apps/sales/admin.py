from django.contrib import admin
from .models import Quotation, QuotationItem, SalesOrder, SalesOrderItem, Invoice


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "date", "status", "valid_till")
    list_filter = ("status",)
    search_fields = ("number", "customer__name")
    inlines = [QuotationItemInline]


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "order_date", "delivery_date", "status", "total_amount")
    list_filter = ("status",)
    search_fields = ("number", "customer__name")
    inlines = [SalesOrderItemInline]
    date_hierarchy = "order_date"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "sales_order", "invoice_date", "total_amount", "paid_amount", "status")
    list_filter = ("status",)
    search_fields = ("number", "sales_order__number")
