from django.db import models
from apps.masters.models import Product, Customer, TimeStampedModel


class Quotation(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotations")
    date = models.DateField()
    valid_till = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    rate = models.DecimalField(max_digits=14, decimal_places=2)

    @property
    def amount(self):
        return self.quantity * self.rate

    def __str__(self):
        return f"{self.quotation.number} - {self.product.code}"


class SalesOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PRODUCTION = "IN_PRODUCTION", "In Production"
        PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED", "Partially Delivered"
        DELIVERED = "DELIVERED", "Delivered"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales_orders")
    quotation = models.ForeignKey(Quotation, null=True, blank=True, on_delete=models.SET_NULL)
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return self.number

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all())


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    rate = models.DecimalField(max_digits=14, decimal_places=2)
    delivered_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    @property
    def amount(self):
        return self.quantity * self.rate

    @property
    def pending_quantity(self):
        return self.quantity - self.delivered_quantity

    def __str__(self):
        return f"{self.sales_order.number} - {self.product.code}"


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partially Paid"
        PAID = "PAID", "Paid"

    number = models.CharField(max_length=30, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="invoices")
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)

    def __str__(self):
        return self.number
