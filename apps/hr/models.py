from django.db import models
from apps.masters.models import Employee, WorkCenter, TimeStampedModel


class Shift(TimeStampedModel):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.name


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        HALF_DAY = "HALF_DAY", "Half Day"
        LEAVE = "LEAVE", "Leave"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    shift = models.ForeignKey(Shift, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ("employee", "date")
        verbose_name_plural = "Attendance"

    def __str__(self):
        return f"{self.employee.code} - {self.date}"


class LabourAllocation(TimeStampedModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="allocations")
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name="labour_allocations")
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.employee.code} @ {self.work_center.code} on {self.date}"
