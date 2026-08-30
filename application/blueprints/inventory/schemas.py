from application.extensions import ma
from application.models import Inventory


class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory


inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)