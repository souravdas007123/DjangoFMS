from django.contrib import admin
from .models import DeliveryOrder, DeliveryOrderItem


class DeliveryOrderItemInline(admin.TabularInline):
    model = DeliveryOrderItem
    extra = 1


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "sales_order", "vehicle_number", "driver_name", "dispatch_date", "delivery_date", "status")
    list_filter = ("status",)
    search_fields = ("number", "sales_order__number", "vehicle_number")
    inlines = [DeliveryOrderItemInline]
