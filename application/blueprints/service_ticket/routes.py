from flask import request, jsonify
from sqlalchemy import select
from marshmallow import ValidationError

from application.extensions import db
from application.models import ServiceTicket, Mechanic, Inventory

from . import service_ticket_bp
from .schemas import service_ticket_schema, service_tickets_schema


# CREATE SERVICE TICKET
@service_ticket_bp.route("/", methods=["POST"])
def create_service_ticket():
    try:
        ticket_data = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_ticket = ServiceTicket(**ticket_data)

    db.session.add(new_ticket)
    db.session.commit()

    return service_ticket_schema.jsonify(new_ticket), 201


# GET ALL SERVICE TICKETS
@service_ticket_bp.route("/", methods=["GET"])
def get_service_tickets():
    query = select(ServiceTicket)
    tickets = db.session.execute(query).scalars().all()

    return service_tickets_schema.jsonify(tickets), 200


# ASSIGN MECHANIC TO A SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/assign-mechanic/<int:mechanic_id>",
    methods=["PUT"]
)
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTicket, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not ticket:
        return jsonify({"error": "Service ticket not found."}), 404

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    if mechanic not in ticket.mechanics:
        ticket.mechanics.append(mechanic)
        db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200


# REMOVE MECHANIC FROM A SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/remove-mechanic/<int:mechanic_id>",
    methods=["PUT"]
)
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTicket, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not ticket:
        return jsonify({"error": "Service ticket not found."}), 404

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    if mechanic in ticket.mechanics:
        ticket.mechanics.remove(mechanic)
        db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200

# EDIT MECHANICS ON SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/edit",
    methods=["PUT"]     
)
def edit_ticket_mechanics(ticket_id):
    ticket = db.session.get(ServiceTicket, ticket_id)

    if not ticket:
        return jsonify({"error": "Service ticket not found."}), 404

    data = request.json

    add_ids = data.get("add_ids", [])
    remove_ids = data.get("remove_ids", [])

    for mechanic_id in add_ids:
        mechanic = db.session.get(Mechanic, mechanic_id)
        
        if mechanic and mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)

    for mechanic_id in remove_ids:
        mechanic = db.session.get(Mechanic, mechanic_id)

        if mechanic and mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)

    db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200

# ADD INVENTORY ITEM TO SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/add-inventory/<int:inventory_id>",
    methods=["PUT"]
)
def add_inventory_to_ticket(ticket_id, inventory_id):
    ticket = db.session.get(ServiceTicket, ticket_id)
    inventory_item = db.session.get(Inventory, inventory_id)

    if not ticket:
        return jsonify({"error": "Service ticket not found."}), 404

    if not inventory_item:
        return jsonify({"error": "Inventory item not found."}), 404

    if inventory_item not in ticket.inventory:
        ticket.inventory.append(inventory_item)
        db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200