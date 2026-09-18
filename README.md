# 🏭 FactoryOS — Factory Management System (Django)

Ek professional, Django-based Factory Management System (FMS) — poore manufacturing workflow ko cover karta hai:

```
Sales → Planning → Procurement → Inventory → Production → Quality → Maintenance → Dispatch → Costing → Reports
```

## ✨ Kya milta hai is project mein

- **Custom flashy dashboard** (`/`) — live KPIs (yield %, rejection %, scrap %, low stock, breakdowns, pending POs/PRs, open NCRs) + Chart.js graphs, dark-glass login screen.
- **Professional Admin Panel** (`/admin/`) — django-jazzmin theme, full CRUD for **all 11 modules** with inline editing (BOM items, PO items, Job Cards, etc.), search, filters, date-hierarchy.
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
- **http://127.0.0.1:8000/admin/** → full professional CRUD admin for every module

## 📁 Project structure

```
fms_project/
├── manage.py
├── requirements.txt
├── fms/                    # settings, urls, wsgi/asgi, jazzmin config
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
│   └── dashboard/             # custom homepage (views/urls/templates)
├── templates/
│   ├── base.html
│   ├── registration/login.html
│   └── dashboard/index.html
└── static/css/style.css       # custom "FactoryOS" theme
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
- Custom UI screens (non-admin) for Sales Order / Production Order entry with a polished form (abhi ye admin panel se hoti hain)
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
