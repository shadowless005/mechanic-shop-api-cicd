from application.extensions import ma
from application.models import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_only = ("password",)
        

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

login_schema = CustomerSchema(only=("email", "password"))
