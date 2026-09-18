from django.contrib import admin
from .models import SparePart, MaintenanceSchedule, Breakdown, MaintenanceWorkOrder


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "stock_quantity", "reorder_level", "unit_cost")
    search_fields = ("code", "name")


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ("machine", "frequency", "last_service_date", "next_due_date")
    list_filter = ("frequency",)
    search_fields = ("machine__code",)


@admin.register(Breakdown)
class BreakdownAdmin(admin.ModelAdmin):
    list_display = ("number", "machine", "reported_at", "status", "engineer", "downtime_hours")
    list_filter = ("status",)
    search_fields = ("number", "machine__code")
    date_hierarchy = "reported_at"


@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "machine", "assigned_to", "scheduled_date", "completed_date", "status")
    list_filter = ("status",)
    search_fields = ("number", "machine__code")
    filter_horizontal = ("spare_parts_used",)
