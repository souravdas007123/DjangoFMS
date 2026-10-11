from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.inventory.models import StockLedgerEntry
from apps.masters.models import BOM, Product, UnitOfMeasure, Warehouse
from apps.production.models import ProductionOrder

User = get_user_model()


class AuthRoutingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pass-12345-xyz")

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(resp, f"{reverse('login')}?next=/", fetch_redirect_response=False)

    def test_login_page_renders(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "registration/login.html")

    def test_login_then_dashboard(self):
        resp = self.client.post(reverse("login"), {"username": "tester", "password": "pass-12345-xyz"})
        self.assertRedirects(resp, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_logout_is_post_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        resp = self.client.post(reverse("logout"))
        self.assertRedirects(resp, "/accounts/login/", fetch_redirect_response=False)

    def test_dashboard_has_logout_form(self):
        self.client.force_login(self.user)
        html = self.client.get("/").content.decode()
        self.assertIn(f'action="{reverse("logout")}"', html)


class DashboardKpiTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("tester", password="pass-12345-xyz"))
        self.unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
        self.wh = Warehouse.objects.create(code="WH-1", name="Main")

    def _product(self, code, reorder_level):
        return Product.objects.create(code=code, name=code, unit=self.unit, reorder_level=reorder_level)

    def _ledger(self, product, qty_in=0, qty_out=0, rate=10):
        return StockLedgerEntry.objects.create(
            product=product, warehouse=self.wh, transaction_type="ADJUSTMENT",
            qty_in=qty_in, qty_out=qty_out, rate=rate, transaction_date=timezone.now(),
        )

    def test_empty_database_renders(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["yield_percent"], 0)
        self.assertEqual(resp.context["low_stock_count"], 0)

    def test_yield_is_same_on_dashboard_and_model(self):
        fg = self._product("FG-1", 0)
        bom = BOM.objects.create(product=fg, version="v1")
        order = ProductionOrder.objects.create(
            number="MO-1", product=fg, bom=bom, quantity=500, produced_quantity=420,
            rejected_quantity=15, scrap_quantity=10, start_date=timezone.localdate(),
            status=ProductionOrder.Status.IN_PROGRESS,
        )
        order.refresh_from_db()
        ctx = self.client.get("/").context
        # good = 420 - 15 - 10 = 395 ; 395 / 420 = 94.05 %
        self.assertEqual(ctx["yield_percent"], 94.0)
        self.assertEqual(ctx["rejection_percent"], 3.6)
        self.assertEqual(ctx["scrap_percent"], 2.4)
        self.assertAlmostEqual(float(order.yield_percent), 94.05, places=2)

    def test_low_stock_uses_net_balance_and_value(self):
        low = self._product("RM-LOW", 100)       # 150 in - 70 out = 80  -> low
        healthy = self._product("RM-OK", 10)     # 50 in                  -> fine
        empty = self._product("RM-EMPTY", 5)     # never moved, balance 0 -> low
        self._product("RM-NOLEVEL", 0)           # no reorder level       -> ignored
        self._ledger(low, qty_in=150)
        self._ledger(low, qty_out=70)
        self._ledger(healthy, qty_in=50)

        ctx = self.client.get("/").context
        self.assertEqual(ctx["low_stock_count"], 2)
        by_code = {row["product"].code: row["balance"] for row in ctx["low_stock_products"]}
        self.assertEqual(set(by_code), {low.code, empty.code})
        self.assertEqual(by_code[low.code], Decimal("80"))
        self.assertEqual(by_code[empty.code], Decimal("0"))
        # net value = (150-70)*10 + 50*10
        self.assertEqual(ctx["total_stock_value"], Decimal("1300"))

    def test_dashboard_query_count_does_not_grow_with_products(self):
        for i in range(3):
            self._ledger(self._product(f"A-{i}", 100), qty_in=1)
        baseline = self._count_queries()

        for i in range(10):
            self._ledger(self._product(f"B-{i}", 100), qty_in=1)
        self.assertEqual(self._count_queries(), baseline)

    def _count_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get("/").status_code, 200)
        return len(ctx)


class SeedAndAdminSmokeTests(TestCase):
    def test_seed_command_is_idempotent_and_dashboard_renders(self):
        call_command("seed_demo_data", verbosity=0)
        call_command("seed_demo_data", verbosity=0)
        self.client.force_login(User.objects.create_user("tester", password="pass-12345-xyz"))
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["yield_percent"], 94.0)
        self.assertEqual(resp.context["machines_breakdown"], 1)

    def test_every_registered_admin_changelist_loads(self):
        call_command("seed_demo_data", verbosity=0)
        admin_user = User.objects.create_superuser("root", "root@example.com", "pass-12345-xyz")
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        for model in admin.site._registry:
            if model._meta.app_label in ("auth", "contenttypes", "sessions"):
                continue
            name = f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            with self.subTest(model=model._meta.label):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
