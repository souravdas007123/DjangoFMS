from django.contrib import admin
from .models import (
    Batch, SerialNumber, StockLedgerEntry, StockTransfer,
    MaterialIssue, MaterialReturn, StockAdjustment,
)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "product", "manufacture_date", "expiry_date")
    search_fields = ("batch_number", "product__code")


@admin.register(SerialNumber)
class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ("serial", "product", "status")
    list_filter = ("status",)
    search_fields = ("serial", "product__code")


@admin.register(StockLedgerEntry)
class StockLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "transaction_type", "reference", "qty_in", "qty_out", "rate", "transaction_date")
    list_filter = ("transaction_type", "warehouse")
    search_fields = ("product__code", "reference")
    date_hierarchy = "transaction_date"


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "from_warehouse", "to_warehouse", "quantity", "transfer_date")
    search_fields = ("number", "product__code")


@admin.register(MaterialIssue)
class MaterialIssueAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "warehouse", "quantity", "issued_against", "issue_date")
    search_fields = ("number", "product__code", "issued_against")


@admin.register(MaterialReturn)
class MaterialReturnAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "warehouse", "quantity", "returned_against", "return_date")
    search_fields = ("number", "product__code")


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "warehouse", "quantity", "reason", "adjustment_date")
    list_filter = ("reason",)
    search_fields = ("number", "product__code")
