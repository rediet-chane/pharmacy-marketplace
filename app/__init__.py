from flask import Flask

from .db import close_db, init_db
from .routes import bp


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE="pharmacy_marketplace.sqlite3",
        CHAPA_SECRET_KEY="",
        CHAPA_INITIALIZE_URL="https://api.chapa.co/v1/transaction/initialize",
    )

    app.teardown_appcontext(close_db)
    app.register_blueprint(bp)

    with app.app_context():
        init_db()

    return app
