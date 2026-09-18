from django.contrib import admin
from .models import (
    ProductionPlan, ProductionPlanItem, ProductionOrder, JobCard,
    OperationEntry, ProductionEntry, ScrapEntry, ReworkEntry,
)


class ProductionPlanItemInline(admin.TabularInline):
    model = ProductionPlanItem
    extra = 1


@admin.register(ProductionPlan)
class ProductionPlanAdmin(admin.ModelAdmin):
    list_display = ("number", "planning_date", "period_start", "period_end", "status")
    list_filter = ("status",)
    search_fields = ("number",)
    inlines = [ProductionPlanItemInline]


class ProductionEntryInline(admin.TabularInline):
    model = ProductionEntry
    extra = 0


class ScrapEntryInline(admin.TabularInline):
    model = ScrapEntry
    extra = 0


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "quantity", "produced_quantity", "rejected_quantity",
                     "scrap_quantity", "status", "start_date", "end_date", "yield_percent")
    list_filter = ("status",)
    search_fields = ("number", "product__code")
    inlines = [ProductionEntryInline, ScrapEntryInline]
    date_hierarchy = "start_date"


class OperationEntryInline(admin.TabularInline):
    model = OperationEntry
    extra = 0


@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ("number", "production_order", "operation_name", "work_center", "machine",
                     "operator", "planned_quantity", "produced_quantity", "rejected_quantity", "status")
    list_filter = ("status", "work_center")
    search_fields = ("number", "production_order__number")
    inlines = [OperationEntryInline]


@admin.register(ScrapEntry)
class ScrapEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "production_order", "product", "quantity", "reason", "entry_date")
    search_fields = ("production_order__number", "product__code")


@admin.register(ReworkEntry)
class ReworkEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "production_order", "product", "quantity", "reason", "entry_date")
    search_fields = ("production_order__number", "product__code")
