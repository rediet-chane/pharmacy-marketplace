# Pharmacy Marketplace

B2B pharmaceutical marketplace for Ethiopia, connecting verified importers with pharmacy buyers.

## Tech Stack

- Backend: Python, Flask
- Database: SQLite
- Frontend: HTML, CSS, JavaScript

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app app run --debug
```

The SQLite database is created automatically in `instance/pharmacy_marketplace.sqlite3` on first run.

## Current MVP Scope

- Importer dashboard shell
- Product list page
- Add product form
- API endpoints for creating and listing importer products
- Pharmacy demo login and dashboard
- Pharmacy product browsing, search, quote requests, and quote history
- Admin demo login, overview dashboard, KYC review, user management, product moderation, and subscription monitoring
- Minimal importer verification gate using a seeded demo importer

## Demo Importer

The app seeds a verified demo importer account for local development.

- Importer ID: `demo-importer-1`
- Business name: `Addis Pharma Imports PLC`

## Demo Pharmacy

- Pharmacy ID: `demo-pharmacy-1`
- Business name: `Unity Pharmacy PLC`
- Login page: `/pharmacy/login`

## Demo Admin

- Username: `admin@pharmacymarketplace.com`
- Password: `Admin123!`
- Role: `ADMIN`
- Login page: `/admin/login`
