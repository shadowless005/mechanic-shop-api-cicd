from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask
from .extensions import db, ma, limiter, cache
from config import Config

SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger.yaml"

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

    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    from . import models

    with app.app_context():
        db.create_all()

    from application.blueprints.customer import customer_bp

    app.register_blueprint(
        customer_bp,
        url_prefix="/customers"
    )

    from application.blueprints.mechanic import mechanic_bp

    app.register_blueprint(
        mechanic_bp,
        url_prefix="/mechanics"
    )

    from application.blueprints.service_ticket import service_ticket_bp

    app.register_blueprint(
        service_ticket_bp,
        url_prefix="/service-tickets"
    )

    from application.blueprints.inventory import inventory_bp

    app.register_blueprint(
        inventory_bp,
        url_prefix="/inventory"
    )

    app.register_blueprint(
    swaggerui_blueprint,
    url_prefix=SWAGGER_URL
)

    return app