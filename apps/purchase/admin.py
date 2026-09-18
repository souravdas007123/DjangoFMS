from django.contrib import admin
from .models import (
    PurchaseRequisition, PurchaseRequisitionItem, PurchaseOrder, PurchaseOrderItem,
    GRN, GRNItem, SupplierPayment,
)


class PRItemInline(admin.TabularInline):
    model = PurchaseRequisitionItem
    extra = 1


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ("number", "date", "required_by", "status")
    list_filter = ("status",)
    search_fields = ("number",)
    inlines = [PRItemInline]


class POItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "supplier", "order_date", "expected_date", "status", "total_amount")
    list_filter = ("status", "supplier")
    search_fields = ("number", "supplier__name")
    inlines = [POItemInline]
    date_hierarchy = "order_date"


class GRNItemInline(admin.TabularInline):
    model = GRNItem
    extra = 1


@admin.register(GRN)
class GRNAdmin(admin.ModelAdmin):
    list_display = ("number", "purchase_order", "warehouse", "received_date", "status")
    list_filter = ("status", "warehouse")
    search_fields = ("number", "purchase_order__number")
    inlines = [GRNItemInline]


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "purchase_order", "amount", "payment_date")
    search_fields = ("supplier__name", "reference")
