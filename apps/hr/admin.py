from django.contrib import admin
from .models import Shift, Attendance, LabourAllocation


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "shift", "status", "overtime_hours")
    list_filter = ("status", "shift")
    search_fields = ("employee__code", "employee__name")
    date_hierarchy = "date"


@admin.register(LabourAllocation)
class LabourAllocationAdmin(admin.ModelAdmin):
    list_display = ("employee", "work_center", "date", "hours_worked")
    search_fields = ("employee__code", "work_center__code")
