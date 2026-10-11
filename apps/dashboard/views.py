from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from apps.masters.models import Product, Machine
from apps.sales.models import SalesOrder
from apps.purchase.models import PurchaseOrder
from apps.inventory.models import StockLedgerEntry
from apps.production.models import ProductionOrder
from apps.quality.models import NCR, Inspection

ZERO = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=3))


def _pct(part, whole):
    """Percentage rounded to 1 decimal; 0 when there is nothing produced yet."""
    return round(float(part) / float(whole) * 100, 1) if whole else 0


@login_required
def index(request):
    today = timezone.localdate()

    # ---- Production KPIs (all orders, same formula as ProductionOrder.yield_percent) ----
    totals = ProductionOrder.objects.aggregate(
        produced=Sum("produced_quantity"),
        rejected=Sum("rejected_quantity"),
        scrap=Sum("scrap_quantity"),
    )
    total_produced = totals["produced"] or 0
    total_rejected = totals["rejected"] or 0
    total_scrap = totals["scrap"] or 0

    good_qty = float(total_produced) - float(total_rejected) - float(total_scrap)
    yield_percent = _pct(good_qty, total_produced)
    rejection_percent = _pct(total_rejected, total_produced)
    scrap_percent = _pct(total_scrap, total_produced)

    # ---- Inventory KPIs (single query instead of 2 queries per product) ----
    low_stock_qs = (
        Product.objects.filter(is_active=True, reorder_level__gt=0)
        .select_related("unit")
        .annotate(
            stock_in=Coalesce(Sum("stock_entries__qty_in"), ZERO),
            stock_out=Coalesce(Sum("stock_entries__qty_out"), ZERO),
        )
        .annotate(balance=F("stock_in") - F("stock_out"))
        .filter(balance__lte=F("reorder_level"))
        .order_by("balance")
    )
    low_stock_count = low_stock_qs.count()
    low_stock_products = [{"product": p, "balance": p.balance} for p in low_stock_qs[:8]]

    # Net stock value = sum((in - out) * rate) over the ledger
    total_stock_value = StockLedgerEntry.objects.aggregate(
        t=Sum(
            ExpressionWrapper(
                (F("qty_in") - F("qty_out")) * F("rate"),
                output_field=DecimalField(max_digits=20, decimal_places=3),
            )
        )
    )["t"] or 0

    # ---- Purchase / Sales KPIs ----
    pending_po = PurchaseOrder.objects.filter(
        status__in=[PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.SENT, PurchaseOrder.Status.PARTIALLY_RECEIVED]
    ).count()
    open_sales_orders = SalesOrder.objects.filter(
        status__in=[SalesOrder.Status.CONFIRMED, SalesOrder.Status.IN_PRODUCTION, SalesOrder.Status.PARTIALLY_DELIVERED]
    ).count()

    # ---- Quality KPIs ----
    open_ncr = NCR.objects.filter(status__in=[NCR.Status.OPEN, NCR.Status.UNDER_REVIEW]).count()
    closed_ncr = NCR.objects.filter(status=NCR.Status.CLOSED).count()
    pending_inspections = Inspection.objects.filter(result=Inspection.Result.PENDING).count()

    # ---- Maintenance KPIs ----
    machines_total = Machine.objects.count()
    machines_breakdown = Machine.objects.filter(status=Machine.Status.BREAKDOWN).count()

    context = {
        "today": today,
        "total_produced": total_produced,
        "yield_percent": yield_percent,
        "rejection_percent": rejection_percent,
        "scrap_percent": scrap_percent,
        "low_stock_count": low_stock_count,
        "low_stock_products": low_stock_products,
        "total_stock_value": total_stock_value,
        "pending_po": pending_po,
        "open_sales_orders": open_sales_orders,
        "open_ncr": open_ncr,
        "closed_ncr": closed_ncr,
        "pending_inspections": pending_inspections,
        "machines_total": machines_total,
        "machines_breakdown": machines_breakdown,
        "recent_production_orders": ProductionOrder.objects.select_related("product").order_by("-created_at")[:6],
    }
    return render(request, "dashboard/index.html", context)
