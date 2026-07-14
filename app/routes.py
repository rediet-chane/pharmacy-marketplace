from datetime import date, datetime
import json
import sqlite3
import time
import urllib.error
import urllib.request

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from .db import get_db


bp = Blueprint("main", __name__)

DEMO_IMPORTER_ID = "demo-importer-1"
DEMO_PHARMACY_ID = "demo-pharmacy-1"
DEMO_ADMIN_USERNAME = "admin@pharmacymarketplace.com"


def get_current_importer():
    db = get_db()
    return db.execute(
        "SELECT * FROM importers WHERE id = ?",
        (DEMO_IMPORTER_ID,),
    ).fetchone()


def get_current_pharmacy():
    db = get_db()
    return db.execute(
        "SELECT * FROM pharmacies WHERE id = ?",
        (DEMO_PHARMACY_ID,),
    ).fetchone()


def get_current_admin():
    db = get_db()
    return db.execute(
        "SELECT * FROM admin_users WHERE username = ?",
        (DEMO_ADMIN_USERNAME,),
    ).fetchone()


def get_platform_stats():
    db = get_db()
    importer_count = db.execute("SELECT COUNT(*) AS count FROM importers").fetchone()["count"]
    pharmacy_count = db.execute("SELECT COUNT(*) AS count FROM pharmacies").fetchone()["count"]
    product_count = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
    quote_count = db.execute("SELECT COUNT(*) AS count FROM quote_requests").fetchone()["count"]
    pending_kyc_count = db.execute(
        "SELECT COUNT(*) AS count FROM verification_requests WHERE status = 'PENDING'"
    ).fetchone()["count"]
    subscription_count = db.execute(
        "SELECT COUNT(*) AS count FROM subscriptions WHERE status = 'ACTIVE'"
    ).fetchone()["count"]

    return {
        "totalUsers": importer_count + pharmacy_count,
        "importers": importer_count,
        "pharmacies": pharmacy_count,
        "products": product_count,
        "orders": quote_count,
        "pendingKyc": pending_kyc_count,
        "activeSubscriptions": subscription_count,
    }


def get_importer_subscription(importer_id):
    return get_db().execute(
        """
        SELECT
            subscriptions.*,
            subscription_plans.name AS plan_name,
            subscription_plans.price_monthly,
            subscription_plans.listing_limit,
            subscription_plans.analytics_level,
            subscription_plans.priority_support,
            subscription_plans.dedicated_support,
            subscription_plans.api_access
        FROM subscriptions
        JOIN subscription_plans ON subscription_plans.id = subscriptions.plan_id
        WHERE subscriptions.user_type = 'IMPORTER'
          AND subscriptions.user_id = ?
          AND subscriptions.status = 'ACTIVE'
        ORDER BY subscriptions.started_at DESC, subscriptions.id DESC
        LIMIT 1
        """,
        (importer_id,),
    ).fetchone()


def get_free_importer_plan():
    return get_db().execute(
        """
        SELECT *
        FROM subscription_plans
        WHERE user_type = 'IMPORTER' AND name = 'Free'
        """
    ).fetchone()


def get_importer_entitlements(importer_id):
    subscription = get_importer_subscription(importer_id)
    plan = subscription or get_free_importer_plan()

    return {
        "planName": plan["plan_name"] if "plan_name" in plan.keys() else plan["name"],
        "listingLimit": plan["listing_limit"],
        "analyticsLevel": plan["analytics_level"],
        "prioritySupport": bool(plan["priority_support"]),
        "dedicatedSupport": bool(plan["dedicated_support"]),
        "apiAccess": bool(plan["api_access"]),
        "priceMonthly": plan["price_monthly"],
    }


def count_importer_products(importer_id):
    return get_db().execute(
        """
        SELECT COUNT(*) AS count
        FROM products
        WHERE importer_id = ? AND status != 'INACTIVE'
        """,
        (importer_id,),
    ).fetchone()["count"]


def activate_subscription(db, user_type, user_id, plan_id):
    db.execute(
        """
        UPDATE subscriptions
        SET status = 'CANCELLED'
        WHERE user_type = ? AND user_id = ? AND status = 'ACTIVE'
        """,
        (user_type, user_id),
    )
    cursor = db.execute(
        """
        UPDATE subscriptions
        SET status = 'ACTIVE', started_at = CURRENT_TIMESTAMP
        WHERE user_type = ? AND user_id = ? AND plan_id = ?
        """,
        (user_type, user_id, plan_id),
    )
    if cursor.rowcount == 0:
        db.execute(
            """
            INSERT INTO subscriptions (user_type, user_id, plan_id, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_type, user_id, plan_id, "ACTIVE"),
        )


def initialize_chapa_checkout(importer, plan, tx_ref):
    amount = int(plan["price_monthly"])
    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": "billing@pharmacymarketplace.com",
        "first_name": importer["business_name"],
        "last_name": "Importer",
        "tx_ref": tx_ref,
        "callback_url": url_for("main.chapa_webhook", _external=True),
        "return_url": url_for("main.importer_subscription_page", _external=True),
        "customization": {
            "title": "Pharmacy Marketplace Subscription",
            "description": f"{plan['name']} monthly subscription",
        },
    }

    secret_key = current_app.config.get("CHAPA_SECRET_KEY") or ""
    if not secret_key:
        return {
            "checkout_url": None,
            "demo": True,
            "message": "CHAPA_SECRET_KEY is not configured. Transaction was recorded in demo mode.",
        }

    request_data = json.dumps(payload).encode("utf-8")
    chapa_request = urllib.request.Request(
        current_app.config["CHAPA_INITIALIZE_URL"],
        data=request_data,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(chapa_request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError(f"Chapa checkout initialization failed: {error}") from error

    checkout_url = data.get("data", {}).get("checkout_url")
    if not checkout_url:
        raise RuntimeError("Chapa did not return a checkout URL.")

    return {
        "checkout_url": checkout_url,
        "demo": False,
        "message": "Checkout initialized.",
    }


def require_verified_importer():
    importer = get_current_importer()
    if importer is None:
        return None, (
            jsonify(
                {
                    "error": "IMPORTER_NOT_FOUND",
                    "message": "Importer account was not found.",
                }
            ),
            403,
        )

    if importer["verification_status"] != "APPROVED":
        return None, (
            jsonify(
                {
                    "error": "IMPORTER_NOT_VERIFIED",
                    "message": "Your importer account must be verified before adding products.",
                }
            ),
            403,
        )

    return importer, None


def require_verified_pharmacy():
    pharmacy = get_current_pharmacy()
    if pharmacy is None:
        return None, (
            jsonify(
                {
                    "error": "PHARMACY_NOT_FOUND",
                    "message": "Pharmacy account was not found.",
                }
            ),
            403,
        )

    if pharmacy["verification_status"] != "APPROVED":
        return None, (
            jsonify(
                {
                    "error": "PHARMACY_NOT_VERIFIED",
                    "message": "Your pharmacy account must be verified before requesting quotes.",
                }
            ),
            403,
        )

    return pharmacy, None


def get_all_business_users():
    return get_db().execute(
        """
        SELECT
            id,
            business_name,
            verification_status,
            account_status,
            created_at,
            'IMPORTER' AS user_type
        FROM importers
        UNION ALL
        SELECT
            id,
            business_name,
            verification_status,
            account_status,
            created_at,
            'PHARMACY' AS user_type
        FROM pharmacies
        ORDER BY created_at DESC, business_name ASC
        """
    ).fetchall()


def update_business_status(user_type, user_id, field, value):
    table_name = None
    if user_type == "IMPORTER":
        table_name = "importers"
    elif user_type == "PHARMACY":
        table_name = "pharmacies"

    if table_name is None:
        return False

    cursor = get_db().execute(
        f"UPDATE {table_name} SET {field} = ? WHERE id = ?",
        (value, user_id),
    )
    return cursor.rowcount > 0


def serialize_product(row):
    return {
        "id": row["id"],
        "importerId": row["importer_id"],
        "name": row["name"],
        "brand": row["brand"],
        "batchNumber": row["batch_number"],
        "expiryDate": row["expiry_date"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_marketplace_product(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "brand": row["brand"],
        "batchNumber": row["batch_number"],
        "expiryDate": row["expiry_date"],
        "status": row["status"],
        "importerId": row["importer_id"],
        "importerBusinessName": row["importer_business_name"],
        "importerVerificationStatus": row["importer_verification_status"],
    }


def serialize_quote_request(row):
    return {
        "id": row["id"],
        "productName": row["product_name"],
        "productBrand": row["product_brand"],
        "importerBusinessName": row["importer_business_name"],
        "importerVerificationStatus": row["importer_verification_status"],
        "status": row["status"],
        "message": row["message"],
        "createdAt": row["created_at"],
    }


def validate_product_payload(payload):
    errors = {}

    name = str(payload.get("name", "")).strip()
    brand = str(payload.get("brand", "")).strip()
    batch_number = str(payload.get("batchNumber", "")).strip()
    expiry_date = str(payload.get("expiryDate", "")).strip()

    if len(name) < 2 or len(name) > 150:
        errors["name"] = "Product name must be between 2 and 150 characters."

    if len(brand) < 2 or len(brand) > 100:
        errors["brand"] = "Brand must be between 2 and 100 characters."

    if len(batch_number) < 2 or len(batch_number) > 80:
        errors["batchNumber"] = "Batch number must be between 2 and 80 characters."

    parsed_expiry_date = None
    try:
        parsed_expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except ValueError:
        errors["expiryDate"] = "Expiry date must use YYYY-MM-DD format."

    if parsed_expiry_date and parsed_expiry_date <= date.today():
        errors["expiryDate"] = "Expiry date must be in the future."

    return errors, {
        "name": name,
        "brand": brand,
        "batch_number": batch_number,
        "expiry_date": expiry_date,
    }


@bp.get("/")
def index():
    return redirect(url_for("main.importer_products_page"))


@bp.get("/pharmacy/login")
def pharmacy_login():
    pharmacy = get_current_pharmacy()
    return render_template("pharmacy_login.html", pharmacy=pharmacy)


@bp.get("/admin/login")
def admin_login():
    admin = get_current_admin()
    return render_template("admin_login.html", admin=admin)


@bp.get("/importer/dashboard")
def importer_dashboard():
    importer = get_current_importer()
    return render_template("dashboard.html", importer=importer)


@bp.get("/importer/dashboard/products")
def importer_products_page():
    importer = get_current_importer()
    return render_template("products.html", importer=importer)


@bp.get("/importer/subscription")
def importer_subscription_page():
    importer = get_current_importer()
    entitlements = get_importer_entitlements(importer["id"]) if importer else None
    product_count = count_importer_products(importer["id"]) if importer else 0
    plans = get_db().execute(
        """
        SELECT *
        FROM subscription_plans
        WHERE user_type = 'IMPORTER' AND is_active = 1
        ORDER BY price_monthly ASC
        """
    ).fetchall()
    transactions = get_db().execute(
        """
        SELECT payment_transactions.*, subscription_plans.name AS plan_name
        FROM payment_transactions
        JOIN subscription_plans ON subscription_plans.id = payment_transactions.plan_id
        WHERE payment_transactions.user_type = 'IMPORTER'
          AND payment_transactions.user_id = ?
        ORDER BY payment_transactions.created_at DESC, payment_transactions.id DESC
        LIMIT 10
        """,
        (importer["id"],),
    ).fetchall() if importer else []
    return render_template(
        "importer_subscription.html",
        importer=importer,
        entitlements=entitlements,
        product_count=product_count,
        plans=plans,
        transactions=transactions,
    )


@bp.get("/pharmacy/dashboard")
def pharmacy_dashboard():
    pharmacy = get_current_pharmacy()
    quote_requests = []

    if pharmacy:
        rows = get_db().execute(
            """
            SELECT
                quote_requests.*,
                products.name AS product_name,
                products.brand AS product_brand,
                importers.business_name AS importer_business_name,
                importers.verification_status AS importer_verification_status
            FROM quote_requests
            JOIN products ON products.id = quote_requests.product_id
            JOIN importers ON importers.id = quote_requests.importer_id
            WHERE quote_requests.pharmacy_id = ?
            ORDER BY quote_requests.created_at DESC, quote_requests.id DESC
            """,
            (pharmacy["id"],),
        ).fetchall()
        quote_requests = [serialize_quote_request(row) for row in rows]

    return render_template(
        "pharmacy_dashboard.html",
        pharmacy=pharmacy,
        quote_requests=quote_requests,
    )


@bp.get("/pharmacy/products")
def pharmacy_products_page():
    pharmacy = get_current_pharmacy()
    return render_template("pharmacy_products.html", pharmacy=pharmacy)


@bp.get("/admin/dashboard")
def admin_dashboard():
    admin = get_current_admin()
    stats = get_platform_stats()
    pending_requests = get_db().execute(
        """
        SELECT *
        FROM verification_requests
        WHERE status = 'PENDING'
        ORDER BY submitted_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()
    return render_template(
        "admin_dashboard.html",
        admin=admin,
        stats=stats,
        pending_requests=pending_requests,
    )


@bp.get("/admin/kyc-review")
def admin_kyc_review():
    admin = get_current_admin()
    requests = get_db().execute(
        """
        SELECT *
        FROM verification_requests
        ORDER BY
            CASE status
                WHEN 'PENDING' THEN 0
                WHEN 'APPROVED' THEN 1
                ELSE 2
            END,
            submitted_at DESC,
            id DESC
        """
    ).fetchall()
    return render_template("admin_kyc_review.html", admin=admin, requests=requests)


@bp.get("/admin/users")
def admin_users():
    admin = get_current_admin()
    users = get_all_business_users()
    return render_template("admin_users.html", admin=admin, users=users)


@bp.get("/admin/products")
def admin_products():
    admin = get_current_admin()
    products = get_db().execute(
        """
        SELECT
            products.*,
            importers.business_name AS importer_business_name,
            importers.verification_status AS importer_verification_status
        FROM products
        JOIN importers ON importers.id = products.importer_id
        ORDER BY products.created_at DESC, products.id DESC
        """
    ).fetchall()
    return render_template("admin_products.html", admin=admin, products=products)


@bp.get("/admin/subscriptions")
def admin_subscriptions():
    admin = get_current_admin()
    plans = get_db().execute(
        """
        SELECT *
        FROM subscription_plans
        ORDER BY user_type, price_monthly ASC
        """
    ).fetchall()
    subscriptions = get_db().execute(
        """
        SELECT
            subscriptions.*,
            subscription_plans.name AS plan_name,
            subscription_plans.price_monthly,
            COALESCE(importers.business_name, pharmacies.business_name) AS business_name
        FROM subscriptions
        JOIN subscription_plans ON subscription_plans.id = subscriptions.plan_id
        LEFT JOIN importers
            ON subscriptions.user_type = 'IMPORTER'
           AND importers.id = subscriptions.user_id
        LEFT JOIN pharmacies
            ON subscriptions.user_type = 'PHARMACY'
           AND pharmacies.id = subscriptions.user_id
        ORDER BY subscriptions.started_at DESC, subscriptions.id DESC
        """
    ).fetchall()
    return render_template(
        "admin_subscriptions.html",
        admin=admin,
        plans=plans,
        subscriptions=subscriptions,
    )


@bp.post("/api/importer/subscription/checkout")
def importer_subscription_checkout():
    importer, error_response = require_verified_importer()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    plan_id = payload.get("planId")
    if not isinstance(plan_id, int):
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Plan ID is required.",
                }
            ),
            400,
        )

    plan = get_db().execute(
        """
        SELECT *
        FROM subscription_plans
        WHERE id = ? AND user_type = 'IMPORTER' AND is_active = 1
        """,
        (plan_id,),
    ).fetchone()
    if plan is None:
        return (
            jsonify(
                {
                    "error": "PLAN_NOT_FOUND",
                    "message": "Subscription plan was not found.",
                }
            ),
            404,
        )

    if plan["price_monthly"] == 0:
        db = get_db()
        activate_subscription(db, "IMPORTER", importer["id"], plan["id"])
        db.commit()
        return jsonify({"message": "Free plan activated.", "checkoutUrl": None})

    tx_ref = f"pm-{importer['id']}-{plan['id']}-{int(time.time())}"
    result = None
    try:
        result = initialize_chapa_checkout(importer, plan, tx_ref)
    except RuntimeError as error:
        return (
            jsonify(
                {
                    "error": "CHAPA_INITIALIZATION_FAILED",
                    "message": str(error),
                }
            ),
            502,
        )

    db = get_db()
    db.execute(
        """
        INSERT INTO payment_transactions (
            user_type,
            user_id,
            plan_id,
            tx_ref,
            amount,
            checkout_url
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "IMPORTER",
            importer["id"],
            plan["id"],
            tx_ref,
            plan["price_monthly"],
            result["checkout_url"],
        ),
    )
    db.commit()

    return jsonify(
        {
            "message": result["message"],
            "checkoutUrl": result["checkout_url"],
            "demo": result["demo"],
            "txRef": tx_ref,
        }
    )


@bp.post("/api/payments/chapa/webhook")
def chapa_webhook():
    payload = request.get_json(silent=True) or {}
    tx_ref = payload.get("tx_ref") or payload.get("trx_ref")
    status = str(payload.get("status", "")).lower()

    if not tx_ref:
        return jsonify({"message": "Missing transaction reference."}), 400

    db = get_db()
    transaction = db.execute(
        "SELECT * FROM payment_transactions WHERE tx_ref = ?",
        (tx_ref,),
    ).fetchone()
    if transaction is None:
        return jsonify({"message": "Transaction not found."}), 404

    if status in {"success", "successful", "paid"}:
        db.execute(
            """
            UPDATE payment_transactions
            SET status = 'PAID', updated_at = CURRENT_TIMESTAMP
            WHERE tx_ref = ?
            """,
            (tx_ref,),
        )
        activate_subscription(
            db,
            transaction["user_type"],
            transaction["user_id"],
            transaction["plan_id"],
        )
    else:
        db.execute(
            """
            UPDATE payment_transactions
            SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP
            WHERE tx_ref = ?
            """,
            (tx_ref,),
        )

    db.commit()
    return jsonify({"message": "Webhook processed."})


@bp.get("/api/importer/products")
def list_importer_products():
    importer, error_response = require_verified_importer()
    if error_response:
        return error_response

    rows = get_db().execute(
        """
        SELECT *
        FROM products
        WHERE importer_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (importer["id"],),
    ).fetchall()

    return jsonify([serialize_product(row) for row in rows])


@bp.get("/api/pharmacy/products")
def list_pharmacy_products():
    pharmacy, error_response = require_verified_pharmacy()
    if error_response:
        return error_response

    search = request.args.get("search", "").strip()
    params = []
    search_clause = ""

    if search:
        search_clause = "AND (products.name LIKE ? OR products.brand LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    rows = get_db().execute(
        f"""
        SELECT
            products.*,
            importers.business_name AS importer_business_name,
            importers.verification_status AS importer_verification_status
        FROM products
        JOIN importers ON importers.id = products.importer_id
        WHERE products.status = 'ACTIVE'
          AND importers.verification_status = 'APPROVED'
          {search_clause}
        ORDER BY products.created_at DESC, products.id DESC
        """,
        params,
    ).fetchall()

    return jsonify([serialize_marketplace_product(row) for row in rows])


@bp.post("/api/pharmacy/quote-request")
def create_quote_request():
    pharmacy, error_response = require_verified_pharmacy()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    product_id = payload.get("productId")
    message = str(payload.get("message", "")).strip() or None

    if not isinstance(product_id, int):
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Product ID is required.",
                }
            ),
            400,
        )

    db = get_db()
    product = db.execute(
        """
        SELECT products.*, importers.verification_status AS importer_verification_status
        FROM products
        JOIN importers ON importers.id = products.importer_id
        WHERE products.id = ?
        """,
        (product_id,),
    ).fetchone()

    if product is None or product["status"] != "ACTIVE":
        return (
            jsonify(
                {
                    "error": "PRODUCT_NOT_AVAILABLE",
                    "message": "This product is not available for quote requests.",
                }
            ),
            404,
        )

    if product["importer_verification_status"] != "APPROVED":
        return (
            jsonify(
                {
                    "error": "IMPORTER_NOT_VERIFIED",
                    "message": "Quotes can only be requested from verified importers.",
                }
            ),
            403,
        )

    cursor = db.execute(
        """
        INSERT INTO quote_requests (
            pharmacy_id,
            product_id,
            importer_id,
            status,
            message
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (pharmacy["id"], product["id"], product["importer_id"], "PENDING", message),
    )
    db.commit()

    return (
        jsonify(
            {
                "id": cursor.lastrowid,
                "productId": product["id"],
                "pharmacyId": pharmacy["id"],
                "importerId": product["importer_id"],
                "status": "PENDING",
                "messageText": message,
                "message": "Quote request submitted.",
            }
        ),
        201,
    )


@bp.post("/api/admin/verify-user")
def admin_verify_user():
    payload = request.get_json(silent=True) or {}
    user_type = str(payload.get("userType", "")).upper()
    user_id = str(payload.get("userId", "")).strip()
    decision = str(payload.get("decision", "")).upper()

    if user_type not in {"IMPORTER", "PHARMACY"} or decision not in {"APPROVED", "REJECTED"}:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "User type and decision are required.",
                }
            ),
            400,
        )

    db = get_db()
    updated = update_business_status(user_type, user_id, "verification_status", decision)
    if not updated:
        return (
            jsonify(
                {
                    "error": "USER_NOT_FOUND",
                    "message": "The selected business account was not found.",
                }
            ),
            404,
        )

    db.execute(
        """
        UPDATE verification_requests
        SET status = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE user_type = ? AND user_id = ?
        """,
        (decision, user_type, user_id),
    )
    db.commit()

    return jsonify(
        {
            "userType": user_type,
            "userId": user_id,
            "status": decision,
            "message": "Verification status updated.",
        }
    )


@bp.post("/api/admin/suspend-user")
def admin_suspend_user():
    payload = request.get_json(silent=True) or {}
    user_type = str(payload.get("userType", "")).upper()
    user_id = str(payload.get("userId", "")).strip()
    action = str(payload.get("action", "")).upper()

    if user_type not in {"IMPORTER", "PHARMACY"} or action not in {"SUSPEND", "REACTIVATE"}:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "User type and suspension action are required.",
                }
            ),
            400,
        )

    status = "SUSPENDED" if action == "SUSPEND" else "ACTIVE"
    db = get_db()
    updated = update_business_status(user_type, user_id, "account_status", status)
    if not updated:
        return (
            jsonify(
                {
                    "error": "USER_NOT_FOUND",
                    "message": "The selected business account was not found.",
                }
            ),
            404,
        )

    db.commit()
    return jsonify(
        {
            "userType": user_type,
            "userId": user_id,
            "accountStatus": status,
            "message": "Account status updated.",
        }
    )


@bp.post("/api/admin/approve-product")
def admin_approve_product():
    payload = request.get_json(silent=True) or {}
    product_id = payload.get("productId")
    action = str(payload.get("action", "")).upper()
    note = str(payload.get("note", "")).strip() or None

    if not isinstance(product_id, int) or action not in {"APPROVE", "FLAG", "REJECT"}:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Product ID and moderation action are required.",
                }
            ),
            400,
        )

    moderation_status = {
        "APPROVE": "APPROVED",
        "FLAG": "FLAGGED",
        "REJECT": "REJECTED",
    }[action]
    product_status = "INACTIVE" if action == "REJECT" else "ACTIVE"

    db = get_db()
    cursor = db.execute(
        """
        UPDATE products
        SET moderation_status = ?,
            moderation_note = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (moderation_status, note, product_status, product_id),
    )
    if cursor.rowcount == 0:
        return (
            jsonify(
                {
                    "error": "PRODUCT_NOT_FOUND",
                    "message": "The selected product was not found.",
                }
            ),
            404,
        )

    db.commit()
    return jsonify(
        {
            "productId": product_id,
            "moderationStatus": moderation_status,
            "status": product_status,
            "message": "Product moderation status updated.",
        }
    )


@bp.post("/api/admin/update-plan")
def admin_update_plan():
    payload = request.get_json(silent=True) or {}
    plan_id = payload.get("planId")
    price_monthly = payload.get("priceMonthly")
    listing_limit = payload.get("listingLimit")

    if not isinstance(plan_id, int) or not isinstance(price_monthly, int):
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Plan ID and monthly price are required.",
                }
            ),
            400,
        )

    if listing_limit == "":
        listing_limit = None
    if listing_limit is not None and not isinstance(listing_limit, int):
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Listing limit must be a number or blank.",
                }
            ),
            400,
        )

    db = get_db()
    cursor = db.execute(
        """
        UPDATE subscription_plans
        SET price_monthly = ?, listing_limit = ?
        WHERE id = ?
        """,
        (price_monthly, listing_limit, plan_id),
    )
    if cursor.rowcount == 0:
        return jsonify({"error": "PLAN_NOT_FOUND", "message": "Plan not found."}), 404

    db.commit()
    return jsonify({"message": "Plan updated."})


@bp.post("/api/importer/products")
def create_importer_product():
    importer, error_response = require_verified_importer()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    errors, cleaned = validate_product_payload(payload)
    if errors:
        return (
            jsonify(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Product details are invalid.",
                    "fields": errors,
                }
            ),
            400,
        )

    db = get_db()
    entitlements = get_importer_entitlements(importer["id"])
    product_count = count_importer_products(importer["id"])
    listing_limit = entitlements["listingLimit"]

    if listing_limit is not None and product_count >= listing_limit:
        return (
            jsonify(
                {
                    "error": "SUBSCRIPTION_LIMIT_REACHED",
                    "message": (
                        f"Your {entitlements['planName']} plan allows "
                        f"{listing_limit} products. Upgrade your subscription to add more."
                    ),
                }
            ),
            403,
        )

    try:
        cursor = db.execute(
            """
            INSERT INTO products (
                importer_id,
                name,
                brand,
                batch_number,
                expiry_date
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                importer["id"],
                cleaned["name"],
                cleaned["brand"],
                cleaned["batch_number"],
                cleaned["expiry_date"],
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return (
            jsonify(
                {
                    "error": "DUPLICATE_BATCH_NUMBER",
                    "message": "A product with this batch number already exists for this importer.",
                }
            ),
            409,
        )

    product = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify(serialize_product(product)), 201
