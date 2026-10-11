# 🏭 FactoryOS — Factory Management System (Django)

Ek professional, Django-based Factory Management System (FMS) — poore manufacturing workflow ko cover karta hai:

```
Sales → Planning → Procurement → Inventory → Production → Quality → Maintenance → Dispatch → Costing → Reports
```

## ✨ Kya milta hai is project mein

- **Custom flashy dashboard** (`/`) — live KPIs (yield %, rejection %, scrap %, low stock, breakdowns, pending POs/PRs, open NCRs) + Chart.js graphs, dark-glass login screen.
- **Modern responsive app UI** (`/m/...`) — sidebar navigation, live search (HTMX), filters, sorting, pagination, CSV export, light/dark theme. Full CRUD for **all 11 modules** with inline line-item editing (BOM items, PO items, Job Cards, etc.). Works on desktop, tablet and phone. Access follows Django model permissions, so you can create department roles with Groups.
- **Plain Django admin** (`/admin/`) — kept only as a superuser backup (users, groups, emergency edits). The UI reads its list/search/filter/inline settings from each app's `admin.py`, so registering a model there adds it to the app UI automatically.
- **11 apps / 40+ models** matching the workflow: `masters`, `sales`, `purchase`, `inventory`, `production`, `quality`, `maintenance`, `hr`, `dispatch`, `costing`, `dashboard`.
- **Demo data seeder** — one command loads a realistic "Steel Chair factory" example (BOM, routing, PO→GRN, Sales Order, Production Order, Job Card, NCR, breakdown) so the dashboard is populated instantly.

## 🚀 Setup (5 minutes)

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Create an admin login
python manage.py createsuperuser

# 5. (Optional but recommended) Load demo data
python manage.py seed_demo_data

# 6. Run the server
python manage.py runserver
```

Open:
- **http://127.0.0.1:8000/** → login screen → flashy dashboard
- **http://127.0.0.1:8000/admin/** → plain Django admin (superuser backup)

## 📁 Project structure

```
fms_project/
├── manage.py
├── requirements.txt
├── fms/                    # settings, urls, wsgi/asgi
├── apps/
│   ├── masters/            # Product, BOM, Routing, WorkCenter, Machine, Customer, Supplier, Employee
│   ├── sales/               # Quotation, SalesOrder, Invoice
│   ├── purchase/            # PR, PO, GRN, SupplierPayment
│   ├── inventory/           # StockLedgerEntry, Batch, StockTransfer, MaterialIssue/Return, Adjustment
│   ├── production/          # ProductionPlan, ProductionOrder, JobCard, ScrapEntry, ReworkEntry
│   ├── quality/              # InspectionPlan, Inspection, NCR, CAPA
│   ├── maintenance/          # MaintenanceSchedule, Breakdown, WorkOrder, SparePart
│   ├── hr/                   # Shift, Attendance, LabourAllocation
│   ├── dispatch/              # DeliveryOrder
│   ├── costing/               # ProductCost
│   ├── dashboard/             # homepage KPIs
│   └── ui/                    # generic CRUD screens for every module (registry, views, forms)
├── templates/
│   ├── base.html
│   ├── registration/login.html
│   └── dashboard/index.html
└── static/css/app.css, static/js/app.js   # FactoryOS design system
```

## 🧱 Document flow implemented

```
Sales Order → Production Plan → Production Order → Job Card → Production Entry
     ↓                                                              ↓
Purchase Requisition → Purchase Order → GRN → Incoming QC → Stock  Final QC → NCR/CAPA
                                                                     ↓
                                                          FG Stock → Delivery Order → Dispatch
```

## ➕ Extending it

Har app ka `models.py` aur `admin.py` alag hai — naya field ya model add karna easy hai:

1. `apps/<app>/models.py` mein field/model add karo
2. `apps/<app>/admin.py` mein register/list_display update karo
3. `python manage.py makemigrations && python manage.py migrate`

### Aage ka roadmap (agar chahiye to bata dena, main bana dunga):
- MRP auto-calculation engine (shortage calculation from BOM explosion)
- Role-based permissions per department (Production Manager, Store Keeper, QC Inspector, etc.)
- REST API (Django REST Framework) for a mobile shop-floor app
- Automatic stock ledger posting on GRN-accept / Material Issue / Production Receipt (currently these are recorded as separate ledger entries — wiring the automatic trigger is the natural next step)
- PDF generation for PO / Invoice / Delivery Order

## ⚠️ Production checklist (before real deployment)
- Change `SECRET_KEY` in `fms/settings.py` (or set `FMS_SECRET_KEY` env var)
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`
- Switch `DATABASES` to PostgreSQL/MySQL
- Run behind Gunicorn/Nginx, collect static files: `python manage.py collectstatic`

## Deploy on CloudPanel (Python site)

1. DNS: add an `A` record `fms` -> server IP. In CloudPanel create a **Python site** for `fms.socialflylive.com` (note the site user), then issue a Let's Encrypt certificate.
2. As the site user, put the code in `~/htdocs/fms.socialflylive.com/` and run `deploy/setup.sh fms.socialflylive.com`, then `createsuperuser`.
3. As root run `deploy/install_service.sh <site-user> fms.socialflylive.com 8010` and set the site's App Port to `8010` in CloudPanel.
4. Updates: `deploy/update.sh` (site user) then `systemctl restart factoryos` (root).

Config lives in `.env` (see `.env.example`). Back up `db.sqlite3` and `media/`.
