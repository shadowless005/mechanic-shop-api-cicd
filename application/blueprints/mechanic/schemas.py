from application.extensions import ma
from application.models import Mechanic


class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        dump_only = ("id",)
        model = Mechanic


mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)