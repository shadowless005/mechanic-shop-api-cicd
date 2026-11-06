from application.extensions import db
from application.models import Customer
from application.utils.util import encode_token
from werkzeug.security import generate_password_hash


def make_customer(label, staff=False):
    customer = Customer(name=label, email=f"{label}@example.com",
                        phone=label, address="123 Test Street",
                        password=generate_password_hash("test-password"), is_staff=staff)
    db.session.add(customer)
    db.session.commit()
    return customer.id, {"Authorization": f"Bearer {encode_token(customer.id)}"}
