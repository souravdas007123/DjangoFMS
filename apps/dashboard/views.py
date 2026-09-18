from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.shortcuts import render
from django.utils import timezone

from apps.masters.models import Product, Machine
from apps.sales.models import SalesOrder
from apps.purchase.models import PurchaseOrder, PurchaseRequisition, GRN
from apps.inventory.models import StockLedgerEntry
from apps.production.models import ProductionOrder
from apps.quality.models import NCR, Inspection
from apps.maintenance.models import Breakdown, MaintenanceSchedule


@login_required
def index(request):
    today = timezone.localdate()

    # ---- Production KPIs ----
    prod_orders_active = ProductionOrder.objects.filter(
        status__in=[ProductionOrder.Status.RELEASED, ProductionOrder.Status.IN_PROGRESS]
    )
    total_planned = prod_orders_active.aggregate(t=Sum("quantity"))["t"] or 0
    total_produced = ProductionOrder.objects.aggregate(t=Sum("produced_quantity"))["t"] or 0
    total_rejected = ProductionOrder.objects.aggregate(t=Sum("rejected_quantity"))["t"] or 0
    total_scrap = ProductionOrder.objects.aggregate(t=Sum("scrap_quantity"))["t"] or 0

    good_qty = float(total_produced) - float(total_rejected) - float(total_scrap)
    yield_percent = round((good_qty / float(total_produced)) * 100, 1) if total_produced else 0
    rejection_percent = round((float(total_rejected) / float(total_produced)) * 100, 1) if total_produced else 0
    scrap_percent = round((float(total_scrap) / float(total_produced)) * 100, 1) if total_produced else 0

    # ---- Inventory KPIs ----
    low_stock_products = []
    for p in Product.objects.filter(is_active=True):
        stock_in = StockLedgerEntry.objects.filter(product=p).aggregate(t=Sum("qty_in"))["t"] or 0
        stock_out = StockLedgerEntry.objects.filter(product=p).aggregate(t=Sum("qty_out"))["t"] or 0
        balance = float(stock_in) - float(stock_out)
        if p.reorder_level and balance <= float(p.reorder_level):
            low_stock_products.append({"product": p, "balance": balance})
    low_stock_count = len(low_stock_products)

    total_stock_value = StockLedgerEntry.objects.aggregate(
        t=Sum(F("qty_in") * F("rate")) 
    )["t"] or 0

    # ---- Purchase KPIs ----
    pending_pr = PurchaseRequisition.objects.filter(
        status__in=[PurchaseRequisition.Status.DRAFT, PurchaseRequisition.Status.SUBMITTED]
    ).count()
    pending_po = PurchaseOrder.objects.filter(
        status__in=[PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.SENT, PurchaseOrder.Status.PARTIALLY_RECEIVED]
    ).count()
    pending_grn_qc = GRN.objects.filter(status=GRN.Status.PENDING_QC).count()

    # ---- Sales KPIs ----
    total_sales_orders = SalesOrder.objects.count()
    open_sales_orders = SalesOrder.objects.filter(
        status__in=[SalesOrder.Status.CONFIRMED, SalesOrder.Status.IN_PRODUCTION, SalesOrder.Status.PARTIALLY_DELIVERED]
    ).count()

    # ---- Quality KPIs ----
    open_ncr = NCR.objects.filter(status__in=[NCR.Status.OPEN, NCR.Status.UNDER_REVIEW]).count()
    closed_ncr = NCR.objects.filter(status=NCR.Status.CLOSED).count()
    pending_inspections = Inspection.objects.filter(result=Inspection.Result.PENDING).count()

    # ---- Maintenance KPIs ----
    machines_total = Machine.objects.count()
    machines_running = Machine.objects.filter(status=Machine.Status.RUNNING).count()
    machines_breakdown = Machine.objects.filter(status=Machine.Status.BREAKDOWN).count()
    open_breakdowns = Breakdown.objects.exclude(status=Breakdown.Status.CLOSED).count()
    pm_due = MaintenanceSchedule.objects.filter(next_due_date__lte=today).count()

    context = {
        "today": today,
        "total_planned": total_planned,
        "total_produced": total_produced,
        "yield_percent": yield_percent,
        "rejection_percent": rejection_percent,
        "scrap_percent": scrap_percent,
        "low_stock_count": low_stock_count,
        "low_stock_products": low_stock_products[:8],
        "total_stock_value": total_stock_value,
        "pending_pr": pending_pr,
        "pending_po": pending_po,
        "pending_grn_qc": pending_grn_qc,
        "total_sales_orders": total_sales_orders,
        "open_sales_orders": open_sales_orders,
        "open_ncr": open_ncr,
        "closed_ncr": closed_ncr,
        "pending_inspections": pending_inspections,
        "machines_total": machines_total,
        "machines_running": machines_running,
        "machines_breakdown": machines_breakdown,
        "open_breakdowns": open_breakdowns,
        "pm_due": pm_due,
        "recent_production_orders": ProductionOrder.objects.order_by("-created_at")[:6],
        "recent_sales_orders": SalesOrder.objects.order_by("-created_at")[:6],
    }
    return render(request, "dashboard/index.html", context)
