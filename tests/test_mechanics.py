import unittest
from auth_helpers import make_customer

from application import create_app
from application.extensions import db
from config import TestingConfig


class TestMechanics(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            _, headers = make_customer("mechanic-staff", staff=True)
        self.client.environ_base["HTTP_AUTHORIZATION"] = headers["Authorization"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_mechanic(self):
        payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        response = self.client.post(
            "/mechanics/",
            json=payload
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["name"], "Mike Johnson")
        self.assertEqual(data["email"], "mike@example.com")

    def test_get_all_mechanics(self):
        payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        self.client.post(
            "/mechanics/",
            json=payload
        )

        response = self.client.get("/mechanics/")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Mike Johnson")
        self.assertEqual(data[0]["email"], "mike@example.com")
    def test_get_mechanics_by_most_tickets(self):
        from application.models import Customer, Mechanic, ServiceTicket

        with self.app.app_context():
            customer = Customer(
                name="Demo Customer",
                email="demo@example.com",
                phone="4075551000",
                address="123 Main St",
                password="demo-password"
            )

            mechanic_one = Mechanic(
                name="Mike Johnson",
                email="mike@example.com",
                phone="4075552222",
                address="789 Garage Road",
                salary=65000
            )

            mechanic_two = Mechanic(
                name="Sarah Lee",
                email="sarah@example.com",
                phone="4075553333",
                address="456 Repair Ave",
                salary=62000
            )

            db.session.add_all([customer, mechanic_one, mechanic_two])
            db.session.flush()

            ticket_one = ServiceTicket(
                description="Replace brake pads",
                vin="1HGCM82633A123456",
                customer_id=customer.id
            )

            ticket_two = ServiceTicket(
                description="Change oil",
                vin="1HGCM82633A123457",
                customer_id=customer.id
            )

            # Mike has one ticket; Sarah has two.
            ticket_one.mechanics.extend([mechanic_one, mechanic_two])
            ticket_two.mechanics.append(mechanic_two)

            db.session.add_all([ticket_one, ticket_two])
            db.session.commit()

            expected_order = [mechanic_two.id, mechanic_one.id]

        response = self.client.get("/mechanics/most-tickets")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(len(data), 2)
        self.assertEqual(
            [mechanic["id"] for mechanic in data],
            expected_order
        )

    def test_update_mechanic(self):
        payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        create_response = self.client.post(
            "/mechanics/",
            json=payload
        )

        mechanic_id = create_response.get_json()["id"]

        update_payload = {
            "name": "Michael Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "999 Updated Garage Road",
            "salary": 70000
        }

        response = self.client.put(
            f"/mechanics/{mechanic_id}",
            json=update_payload
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["name"], "Michael Johnson")
        self.assertEqual(data["address"], "999 Updated Garage Road")
        self.assertEqual(data["salary"], 70000.0)  

    def test_delete_mechanic(self):
        payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        create_response = self.client.post(
            "/mechanics/",
            json=payload
        )

        mechanic_id = create_response.get_json()["id"]

        response = self.client.delete(
            f"/mechanics/{mechanic_id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn(
            "successfully deleted",
            data["message"]
        )   
    def test_update_mechanic_not_found(self):
        update_payload = {
            "name": "Michael Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "999 Updated Garage Road",
            "salary": 70000
        }

        response = self.client.put(
            "/mechanics/9999",
            json=update_payload
        )

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"],
            "Mechanic not found."
        )        