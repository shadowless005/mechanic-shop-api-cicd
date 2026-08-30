from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db, limiter, cache
from application.models import Customer

from . import customer_bp
from .schemas import customer_schema, customers_schema, login_schema
from application.utils.util import encode_token, token_required



# CREATE CUSTOMER
@customer_bp.route("/", methods=["POST"])
@limiter.limit("3 per hour")
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(**customer_data)

    db.session.add(new_customer)
    db.session.commit()

    return customer_schema.jsonify(new_customer), 201


# GET ALL CUSTOMERS
@customer_bp.route("/", methods=["GET"])
@cache.cached(timeout=60)
def get_customers():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    query = select(Customer)
    customers = db.session.execute(query.offset((page - 1) * per_page).limit(per_page)).scalars().all()

    return customers_schema.jsonify(customers), 200


# GET ONE CUSTOMER
@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    return customer_schema.jsonify(customer), 200


# UPDATE LOGGED-IN CUSTOMER
@customer_bp.route("/", methods=["PUT"])
@token_required
def update_customer(customer_id):
    customer = db.session.get(Customer, int(customer_id))

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()

    return customer_schema.jsonify(customer), 200


# DELETE CUSTOMER
@customer_bp.route("/", methods=["DELETE"])
@token_required
def delete_customer(customer_id):
    customer = db.session.get(Customer, int(customer_id))

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    db.session.delete(customer)
    db.session.commit()

    return jsonify({
        "message": f"Customer id: {customer_id} successfully deleted."
    }), 200


# LOGIN CUSTOMER
@customer_bp.route("/login", methods=["POST"])
def login():
    try:
        credentials = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    email = credentials["email"]
    password = credentials["password"]

    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalar_one_or_none()

    if customer and customer.password == password:
        auth_token = encode_token(customer.id)

        return jsonify({
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }), 200

    return jsonify({
        "message": "Invalid email or password"
    }), 401

# GET LOGGED-IN CUSTOMER'S SERVICE TICKETS
@customer_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets(customer_id):
    customer = db.session.get(Customer, int(customer_id))

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    tickets = customer.service_tickets

    return jsonify([
        {
            "id": ticket.id,
            "description": ticket.description,
            "vin": ticket.vin,
            "customer_id": ticket.customer_id
        }
        for ticket in tickets
    ]), 200