from django.contrib import admin
from .models import (
    UnitOfMeasure, ProductCategory, Product, Warehouse, Bin,
    Customer, Supplier, WorkCenter, Machine, BOM, BOMItem,
    Routing, RoutingOperation, Employee,
)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "product_type", "category", "unit", "standard_cost", "selling_price", "is_active")
    list_filter = ("product_type", "category", "batch_required", "qc_required", "is_active")
    search_fields = ("code", "name", "hsn_code")
    list_editable = ("selling_price",)
    fieldsets = (
        ("Basic Info", {"fields": ("code", "name", "product_type", "category", "unit", "image")}),
        ("Tax & Compliance", {"fields": ("hsn_code", "tax_percent")}),
        ("Flags", {"fields": ("batch_required", "serial_required", "qc_required", "is_active")}),
        ("Costing", {"fields": ("standard_cost", "selling_price", "reorder_level")}),
    )


class BinInline(admin.TabularInline):
    model = Bin
    extra = 1


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "location", "is_active")
    search_fields = ("code", "name")
    inlines = [BinInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "contact_person", "phone", "credit_limit", "is_active")
    search_fields = ("code", "name", "gst_number")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "contact_person", "phone", "rating", "is_active")
    search_fields = ("code", "name", "gst_number")


@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "capacity_per_shift", "efficiency_percent", "cost_per_hour")
    search_fields = ("code", "name")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "work_center", "status", "purchase_date")
    list_filter = ("status", "work_center")
    search_fields = ("code", "name", "serial_number")


class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "version", "output_quantity", "is_default", "effective_date")
    list_filter = ("is_default",)
    search_fields = ("product__code", "product__name")
    inlines = [BOMItemInline]


class RoutingOperationInline(admin.TabularInline):
    model = RoutingOperation
    extra = 1


@admin.register(Routing)
class RoutingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "bom")
    search_fields = ("product__code",)
    inlines = [RoutingOperationInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "designation", "department", "work_center", "is_active")
    list_filter = ("department", "work_center")
    search_fields = ("code", "name")
