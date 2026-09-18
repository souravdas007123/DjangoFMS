from django.contrib import admin
from .models import ProductCost


@admin.register(ProductCost)
class ProductCostAdmin(admin.ModelAdmin):
    list_display = ("product", "production_order", "material_cost", "labour_cost", "machine_cost",
                     "power_cost", "overhead_cost", "total_cost", "profit_per_unit", "calculated_on")
    search_fields = ("product__code",)
    date_hierarchy = "calculated_on"
