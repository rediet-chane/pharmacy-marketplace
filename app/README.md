# 🏥 Pharmacy Marketplace - Ethiopia

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0.3-green.svg)](https://flask.palletsprojects.com)

A B2B pharmaceutical marketplace connecting verified importers with pharmacies in Ethiopia.

## 🌟 Features

- **Importer Dashboard** - List and manage pharmaceutical products
- **Pharmacy Dashboard** - Browse products and request quotes
- **Admin Dashboard** - Manage users, KYC, and platform oversight
- **KYC Verification** - Only verified businesses can transact
- **Quote System** - Request and manage quotes between pharmacies and importers
- **Search & Filter** - Find products by name or brand

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite (production-ready: PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Ready for Railway/Vercel

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/rediet-chane/pharmacy-marketplace.git
cd pharmacy-marketplace

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m flask --app app run --debug