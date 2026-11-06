from marshmallow import fields
from application.extensions import ma
from application.models import ServiceTicket


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    mechanics = fields.Function(lambda ticket: [item.id for item in ticket.mechanics], dump_only=True)
    inventory = fields.Function(lambda ticket: [item.id for item in ticket.inventory], dump_only=True)

    class Meta:
        dump_only = ("id",)
        model = ServiceTicket
        include_fk = True


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)