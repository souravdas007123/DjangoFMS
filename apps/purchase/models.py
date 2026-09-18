from django.db import models
from apps.masters.models import Product, Supplier, Warehouse, TimeStampedModel


class PurchaseRequisition(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CLOSED = "CLOSED", "Closed"

    number = models.CharField(max_length=30, unique=True)
    date = models.DateField()
    required_by = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number


class PurchaseRequisitionItem(models.Model):
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f"{self.requisition.number} - {self.product.code}"


class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        SENT = "SENT", "Sent to Supplier"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
        RECEIVED = "RECEIVED", "Received"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    requisition = models.ForeignKey(PurchaseRequisition, null=True, blank=True, on_delete=models.SET_NULL)
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all())


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    rate = models.DecimalField(max_digits=14, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    @property
    def amount(self):
        return self.quantity * self.rate

    @property
    def pending_quantity(self):
        return self.quantity - self.received_quantity

    def __str__(self):
        return f"{self.purchase_order.number} - {self.product.code}"


class GRN(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING_QC = "PENDING_QC", "Pending QC"
        ACCEPTED = "ACCEPTED", "Accepted"
        PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED", "Partially Accepted"
        REJECTED = "REJECTED", "Rejected"

    number = models.CharField(max_length=30, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="grns")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    received_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_QC)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "GRN"
        verbose_name_plural = "GRNs"

    def __str__(self):
        return self.number


class GRNItem(models.Model):
    grn = models.ForeignKey(GRN, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    received_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    accepted_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rejected_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    batch_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.grn.number} - {self.product.code}"


class SupplierPayment(TimeStampedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="payments")
    purchase_order = models.ForeignKey(PurchaseOrder, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment-{self.id} - {self.supplier.name}"
