import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.masters.models import (
    UnitOfMeasure, ProductCategory, Product, Warehouse, Customer, Supplier,
    WorkCenter, Machine, BOM, BOMItem, Routing, RoutingOperation, Employee,
)
from apps.sales.models import SalesOrder, SalesOrderItem
from apps.purchase.models import PurchaseOrder, PurchaseOrderItem, GRN, GRNItem
from apps.inventory.models import StockLedgerEntry
from apps.production.models import ProductionPlan, ProductionPlanItem, ProductionOrder, JobCard
from apps.quality.models import Inspection, NCR
from apps.maintenance.models import MaintenanceSchedule, Breakdown


class Command(BaseCommand):
    help = "Seed the FMS database with realistic demo data (Steel Chair factory example)."

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write("Seeding FactoryOS demo data...")

        kg, _ = UnitOfMeasure.objects.get_or_create(code="KG", name="Kilogram")
        pcs, _ = UnitOfMeasure.objects.get_or_create(code="PCS", name="Pieces")

        cat_rm, _ = ProductCategory.objects.get_or_create(name="Raw Material")
        cat_fg, _ = ProductCategory.objects.get_or_create(name="Finished Goods")

        pipe, _ = Product.objects.get_or_create(code="RM-PIPE", defaults=dict(
            name="Steel Pipe", product_type="RM", category=cat_rm, unit=kg,
            standard_cost=60, selling_price=0, reorder_level=500))
        sheet, _ = Product.objects.get_or_create(code="RM-SHEET", defaults=dict(
            name="Steel Sheet", product_type="RM", category=cat_rm, unit=kg,
            standard_cost=55, selling_price=0, reorder_level=300))
        rod, _ = Product.objects.get_or_create(code="RM-ROD", defaults=dict(
            name="Welding Rod", product_type="RM", category=cat_rm, unit=kg,
            standard_cost=120, selling_price=0, reorder_level=50))
        paint, _ = Product.objects.get_or_create(code="RM-PAINT", defaults=dict(
            name="Paint", product_type="RM", category=cat_rm, unit=kg,
            standard_cost=200, selling_price=0, reorder_level=20))
        chair, _ = Product.objects.get_or_create(code="FG-CHAIR", defaults=dict(
            name="Steel Chair", product_type="FG", category=cat_fg, unit=pcs, qc_required=True,
            standard_cost=650, selling_price=899, reorder_level=50))

        wh_rm, _ = Warehouse.objects.get_or_create(code="WH-RM", name="Raw Material Store")
        wh_fg, _ = Warehouse.objects.get_or_create(code="WH-FG", name="Finished Goods Store")

        cust, _ = Customer.objects.get_or_create(code="CUST-001", defaults=dict(
            name="ABC Industries", contact_person="Rahul Sharma", phone="9876500001",
            email="rahul@abcind.com", credit_limit=500000))
        supp, _ = Supplier.objects.get_or_create(code="SUP-001", defaults=dict(
            name="Bharat Steel Suppliers", contact_person="Vikram Singh", phone="9876500002",
            email="sales@bharatsteel.com"))

        wc_cut, _ = WorkCenter.objects.get_or_create(code="WC-01", defaults=dict(name="Cutting", capacity_per_shift=800, cost_per_hour=150))
        wc_bend, _ = WorkCenter.objects.get_or_create(code="WC-02", defaults=dict(name="Bending", capacity_per_shift=700, cost_per_hour=140))
        wc_weld, _ = WorkCenter.objects.get_or_create(code="WC-03", defaults=dict(name="Welding", capacity_per_shift=600, cost_per_hour=180))
        wc_paint, _ = WorkCenter.objects.get_or_create(code="WC-04", defaults=dict(name="Painting", capacity_per_shift=650, cost_per_hour=130))
        wc_assy, _ = WorkCenter.objects.get_or_create(code="WC-05", defaults=dict(name="Assembly", capacity_per_shift=600, cost_per_hour=120))

        m1, _ = Machine.objects.get_or_create(code="MC-CUT-01", defaults=dict(name="Laser Cutter", work_center=wc_cut, status="RUNNING"))
        m2, _ = Machine.objects.get_or_create(code="MC-WELD-01", defaults=dict(name="MIG Welder", work_center=wc_weld, status="RUNNING"))
        m3, _ = Machine.objects.get_or_create(code="MC-PAINT-01", defaults=dict(name="Paint Booth", work_center=wc_paint, status="BREAKDOWN"))

        emp1, _ = Employee.objects.get_or_create(code="EMP-101", defaults=dict(name="Suresh Kumar", designation="Welder", department="Production", work_center=wc_weld))
        emp2, _ = Employee.objects.get_or_create(code="EMP-102", defaults=dict(name="Anita Devi", designation="QC Inspector", department="Quality"))

        bom, _ = BOM.objects.get_or_create(product=chair, version="v1", defaults=dict(output_quantity=1, effective_date=today))
        for comp, qty in [(pipe, 4), (sheet, 2), (rod, 0.1), (paint, 0.2)]:
            BOMItem.objects.get_or_create(bom=bom, component=comp, defaults=dict(quantity=qty))

        routing, _ = Routing.objects.get_or_create(product=chair, bom=bom, defaults=dict(name="Chair Routing"))
        ops = [
            (10, "Cutting", wc_cut), (20, "Bending", wc_bend), (30, "Welding", wc_weld),
            (40, "Painting", wc_paint), (50, "Assembly", wc_assy),
        ]
        for seq, name, wc in ops:
            RoutingOperation.objects.get_or_create(routing=routing, sequence=seq, defaults=dict(
                operation_name=name, work_center=wc, setup_time_min=15, run_time_min=5))

        # ---- Opening stock ----
        for prod, wh, qty, rate in [
            (pipe, wh_rm, 2500, 60), (sheet, wh_rm, 1500, 55), (rod, wh_rm, 150, 120), (paint, wh_rm, 60, 200),
        ]:
            StockLedgerEntry.objects.get_or_create(
                product=prod, warehouse=wh, transaction_type="ADJUSTMENT", reference="OPENING-STOCK",
                defaults=dict(qty_in=qty, rate=rate, transaction_date=timezone.now() - datetime.timedelta(days=10)))

        # ---- Sales Order ----
        so, created = SalesOrder.objects.get_or_create(number="SO-00001", defaults=dict(
            customer=cust, order_date=today - datetime.timedelta(days=5),
            delivery_date=today + datetime.timedelta(days=10), status="IN_PRODUCTION"))
        if created:
            SalesOrderItem.objects.create(sales_order=so, product=chair, quantity=500, rate=899, delivered_quantity=0)

        # ---- Purchase Order + GRN ----
        po, created = PurchaseOrder.objects.get_or_create(number="PO-00001", defaults=dict(
            supplier=supp, order_date=today - datetime.timedelta(days=8),
            expected_date=today - datetime.timedelta(days=2), status="RECEIVED"))
        if created:
            PurchaseOrderItem.objects.create(purchase_order=po, product=pipe, quantity=1000, rate=60, received_quantity=1000)

        grn, created = GRN.objects.get_or_create(number="GRN-00001", defaults=dict(
            purchase_order=po, warehouse=wh_rm, received_date=today - datetime.timedelta(days=2), status="PARTIALLY_ACCEPTED"))
        if created:
            GRNItem.objects.create(grn=grn, product=pipe, received_quantity=1000, accepted_quantity=970, rejected_quantity=30)
            StockLedgerEntry.objects.create(product=pipe, warehouse=wh_rm, transaction_type="PURCHASE_RECEIPT",
                                             reference=grn.number, qty_in=970, rate=60, transaction_date=timezone.now())

        # ---- Production Plan + Order ----
        plan, created = ProductionPlan.objects.get_or_create(number="PP-00001", defaults=dict(
            planning_date=today - datetime.timedelta(days=4), status="RELEASED"))
        if created:
            ProductionPlanItem.objects.create(plan=plan, product=chair, required_quantity=500,
                                               available_stock=0, planned_quantity=500, priority="HIGH",
                                               start_date=today - datetime.timedelta(days=3), end_date=today + datetime.timedelta(days=5))

        mo, created = ProductionOrder.objects.get_or_create(number="MO-00045", defaults=dict(
            plan=plan, product=chair, bom=bom, routing=routing, quantity=500, produced_quantity=420,
            rejected_quantity=15, scrap_quantity=10, start_date=today - datetime.timedelta(days=3), status="IN_PROGRESS"))

        JobCard.objects.get_or_create(number="JC-00045", defaults=dict(
            production_order=mo, operation_name="Welding", work_center=wc_weld, machine=m2, operator=emp1,
            planned_quantity=500, produced_quantity=420, rejected_quantity=15, rework_quantity=10, status="IN_PROGRESS"))

        # ---- Quality ----
        insp, created = Inspection.objects.get_or_create(number="QC-00001", defaults=dict(
            stage="FINAL", product=chair, reference=mo.number, inspected_quantity=420,
            accepted_quantity=405, rejected_quantity=15, result="PASSED",
            inspection_date=today, inspector="Anita Devi"))

        NCR.objects.get_or_create(number="NCR-00021", defaults=dict(
            product=chair, inspection=insp, quantity=15, problem_description="Welding crack near joint",
            root_cause="Incorrect welding current parameter", action_taken="REWORK",
            responsible_person="Production Supervisor", status="OPEN", raised_date=today))

        # ---- Maintenance ----
        MaintenanceSchedule.objects.get_or_create(machine=m3, frequency="MONTHLY", defaults=dict(
            last_service_date=today - datetime.timedelta(days=40), next_due_date=today - datetime.timedelta(days=2)))

        Breakdown.objects.get_or_create(number="BD-00001", defaults=dict(
            machine=m3, reported_by="Shift Supervisor", reported_at=timezone.now() - datetime.timedelta(hours=6),
            diagnosis="Spray gun clogged", status="UNDER_REPAIR"))

        self.stdout.write(self.style.SUCCESS(
            "Demo data seeded! Visit / to see the dashboard, or /admin/ for full CRUD."))
