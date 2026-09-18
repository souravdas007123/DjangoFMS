from django.db import models
from apps.masters.models import Product, TimeStampedModel
from apps.sales.models import SalesOrder


class DeliveryOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PICKED = "PICKED", "Picked"
        PACKED = "PACKED", "Packed"
        DISPATCHED = "DISPATCHED", "Dispatched"
        DELIVERED = "DELIVERED", "Delivered"

    number = models.CharField(max_length=30, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="delivery_orders")
    vehicle_number = models.CharField(max_length=30, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    dispatch_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)

    def __str__(self):
        return self.number


class DeliveryOrderItem(models.Model):
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)

    def __str__(self):
        return f"{self.delivery_order.number} - {self.product.code}"
