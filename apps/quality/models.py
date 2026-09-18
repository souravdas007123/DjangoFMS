from django.db import models
from apps.masters.models import Product, TimeStampedModel


class InspectionPlan(TimeStampedModel):
    name = models.CharField(max_length=150)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inspection_plans")
    stage = models.CharField(max_length=20, choices=[
        ("INCOMING", "Incoming"), ("IN_PROCESS", "In-Process"), ("FINAL", "Final"),
    ])

    def __str__(self):
        return self.name


class InspectionParameter(models.Model):
    plan = models.ForeignKey(InspectionPlan, on_delete=models.CASCADE, related_name="parameters")
    parameter_name = models.CharField(max_length=100)
    specification = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.plan.name} - {self.parameter_name}"


class Inspection(TimeStampedModel):
    class Stage(models.TextChoices):
        INCOMING = "INCOMING", "Incoming QC"
        IN_PROCESS = "IN_PROCESS", "In-Process QC"
        FINAL = "FINAL", "Final QC"

    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"

    number = models.CharField(max_length=30, unique=True)
    stage = models.CharField(max_length=15, choices=Stage.choices)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="inspections")
    reference = models.CharField(max_length=100, blank=True, help_text="GRN/Job Card/Production Order number")
    inspected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    accepted_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rejected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING)
    inspection_date = models.DateField()
    inspector = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number


class InspectionResult(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="results")
    parameter_name = models.CharField(max_length=100)
    measured_value = models.CharField(max_length=100, blank=True)
    is_ok = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.inspection.number} - {self.parameter_name}"


class NCR(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        CLOSED = "CLOSED", "Closed"

    class ActionTaken(models.TextChoices):
        REWORK = "REWORK", "Rework"
        SCRAP = "SCRAP", "Scrap"
        RETURN_TO_SUPPLIER = "RETURN_TO_SUPPLIER", "Return to Supplier"
        USE_AS_IS = "USE_AS_IS", "Use As Is"

    number = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="ncrs")
    inspection = models.ForeignKey(Inspection, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    problem_description = models.TextField()
    root_cause = models.TextField(blank=True)
    action_taken = models.CharField(max_length=25, choices=ActionTaken.choices, null=True, blank=True)
    responsible_person = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    raised_date = models.DateField()

    class Meta:
        verbose_name = "NCR"
        verbose_name_plural = "NCRs"

    def __str__(self):
        return self.number


class CAPA(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        VERIFIED = "VERIFIED", "Verified"
        CLOSED = "CLOSED", "Closed"

    number = models.CharField(max_length=30, unique=True)
    ncr = models.ForeignKey(NCR, on_delete=models.CASCADE, related_name="capas")
    corrective_action = models.TextField()
    preventive_action = models.TextField(blank=True)
    responsible_person = models.CharField(max_length=100, blank=True)
    target_date = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    class Meta:
        verbose_name = "CAPA"
        verbose_name_plural = "CAPAs"

    def __str__(self):
        return self.number
