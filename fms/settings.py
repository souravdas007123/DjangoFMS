"""
FMS - Factory Management System
Django settings
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("FMS_SECRET_KEY", "django-insecure-change-this-in-production-fms-2026")

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    # Admin theme (professional flashy UI) - must be before django.contrib.admin
    "jazzmin",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # FMS apps
    "apps.masters",
    "apps.sales",
    "apps.purchase",
    "apps.inventory",
    "apps.production",
    "apps.quality",
    "apps.maintenance",
    "apps.hr",
    "apps.dispatch",
    "apps.costing",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "fms.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# -------------------------------------------------------------------
# JAZZMIN ADMIN THEME CONFIG - professional flashy sidebar/navigation
# Structured to mirror the FMS workflow: Masters, Sales, Planning,
# Procurement, Inventory, Production, Quality, Maintenance, HR,
# Dispatch, Costing
# -------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "FMS Admin",
    "site_header": "Factory MS",
    "site_brand": "🏭 FactoryOS",
    "welcome_sign": "Welcome to Factory Management System",
    "copyright": "Factory Management System",
    "search_model": ["sales.SalesOrder", "production.ProductionOrder", "masters.Product"],
    "show_sidebar": True,
    "navigation_expanded": False,
    "changeform_format": "horizontal_tabs",
    "related_modal_active": True,
    "custom_css": "css/style.css",
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",

        "masters.Product": "fas fa-box",
        "masters.ProductCategory": "fas fa-layer-group",
        "masters.UnitOfMeasure": "fas fa-ruler",
        "masters.BOM": "fas fa-sitemap",
        "masters.BOMItem": "fas fa-puzzle-piece",
        "masters.Routing": "fas fa-route",
        "masters.RoutingOperation": "fas fa-cogs",
        "masters.WorkCenter": "fas fa-industry",
        "masters.Machine": "fas fa-robot",
        "masters.Warehouse": "fas fa-warehouse",
        "masters.Customer": "fas fa-user-tie",
        "masters.Supplier": "fas fa-truck-loading",

        "sales.Quotation": "fas fa-file-invoice",
        "sales.SalesOrder": "fas fa-shopping-cart",
        "sales.SalesOrderItem": "fas fa-list",

        "purchase.PurchaseRequisition": "fas fa-clipboard-list",
        "purchase.PurchaseOrder": "fas fa-file-contract",
        "purchase.GRN": "fas fa-dolly",

        "inventory.StockLedgerEntry": "fas fa-book",
        "inventory.Batch": "fas fa-barcode",
        "inventory.StockTransfer": "fas fa-exchange-alt",
        "inventory.MaterialIssue": "fas fa-sign-out-alt",
        "inventory.MaterialReturn": "fas fa-undo",
        "inventory.StockAdjustment": "fas fa-balance-scale",

        "production.ProductionPlan": "fas fa-calendar-alt",
        "production.ProductionOrder": "fas fa-tasks",
        "production.JobCard": "fas fa-id-card",
        "production.OperationEntry": "fas fa-stopwatch",
        "production.ScrapEntry": "fas fa-trash-alt",

        "quality.InspectionPlan": "fas fa-clipboard-check",
        "quality.Inspection": "fas fa-search",
        "quality.NCR": "fas fa-exclamation-triangle",
        "quality.CAPA": "fas fa-shield-alt",

        "maintenance.MaintenanceSchedule": "fas fa-calendar-check",
        "maintenance.Breakdown": "fas fa-tools",
        "maintenance.MaintenanceWorkOrder": "fas fa-wrench",
        "maintenance.SparePart": "fas fa-cog",

        "hr.Employee": "fas fa-id-badge",
        "hr.Shift": "fas fa-business-time",
        "hr.Attendance": "fas fa-calendar-day",

        "dispatch.DeliveryOrder": "fas fa-shipping-fast",

        "costing.ProductCost": "fas fa-rupee-sign",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "order_with_respect_to": [
        "masters", "sales", "purchase", "inventory", "production",
        "quality", "maintenance", "hr", "dispatch", "costing", "auth",
    ],
    "topmenu_links": [
        {"name": "Dashboard", "url": "dashboard:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-indigo",
    "accent": "accent-primary",
    "navbar": "navbar-indigo navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-indigo",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
