import os
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        os.makedirs(current_app.instance_path, exist_ok=True)
        db_path = os.path.join(current_app.instance_path, current_app.config["DATABASE"])
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS importers (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            verification_status TEXT NOT NULL CHECK (
                verification_status IN ('PENDING', 'APPROVED', 'REJECTED')
            ),
            account_status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            importer_id TEXT NOT NULL,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            batch_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
            moderation_status TEXT NOT NULL DEFAULT 'APPROVED',
            moderation_note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (importer_id) REFERENCES importers (id),
            UNIQUE (importer_id, batch_number)
        );

        CREATE TABLE IF NOT EXISTS pharmacies (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            verification_status TEXT NOT NULL CHECK (
                verification_status IN ('PENDING', 'APPROVED', 'REJECTED')
            ),
            account_status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quote_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pharmacy_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            importer_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
                status IN ('PENDING', 'ACCEPTED', 'REJECTED')
            ),
            message TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pharmacy_id) REFERENCES pharmacies (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (importer_id) REFERENCES importers (id)
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'ADMIN',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS verification_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL CHECK (user_type IN ('IMPORTER', 'PHARMACY')),
            user_id TEXT NOT NULL,
            business_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
                status IN ('PENDING', 'APPROVED', 'REJECTED')
            ),
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            UNIQUE (user_type, user_id)
        );

        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            user_type TEXT NOT NULL CHECK (user_type IN ('IMPORTER', 'PHARMACY')),
            price_monthly INTEGER NOT NULL,
            listing_limit INTEGER,
            analytics_level TEXT NOT NULL DEFAULT 'NONE',
            priority_support INTEGER NOT NULL DEFAULT 0,
            dedicated_support INTEGER NOT NULL DEFAULT 0,
            api_access INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL CHECK (user_type IN ('IMPORTER', 'PHARMACY')),
            user_id TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (
                status IN ('ACTIVE', 'PAST_DUE', 'CANCELLED')
            ),
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans (id),
            UNIQUE (user_type, user_id, plan_id)
        );

        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL CHECK (user_type IN ('IMPORTER', 'PHARMACY')),
            user_id TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            provider TEXT NOT NULL DEFAULT 'CHAPA',
            tx_ref TEXT NOT NULL UNIQUE,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
                status IN ('PENDING', 'PAID', 'FAILED', 'CANCELLED')
            ),
            checkout_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
        );
        """
    )

    ensure_quote_requests_schema(db)
    ensure_column(db, "importers", "account_status", "TEXT NOT NULL DEFAULT 'ACTIVE'")
    ensure_column(db, "pharmacies", "account_status", "TEXT NOT NULL DEFAULT 'ACTIVE'")
    ensure_column(db, "products", "moderation_status", "TEXT NOT NULL DEFAULT 'APPROVED'")
    ensure_column(db, "products", "moderation_note", "TEXT")
    ensure_column(db, "subscription_plans", "analytics_level", "TEXT NOT NULL DEFAULT 'NONE'")
    ensure_column(db, "subscription_plans", "priority_support", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(db, "subscription_plans", "dedicated_support", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(db, "subscription_plans", "api_access", "INTEGER NOT NULL DEFAULT 0")

    db.execute(
        """
        INSERT OR IGNORE INTO importers (id, business_name, verification_status)
        VALUES (?, ?, ?)
        """,
        ("demo-importer-1", "Addis Pharma Imports PLC", "APPROVED"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO importers (id, business_name, verification_status)
        VALUES (?, ?, ?)
        """,
        ("pending-importer-1", "Blue Nile Pharma Imports PLC", "PENDING"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO products (
            importer_id,
            name,
            brand,
            batch_number,
            expiry_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "demo-importer-1",
            "Amoxicillin 500mg Capsules",
            "Amoxil",
            "AMX-DEMO-2026-001",
            "2028-12-31",
        ),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO pharmacies (id, business_name, verification_status)
        VALUES (?, ?, ?)
        """,
        ("demo-pharmacy-1", "Unity Pharmacy PLC", "APPROVED"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO pharmacies (id, business_name, verification_status)
        VALUES (?, ?, ?)
        """,
        ("pending-pharmacy-1", "Medline Pharmacy", "PENDING"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO admin_users (username, password, role)
        VALUES (?, ?, ?)
        """,
        ("admin@pharmacymarketplace.com", "Admin123!", "ADMIN"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO verification_requests (
            user_type,
            user_id,
            business_name,
            status
        )
        VALUES (?, ?, ?, ?)
        """,
        ("IMPORTER", "pending-importer-1", "Blue Nile Pharma Imports PLC", "PENDING"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO verification_requests (
            user_type,
            user_id,
            business_name,
            status
        )
        VALUES (?, ?, ?, ?)
        """,
        ("PHARMACY", "pending-pharmacy-1", "Medline Pharmacy", "PENDING"),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscription_plans (
            name,
            user_type,
            price_monthly,
            listing_limit,
            analytics_level,
            priority_support,
            dedicated_support,
            api_access
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Free", "IMPORTER", 0, 5, "NONE", 0, 0, 0),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscription_plans (
            name,
            user_type,
            price_monthly,
            listing_limit,
            analytics_level,
            priority_support,
            dedicated_support,
            api_access
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Basic", "IMPORTER", 2500, 50, "BASIC", 0, 0, 0),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscription_plans (
            name,
            user_type,
            price_monthly,
            listing_limit,
            analytics_level,
            priority_support,
            dedicated_support,
            api_access
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Premium", "IMPORTER", 7500, None, "ADVANCED", 1, 0, 0),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscription_plans (
            name,
            user_type,
            price_monthly,
            listing_limit,
            analytics_level,
            priority_support,
            dedicated_support,
            api_access
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Enterprise", "IMPORTER", 20000, None, "ADVANCED", 1, 1, 1),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscription_plans (
            name,
            user_type,
            price_monthly,
            listing_limit,
            analytics_level,
            priority_support,
            dedicated_support,
            api_access
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Pharmacy Buyer Pro", "PHARMACY", 1200, None, "BASIC", 0, 0, 0),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO subscriptions (user_type, user_id, plan_id, status)
        SELECT ?, ?, id, ?
        FROM subscription_plans
        WHERE name = ?
        """,
        ("IMPORTER", "demo-importer-1", "ACTIVE", "Basic"),
    )
    db.commit()


def ensure_column(db, table_name, column_name, definition):
    columns = {
        row["name"]
        for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in columns:
        return

    db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def ensure_quote_requests_schema(db):
    table = db.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'quote_requests'
        """
    ).fetchone()

    if table is None:
        return

    table_sql = table["sql"] or ""
    columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(quote_requests)").fetchall()
    }

    if "message" in columns and "SUBMITTED" not in table_sql:
        return

    db.executescript(
        """
        PRAGMA foreign_keys = OFF;

        ALTER TABLE quote_requests RENAME TO quote_requests_old;

        CREATE TABLE quote_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pharmacy_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            importer_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
                status IN ('PENDING', 'ACCEPTED', 'REJECTED')
            ),
            message TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pharmacy_id) REFERENCES pharmacies (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (importer_id) REFERENCES importers (id)
        );

        INSERT INTO quote_requests (
            id,
            pharmacy_id,
            product_id,
            importer_id,
            status,
            message,
            created_at
        )
        SELECT
            id,
            pharmacy_id,
            product_id,
            importer_id,
            CASE status
                WHEN 'SUBMITTED' THEN 'PENDING'
                WHEN 'REVIEWED' THEN 'ACCEPTED'
                WHEN 'CANCELLED' THEN 'REJECTED'
                ELSE status
            END,
            NULL,
            created_at
        FROM quote_requests_old;

        DROP TABLE quote_requests_old;

        PRAGMA foreign_keys = ON;
        """
    )
