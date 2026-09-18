from django.db import models
from apps.masters.models import Product, TimeStampedModel
from apps.production.models import ProductionOrder


class ProductCost(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cost_records")
    production_order = models.ForeignKey(ProductionOrder, null=True, blank=True, on_delete=models.SET_NULL)
    material_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    labour_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    machine_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    power_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    calculated_on = models.DateField()

    @property
    def total_cost(self):
        return (self.material_cost + self.labour_cost + self.machine_cost
                + self.power_cost + self.overhead_cost)

    @property
    def profit_per_unit(self):
        return self.product.selling_price - self.total_cost

    def __str__(self):
        return f"Cost-{self.product.code}-{self.calculated_on}"
