from flask import request, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from application.utils.util import staff_required
from marshmallow import ValidationError

from application.extensions import db
from application.models import Mechanic

from . import mechanic_bp
from .schemas import mechanic_schema, mechanics_schema

@mechanic_bp.route("/", methods=["POST"])
@staff_required
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.get_json(silent=True))
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_mechanic = Mechanic(**mechanic_data)

    db.session.add(new_mechanic)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone is already in use, or the record is still referenced."}), 409

    return mechanic_schema.jsonify(new_mechanic), 201


@mechanic_bp.route("/", methods=["GET"])
def get_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()

    return mechanics_schema.jsonify(mechanics), 200

# Get Mechanics ORDERED BY MOST SERVICE TICKETS 
@mechanic_bp.route("/most-tickets", methods=["GET"])
def get_mechanics_by_most_tickets():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()

    mechanics.sort(
        key=lambda mechanic: len(mechanic.service_tickets),
        reverse=True
    )

    return mechanics_schema.jsonify(mechanics), 200


@mechanic_bp.route("/<int:mechanic_id>", methods=["PUT"])
@staff_required
def update_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    try:
        mechanic_data = mechanic_schema.load(request.get_json(silent=True))
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone is already in use, or the record is still referenced."}), 409

    return mechanic_schema.jsonify(mechanic), 200


@mechanic_bp.route("/<int:mechanic_id>", methods=["DELETE"])
@staff_required
def delete_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    db.session.delete(mechanic)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone is already in use, or the record is still referenced."}), 409

    return jsonify({
        "message": f"Mechanic id: {mechanic_id} successfully deleted."
    }), 200
