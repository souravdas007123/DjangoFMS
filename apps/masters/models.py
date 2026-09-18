from django.db import models
from django.core.validators import MinValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class UnitOfMeasure(TimeStampedModel):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        return self.code


class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    class Meta:
        verbose_name_plural = "Product Categories"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    class ProductType(models.TextChoices):
        RAW_MATERIAL = "RM", "Raw Material"
        SEMI_FINISHED = "SFG", "Semi Finished"
        FINISHED = "FG", "Finished Goods"
        CONSUMABLE = "CONS", "Consumable"

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=4, choices=ProductType.choices, default=ProductType.FINISHED)
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    hsn_code = models.CharField(max_length=20, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    batch_required = models.BooleanField(default=False)
    serial_required = models.BooleanField(default=False)
    qc_required = models.BooleanField(default=False)
    reorder_level = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    standard_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class Bin(TimeStampedModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="bins")
    code = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("warehouse", "code")

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"


class Customer(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)

    def __str__(self):
        return self.name


class WorkCenter(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    capacity_per_shift = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    efficiency_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Machine(TimeStampedModel):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        IDLE = "IDLE", "Idle"
        BREAKDOWN = "BREAKDOWN", "Breakdown"
        MAINTENANCE = "MAINTENANCE", "Under Maintenance"
        RETIRED = "RETIRED", "Retired"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    machine_type = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    model_no = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name="machines")
    purchase_date = models.DateField(null=True, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    capacity = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.RUNNING)

    def __str__(self):
        return f"{self.code} - {self.name}"


class BOM(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="boms")
    version = models.CharField(max_length=20, default="v1")
    output_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=1)
    is_default = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "BOM"
        verbose_name_plural = "BOMs"
        unique_together = ("product", "version")

    def __str__(self):
        return f"BOM-{self.product.code}-{self.version}"


class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="items")
    component = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_boms")
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(0)])
    scrap_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.bom} - {self.component.code} x {self.quantity}"


class Routing(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="routings")
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True, related_name="routings")
    name = models.CharField(max_length=100, default="Default Routing")

    def __str__(self):
        return f"Routing-{self.product.code}"


class RoutingOperation(models.Model):
    routing = models.ForeignKey(Routing, on_delete=models.CASCADE, related_name="operations")
    sequence = models.PositiveIntegerField(default=10)
    operation_name = models.CharField(max_length=100)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT)
    setup_time_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    run_time_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_required = models.PositiveIntegerField(default=1)
    qc_required = models.BooleanField(default=False)

    class Meta:
        ordering = ["sequence"]

    def __str__(self):
        return f"Op{self.sequence:02d} {self.operation_name} ({self.routing.product.code})"


class Employee(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
