from flask import request, jsonify, g
from sqlalchemy import select
from marshmallow import ValidationError

from application.utils.util import staff_required, token_required
from application.extensions import db
from application.models import ServiceTicket, Mechanic, Inventory, Customer

from . import service_ticket_bp
from .schemas import service_ticket_schema, service_tickets_schema


# CREATE SERVICE TICKET
@service_ticket_bp.route("/", methods=["POST"])
@token_required
def create_service_ticket(authenticated_customer_id):
    try:
        ticket_data = service_ticket_schema.load(request.get_json(silent=True))
    except ValidationError as e:
        return jsonify(e.messages), 400

    if not g.current_customer.is_staff and ticket_data["customer_id"] != authenticated_customer_id:
        return jsonify({"message": "You can only create tickets for your own account."}), 403

    if db.session.get(Customer, ticket_data["customer_id"]) is None:
        return jsonify({"error": "Customer not found."}), 404

    new_ticket = ServiceTicket(**ticket_data)

    db.session.add(new_ticket)
    db.session.commit()

    return service_ticket_schema.jsonify(new_ticket), 201


# GET ALL SERVICE TICKETS
@service_ticket_bp.route("/", methods=["GET"])
@token_required
def get_service_tickets(authenticated_customer_id):
    query = select(ServiceTicket).order_by(ServiceTicket.id)
    if not g.current_customer.is_staff:
        query = query.where(ServiceTicket.customer_id == authenticated_customer_id)
    tickets = db.session.execute(query).scalars().all()

    return service_tickets_schema.jsonify(tickets), 200


# ASSIGN MECHANIC TO A SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/assign-mechanic/<int:mechanic_id>",
    methods=["PUT"]
)
@staff_required
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTicket, ticket_id)

    if ticket is None:
        return jsonify({"error": "Service ticket not found."}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)

    if mechanic is None:
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
@staff_required
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTicket, ticket_id)

    if ticket is None:
        return jsonify({"error": "Service ticket not found."}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)

    if mechanic is None:
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
@staff_required
def edit_ticket_mechanics(ticket_id):
    ticket = db.session.get(ServiceTicket, ticket_id)

    if ticket is None:
        return jsonify({"error": "Service ticket not found."}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    add_ids = data.get("add_ids", [])
    remove_ids = data.get("remove_ids", [])

    if not isinstance(add_ids, list) or not isinstance(remove_ids, list):
        return jsonify({
            "error": "add_ids and remove_ids must be lists."
        }), 400

    if any(type(value) is not int for value in add_ids + remove_ids):
        return jsonify({"error": "Mechanic IDs must be integers."}), 400

    if set(add_ids) & set(remove_ids):
        return jsonify({
            "error": "A mechanic cannot be added and removed in the same request."
        }), 400

    # Validate every ID before changing any assignments.
    mechanics_by_id = {}

    for mechanic_id in sorted(set(add_ids + remove_ids)):
        mechanic = db.session.get(Mechanic, mechanic_id)

        if mechanic is None:
            return jsonify({
                "error": f"Mechanic id: {mechanic_id} not found."
            }), 404

        mechanics_by_id[mechanic_id] = mechanic

    for mechanic_id in add_ids:
        mechanic = mechanics_by_id[mechanic_id]

        if mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)

    for mechanic_id in remove_ids:
        mechanic = mechanics_by_id[mechanic_id]

        if mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)

    db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200


# ADD INVENTORY ITEM TO SERVICE TICKET
@service_ticket_bp.route(
    "/<int:ticket_id>/add-inventory/<int:inventory_id>",
    methods=["PUT"]
)
@staff_required
def add_inventory_to_ticket(ticket_id, inventory_id):
    ticket = db.session.get(ServiceTicket, ticket_id)

    if ticket is None:
        return jsonify({"error": "Service ticket not found."}), 404

    inventory_item = db.session.get(Inventory, inventory_id)

    if inventory_item is None:
        return jsonify({"error": "Inventory item not found."}), 404

    if inventory_item not in ticket.inventory:
        ticket.inventory.append(inventory_item)
        db.session.commit()

    return service_ticket_schema.jsonify(ticket), 200
