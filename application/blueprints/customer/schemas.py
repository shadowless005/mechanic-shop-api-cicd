from application.extensions import ma
from application.models import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        dump_only = ("id",)
        model = Customer
        load_only = ("password",)
        exclude = ("is_staff",)
        

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

login_schema = CustomerSchema(only=("email", "password"))
