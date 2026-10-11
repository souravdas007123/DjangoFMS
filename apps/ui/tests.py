from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.masters.models import Customer, Product, UnitOfMeasure
from apps.sales.models import SalesOrder
from apps.ui import registry

User = get_user_model()
PASSWORD = "pass-12345-xyz"


class UiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)

    def setUp(self):
        self.client.force_login(self.admin)

    def url(self, name, *args):
        return reverse(f"ui:{name}", args=args)


class RegistryTests(UiTestCase):
    def test_all_eleven_modules_are_registered(self):
        groups = {cfg.group for cfg in registry.get_registry().values()}
        self.assertEqual(
            groups,
            {"masters", "sales", "purchase", "inventory", "production", "quality",
             "maintenance", "hr", "dispatch", "costing"},
        )
        self.assertGreaterEqual(len(registry.get_registry()), 40)

    def test_auth_models_are_not_exposed(self):
        self.assertEqual(self.client.get("/m/auth/user/").status_code, 404)
        self.assertEqual(self.client.get("/m/nope/nothing/").status_code, 404)


class EveryScreenLoadsTests(UiTestCase):
    def test_every_list_page(self):
        for cfg in registry.get_registry().values():
            with self.subTest(model=cfg.model._meta.label):
                self.assertEqual(self.client.get(cfg.list_url).status_code, 200)

    def test_every_create_form(self):
        for cfg in registry.get_registry().values():
            with self.subTest(model=cfg.model._meta.label):
                self.assertEqual(self.client.get(cfg.create_url).status_code, 200)

    def test_every_detail_and_edit_page(self):
        for cfg in registry.get_registry().values():
            obj = cfg.model.objects.first()
            if obj is None:
                continue
            with self.subTest(model=cfg.model._meta.label):
                self.assertEqual(self.client.get(cfg.detail_url(obj.pk)).status_code, 200)
                self.assertEqual(self.client.get(cfg.update_url(obj.pk)).status_code, 200)
                self.assertEqual(self.client.get(cfg.delete_url(obj.pk)).status_code, 200)

    def test_every_list_exports_csv(self):
        for cfg in registry.get_registry().values():
            with self.subTest(model=cfg.model._meta.label):
                resp = self.client.get(cfg.list_url, {"export": "csv"})
                self.assertEqual(resp.status_code, 200)
                self.assertIn("text/csv", resp["Content-Type"])


class CrudTests(UiTestCase):
    def test_create_simple_record(self):
        resp = self.client.post(self.url("create", "masters", "unitofmeasure"),
                                {"code": "LTR", "name": "Litre", "is_active": "on"})
        unit = UnitOfMeasure.objects.get(code="LTR")
        self.assertRedirects(resp, self.url("detail", "masters", "unitofmeasure", unit.pk))

    def test_validation_errors_are_shown_and_nothing_saved(self):
        resp = self.client.post(self.url("create", "masters", "unitofmeasure"), {"code": "", "name": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required")
        self.assertFalse(UnitOfMeasure.objects.filter(name="").exists())

    def test_duplicate_unique_value_is_rejected(self):
        resp = self.client.post(self.url("create", "masters", "unitofmeasure"), {"code": "KG", "name": "Dup"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(UnitOfMeasure.objects.filter(code="KG").count(), 1)

    def test_update_record(self):
        customer = Customer.objects.get(code="CUST-001")
        resp = self.client.post(
            self.url("update", "masters", "customer", customer.pk),
            {"code": customer.code, "name": "ABC Industries Ltd", "credit_limit": "750000", "is_active": "on"},
        )
        self.assertRedirects(resp, self.url("detail", "masters", "customer", customer.pk))
        customer.refresh_from_db()
        self.assertEqual(customer.name, "ABC Industries Ltd")
        self.assertEqual(customer.credit_limit, Decimal("750000"))

    def test_delete_record(self):
        unit = UnitOfMeasure.objects.create(code="TMP", name="Temp")
        resp = self.client.post(self.url("delete", "masters", "unitofmeasure", unit.pk))
        self.assertRedirects(resp, self.url("list", "masters", "unitofmeasure"))
        self.assertFalse(UnitOfMeasure.objects.filter(pk=unit.pk).exists())

    def test_delete_protected_record_is_blocked_with_message(self):
        unit = UnitOfMeasure.objects.get(code="KG")  # used by seeded products (PROTECT)
        resp = self.client.post(self.url("delete", "masters", "unitofmeasure", unit.pk), follow=True)
        self.assertTrue(UnitOfMeasure.objects.filter(pk=unit.pk).exists())
        self.assertContains(resp, "cannot be deleted")


class InlineRowTests(UiTestCase):
    def sales_order_payload(self, **overrides):
        customer = Customer.objects.get(code="CUST-001")
        product = Product.objects.get(code="FG-CHAIR")
        data = {
            "number": "SO-UI-1", "customer": customer.pk, "order_date": "2026-10-01",
            "delivery_date": "2026-10-20", "status": "DRAFT", "remarks": "", "is_active": "on",
            "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
            "items-0-id": "", "items-0-sales_order": "",
            "items-0-product": product.pk, "items-0-quantity": "10",
            "items-0-rate": "899", "items-0-delivered_quantity": "0",
        }
        data.update(overrides)
        return data

    def test_create_document_with_line_items(self):
        resp = self.client.post(self.url("create", "sales", "salesorder"), self.sales_order_payload())
        order = SalesOrder.objects.get(number="SO-UI-1")
        self.assertRedirects(resp, self.url("detail", "sales", "salesorder", order.pk))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal("8990"))

    def test_invalid_line_item_blocks_the_whole_save(self):
        resp = self.client.post(self.url("create", "sales", "salesorder"),
                                self.sales_order_payload(**{"items-0-rate": ""}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(SalesOrder.objects.filter(number="SO-UI-1").exists())

    def test_blank_extra_row_is_ignored(self):
        data = self.sales_order_payload(**{
            "items-0-product": "", "items-0-quantity": "", "items-0-rate": "",
        })
        resp = self.client.post(self.url("create", "sales", "salesorder"), data)
        order = SalesOrder.objects.get(number="SO-UI-1")
        self.assertRedirects(resp, self.url("detail", "sales", "salesorder", order.pk))
        self.assertEqual(order.items.count(), 0)

    def test_edit_form_shows_existing_rows_and_detail_shows_items(self):
        order = SalesOrder.objects.get(number="SO-00001")
        edit = self.client.get(self.url("update", "sales", "salesorder", order.pk))
        self.assertContains(edit, 'name="items-TOTAL_FORMS"')
        self.assertContains(edit, 'id="tpl-items"')
        detail = self.client.get(self.url("detail", "sales", "salesorder", order.pk))
        self.assertContains(detail, "FG-CHAIR")


class ListBehaviourTests(UiTestCase):
    def test_search_filters_rows(self):
        url = self.url("list", "masters", "customer")
        self.assertContains(self.client.get(url, {"q": "ABC"}), "ABC Industries")
        self.assertNotContains(self.client.get(url, {"q": "zzz-no-match"}), "ABC Industries")

    def test_htmx_request_returns_only_the_results_fragment(self):
        url = self.url("list", "masters", "customer")
        fragment = self.client.get(url, HTTP_HX_REQUEST="true")
        self.assertEqual(fragment.status_code, 200)
        self.assertNotContains(fragment, "<html")
        self.assertContains(fragment, "ABC Industries")
        self.assertContains(self.client.get(url), "<html")

    def test_choice_filter(self):
        url = self.url("list", "sales", "salesorder")
        self.assertContains(self.client.get(url, {"f_status": "IN_PRODUCTION"}), "SO-00001")
        self.assertNotContains(self.client.get(url, {"f_status": "DRAFT"}), "SO-00001")

    def test_bad_filter_value_does_not_crash(self):
        url = self.url("list", "masters", "machine")
        self.assertEqual(self.client.get(url, {"f_work_center": "not-a-number"}).status_code, 200)

    def test_sorting_and_invalid_sort_are_safe(self):
        url = self.url("list", "masters", "product")
        asc = self.client.get(url, {"o": "name"})
        self.assertEqual(asc.status_code, 200)
        self.assertEqual(self.client.get(url, {"o": "-name"}).status_code, 200)
        self.assertEqual(self.client.get(url, {"o": "does_not_exist; drop"}).status_code, 200)

    def test_pagination(self):
        for i in range(25):
            UnitOfMeasure.objects.create(code=f"U{i:02d}", name=f"Unit {i}")
        url = self.url("list", "masters", "unitofmeasure")
        page1 = self.client.get(url)
        self.assertEqual(len(page1.context["rows"]), 20)
        self.assertEqual(len(self.client.get(url, {"page": 2}).context["rows"]), 7)  # 25 new + 2 seeded = 27
        self.assertEqual(self.client.get(url, {"page": 999}).status_code, 200)

    def test_csv_export_has_header_and_rows(self):
        resp = self.client.get(self.url("list", "masters", "customer"), {"export": "csv"})
        body = resp.content.decode("utf-8-sig")
        self.assertIn("ABC Industries", body)
        self.assertIn("Code", body.splitlines()[0])


class PermissionTests(UiTestCase):
    def make_user(self, *codenames):
        user = User.objects.create_user("limited", password=PASSWORD)
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(codename=codename))
        return user

    def test_anonymous_is_sent_to_login(self):
        self.client.logout()
        resp = self.client.get(self.url("list", "masters", "customer"))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].startswith(reverse("login")))

    def test_user_without_permission_gets_403(self):
        self.client.force_login(self.make_user())
        self.assertEqual(self.client.get(self.url("list", "masters", "customer")).status_code, 403)

    def test_view_only_user_cannot_add_edit_or_delete(self):
        customer = Customer.objects.get(code="CUST-001")
        self.client.force_login(self.make_user("view_customer"))
        self.assertEqual(self.client.get(self.url("list", "masters", "customer")).status_code, 200)
        self.assertEqual(self.client.get(self.url("create", "masters", "customer")).status_code, 403)
        self.assertEqual(self.client.get(self.url("update", "masters", "customer", customer.pk)).status_code, 403)
        self.assertEqual(self.client.post(self.url("delete", "masters", "customer", customer.pk)).status_code, 403)
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())

    def test_sidebar_only_lists_permitted_modules(self):
        self.client.force_login(self.make_user("view_customer"))
        html = self.client.get(self.url("list", "masters", "customer")).content.decode()
        self.assertIn("/m/masters/customer/", html)
        self.assertNotIn("/m/sales/salesorder/", html)

    def test_list_hides_buttons_the_user_cannot_use(self):
        self.client.force_login(self.make_user("view_customer"))
        html = self.client.get(self.url("list", "masters", "customer")).content.decode()
        self.assertNotIn(self.url("create", "masters", "customer"), html)
