from flask import request, jsonify
from sqlalchemy import select
from marshmallow import ValidationError

from application.extensions import db
from application.models import Inventory

from . import inventory_bp
from .schemas import inventory_schema, inventories_schema

# CREATE INVENTORY ITEM
@inventory_bp.route("/", methods=["POST"])
def create_inventory_item():
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_inventory_item = Inventory(**inventory_data)

    db.session.add(new_inventory_item)
    db.session.commit()

    return inventory_schema.jsonify(new_inventory_item), 201

# GET ALL INVENTORY ITEMS
@inventory_bp.route("/", methods=["GET"])
def get_inventory_items():
    query = select(Inventory)
    inventory_items = db.session.execute(query).scalars().all()

    return inventories_schema.jsonify(inventory_items), 200

# GET ONE INVENTORY ITEM
@inventory_bp.route("/<int:inventory_id>", methods=["GET"])
def get_inventory_item(inventory_id):
    inventory_item = db.session.get(Inventory, inventory_id)

    if not inventory_item:
        return jsonify({"error": "Inventory item not found."}), 404

    return inventory_schema.jsonify(inventory_item), 200

# UPDATE INVENTORY ITEM
@inventory_bp.route("/<int:inventory_id>", methods=["PUT"])
def update_inventory_item(inventory_id):
    inventory_item = db.session.get(Inventory, inventory_id)

    if not inventory_item:
        return jsonify({"error": "Inventory item not found."}), 404

    try:
        inventory_data = inventory_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in inventory_data.items():
        setattr(inventory_item, key, value)

    db.session.commit()

    return inventory_schema.jsonify(inventory_item), 200

# DELETE INVENTORY ITEM
@inventory_bp.route("/<int:inventory_id>", methods=["DELETE"])
def delete_inventory_item(inventory_id):
    inventory = db.session.get(Inventory, inventory_id)

    if not inventory:
        return jsonify({"error": "Inventory item not found."}), 404

    db.session.delete(inventory)
    db.session.commit()

    return jsonify({"message": "Inventory item deleted successfully."}), 200