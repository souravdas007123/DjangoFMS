from django.db import models
from apps.masters.models import Machine, Employee, TimeStampedModel


class SparePart(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    stock_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_level = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.code} - {self.name}"


class MaintenanceSchedule(TimeStampedModel):
    class Frequency(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        YEARLY = "YEARLY", "Yearly"

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="maintenance_schedules")
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY)
    last_service_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    checklist = models.TextField(blank=True)

    def __str__(self):
        return f"PM-{self.machine.code}-{self.frequency}"


class Breakdown(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DIAGNOSED = "DIAGNOSED", "Diagnosed"
        UNDER_REPAIR = "UNDER_REPAIR", "Under Repair"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    number = models.CharField(max_length=30, unique=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="breakdowns")
    reported_by = models.CharField(max_length=100, blank=True)
    reported_at = models.DateTimeField()
    diagnosis = models.TextField(blank=True)
    engineer = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.number

    @property
    def downtime_hours(self):
        if self.resolved_at and self.reported_at:
            return round((self.resolved_at - self.reported_at).total_seconds() / 3600, 2)
        return None


class MaintenanceWorkOrder(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    number = models.CharField(max_length=30, unique=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="work_orders")
    breakdown = models.ForeignKey(Breakdown, null=True, blank=True, on_delete=models.SET_NULL, related_name="work_orders")
    schedule = models.ForeignKey(MaintenanceSchedule, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    spare_parts_used = models.ManyToManyField(SparePart, blank=True, related_name="work_orders")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.number
