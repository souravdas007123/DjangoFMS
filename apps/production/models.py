from django.db import models
from apps.masters.models import Product, BOM, Routing, WorkCenter, Machine, Employee, TimeStampedModel


class ProductionPlan(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        SCHEDULED = "SCHEDULED", "Scheduled"
        RELEASED = "RELEASED", "Released"
        COMPLETED = "COMPLETED", "Completed"

    number = models.CharField(max_length=30, unique=True)
    planning_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number


class ProductionPlanItem(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    required_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    available_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    planned_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.plan.number} - {self.product.code}"


class ProductionOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PLANNED = "PLANNED", "Planned"
        APPROVED = "APPROVED", "Approved"
        RELEASED = "RELEASED", "Released"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    number = models.CharField(max_length=30, unique=True)
    plan = models.ForeignKey(ProductionPlan, null=True, blank=True, on_delete=models.SET_NULL, related_name="production_orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="production_orders")
    bom = models.ForeignKey(BOM, on_delete=models.PROTECT)
    routing = models.ForeignKey(Routing, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    produced_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rejected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    scrap_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number

    @property
    def yield_percent(self):
        if self.quantity:
            good = self.produced_quantity - self.rejected_quantity - self.scrap_quantity
            return round((good / self.quantity) * 100, 2)
        return 0


class JobCard(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    number = models.CharField(max_length=30, unique=True)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name="job_cards")
    operation_name = models.CharField(max_length=100)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, null=True, blank=True, on_delete=models.SET_NULL)
    operator = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    planned_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    produced_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rejected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rework_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.number


class OperationEntry(TimeStampedModel):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name="operation_entries")
    started_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    completed_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rejected_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rework_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    scrap_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    downtime_minutes = models.PositiveIntegerField(default=0)
    remarks = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"OpEntry-{self.id} ({self.job_card.number})"


class ProductionEntry(TimeStampedModel):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name="production_entries")
    entry_date = models.DateField()
    produced_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    rejected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    remarks = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Entry-{self.id} ({self.production_order.number})"


class ScrapEntry(TimeStampedModel):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name="scrap_entries")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    reason = models.CharField(max_length=200, blank=True)
    entry_date = models.DateField()

    def __str__(self):
        return f"Scrap-{self.id} ({self.production_order.number})"


class ReworkEntry(TimeStampedModel):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name="rework_entries")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    reason = models.CharField(max_length=200, blank=True)
    entry_date = models.DateField()

    def __str__(self):
        return f"Rework-{self.id} ({self.production_order.number})"
