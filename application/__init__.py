from flask import Flask
from .extensions import db, ma, limiter, cache
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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

    return app