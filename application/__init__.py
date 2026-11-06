from pathlib import Path

import yaml
from flask import Flask, jsonify, request
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

from .extensions import db, ma, limiter, cache
from config import Config


SWAGGER_URL = "/api/docs"
API_URL = "/api/swagger.json"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Mechanic Shop API"
    }
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config.get("PRODUCTION"):
        if not app.config.get("SQLALCHEMY_DATABASE_URI") or not app.config.get("SECRET_KEY"):
            raise RuntimeError("Production requires DATABASE_URL and SECRET_KEY environment variables.")
        if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
            raise RuntimeError("Production requires a PostgreSQL DATABASE_URL.")

    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    from . import models

    if app.config.get("AUTO_CREATE_TABLES", True):
        with app.app_context():
            db.create_all()

    from application.blueprints.customer import customer_bp
    from application.blueprints.mechanic import mechanic_bp
    from application.blueprints.service_ticket import service_ticket_bp
    from application.blueprints.inventory import inventory_bp

    app.register_blueprint(
        customer_bp,
        url_prefix="/customers"
    )

    app.register_blueprint(
        mechanic_bp,
        url_prefix="/mechanics"
    )

    app.register_blueprint(
        service_ticket_bp,
        url_prefix="/service-tickets"
    )

    app.register_blueprint(
        inventory_bp,
        url_prefix="/inventory"
    )

    @app.route("/api/swagger.json", methods=["GET"])
    def swagger_spec():
        # Use the existing YAML documentation as Flask-Swagger's template.
        swagger_path = Path(app.root_path) / "static" / "swagger.yaml"

        with swagger_path.open(encoding="utf-8") as file:
            template = yaml.safe_load(file)

        # Production YAML keeps the deployed host and HTTPS. Local demos use
        # this server so a local Try-it-out never writes to the live database.
        if not app.config.get("PRODUCTION"):
            template["host"] = request.host
            template["schemes"] = [request.scheme]
        specification = swagger(app, template=template)
        return jsonify(specification)

    app.register_blueprint(
        swaggerui_blueprint,
        url_prefix=SWAGGER_URL
    )

    @app.route("/health", methods=["GET"])
    def health():
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        try:
            # Also verifies the migration needed by the new customer model.
            db.session.execute(text("SELECT is_staff FROM customers LIMIT 1"))
            return jsonify({"status": "ok", "database": "connected"}), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"status": "unavailable", "database": "unavailable"}), 503

    from .cli import create_staff, upgrade_db, reset_password
    app.cli.add_command(create_staff)
    app.cli.add_command(upgrade_db)
    app.cli.add_command(reset_password)

    return app
