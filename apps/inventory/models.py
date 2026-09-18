from django.db import models
from apps.masters.models import Product, Warehouse, Bin, TimeStampedModel


class Batch(TimeStampedModel):
    batch_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.batch_number


class SerialNumber(TimeStampedModel):
    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In Stock"
        ISSUED = "ISSUED", "Issued"
        SOLD = "SOLD", "Sold"

    serial = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="serials")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.IN_STOCK)

    def __str__(self):
        return self.serial


class StockLedgerEntry(TimeStampedModel):
    class TransactionType(models.TextChoices):
        PURCHASE_RECEIPT = "PURCHASE_RECEIPT", "Purchase Receipt"
        MATERIAL_ISSUE = "MATERIAL_ISSUE", "Material Issue"
        MATERIAL_RETURN = "MATERIAL_RETURN", "Material Return"
        STOCK_TRANSFER = "STOCK_TRANSFER", "Stock Transfer"
        PRODUCTION_RECEIPT = "PRODUCTION_RECEIPT", "Production Receipt"
        SALES_DISPATCH = "SALES_DISPATCH", "Sales Dispatch"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        SCRAP = "SCRAP", "Scrap"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_entries")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_entries")
    bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    reference = models.CharField(max_length=100, blank=True, help_text="e.g. GRN-0001, MO-0002")
    qty_in = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    qty_out = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    transaction_date = models.DateTimeField()

    class Meta:
        ordering = ["-transaction_date"]
        verbose_name = "Stock Ledger Entry"
        verbose_name_plural = "Stock Ledger"

    @property
    def value(self):
        return (self.qty_in - self.qty_out) * self.rate

    def __str__(self):
        return f"{self.product.code} | {self.transaction_type} | {self.reference}"


class StockTransfer(TimeStampedModel):
    number = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="transfers_out")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="transfers_in")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    transfer_date = models.DateField()

    def __str__(self):
        return self.number


class MaterialIssue(TimeStampedModel):
    number = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    issued_against = models.CharField(max_length=100, blank=True, help_text="Production Order Number")
    issue_date = models.DateField()

    def __str__(self):
        return self.number


class MaterialReturn(TimeStampedModel):
    number = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    returned_against = models.CharField(max_length=100, blank=True)
    return_date = models.DateField()

    def __str__(self):
        return self.number


class StockAdjustment(TimeStampedModel):
    class ReasonType(models.TextChoices):
        DAMAGE = "DAMAGE", "Damage"
        COUNT_MISMATCH = "COUNT_MISMATCH", "Physical Count Mismatch"
        EXPIRY = "EXPIRY", "Expiry"
        OTHER = "OTHER", "Other"

    number = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, help_text="Positive to add, negative to reduce")
    reason = models.CharField(max_length=20, choices=ReasonType.choices, default=ReasonType.OTHER)
    adjustment_date = models.DateField()
    approved_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.number
