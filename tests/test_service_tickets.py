import unittest

from werkzeug.security import generate_password_hash

from application import create_app
from application.extensions import db
from application.models import Customer, ServiceTicket
from application.utils.util import encode_token
from config import TestingConfig



class TestServiceTickets(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            staff = Customer(
                name="Service Ticket Staff",
                email="ticket-staff@example.com",
                phone="4075559301",
                address="123 Shop Street",
                password=generate_password_hash("staff-test-password"),
                is_staff=True
            )
            db.session.add(staff)
            db.session.commit()

            token = encode_token(staff.id)

        self.client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_service_ticket(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        response = self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(
            data["description"],
            "Replace front brake pads"
        )
        self.assertEqual(data["vin"], "1HGCM82633A123456")
        self.assertEqual(data["customer_id"], customer_id)

    def test_get_all_service_tickets(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        response = self.client.get(
            "/service-tickets/"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["description"],
            "Replace front brake pads"
        )
        self.assertEqual(
            data[0]["customer_id"],
            customer_id
        )

    def test_assign_mechanic_to_service_ticket(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        ticket_response = self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        ticket_id = ticket_response.get_json()["id"]

        mechanic_payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        mechanic_response = self.client.post(
            "/mechanics/",
            json=mechanic_payload
        )

        mechanic_id = mechanic_response.get_json()["id"]

        response = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)

            self.assertIsNotNone(ticket)
            self.assertIn(
                mechanic_id,
                [mechanic.id for mechanic in ticket.mechanics]
            )
        

    def test_remove_mechanic_from_service_ticket(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        ticket_response = self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        ticket_id = ticket_response.get_json()["id"]

        mechanic_payload = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        mechanic_response = self.client.post(
            "/mechanics/",
            json=mechanic_payload
        )

        mechanic_id = mechanic_response.get_json()["id"]

        self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )

        response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}"
        )

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)
            self.assertEqual(len(ticket.mechanics), 0)

    def test_edit_ticket_mechanics(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        ticket_response = self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        ticket_id = ticket_response.get_json()["id"]

        mechanic_one = {
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "phone": "4075552222",
            "address": "789 Garage Road",
            "salary": 65000
        }

        mechanic_two = {
            "name": "Sarah Lee",
            "email": "sarah@example.com",
            "phone": "4075553333",
            "address": "456 Repair Ave",
            "salary": 62000
        }

        mechanic_one_response = self.client.post(
            "/mechanics/",
            json=mechanic_one
        )

        mechanic_two_response = self.client.post(
            "/mechanics/",
            json=mechanic_two
        )

        mechanic_one_id = mechanic_one_response.get_json()["id"]
        mechanic_two_id = mechanic_two_response.get_json()["id"]

        self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_one_id}"
        )

        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={
                "add_ids": [mechanic_two_id],
                "remove_ids": [mechanic_one_id]
            }
        )

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)

            mechanic_ids = [
                mechanic.id
                for mechanic in ticket.mechanics
            ]

            self.assertIn(mechanic_two_id, mechanic_ids)
            self.assertNotIn(mechanic_one_id, mechanic_ids)     
    def test_add_inventory_to_service_ticket(self):
        customer_payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        customer_response = self.client.post(
            "/customers/",
            json=customer_payload
        )

        customer_id = customer_response.get_json()["id"]

        ticket_payload = {
            "description": "Replace front brake pads",
            "vin": "1HGCM82633A123456",
            "customer_id": customer_id
        }

        ticket_response = self.client.post(
            "/service-tickets/",
            json=ticket_payload
        )

        ticket_id = ticket_response.get_json()["id"]

        inventory_payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        inventory_response = self.client.post(
            "/inventory/",
            json=inventory_payload
        )
        self.assertEqual(
            inventory_response.status_code,
            201,
            inventory_response.get_json()
        )
        inventory_id = inventory_response.get_json()["id"]

        response = self.client.put(
            f"/service-tickets/{ticket_id}/add-inventory/{inventory_id}"
        )

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)

            inventory_ids = [
                item.id
                for item in ticket.inventory
            ]

            self.assertIn(inventory_id, inventory_ids)       

    def test_service_ticket_not_found(self):
        response = self.client.put(
            "/service-tickets/9999/assign-mechanic/1"
        )

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"],
            "Service ticket not found."
        )                        

    def test_edit_mechanics_rejects_invalid_requests(self):
        from application.models import Customer

        with self.app.app_context():
            customer = Customer(
                name="Validation Customer",
                email="validation@example.com",
                phone="4075559101",
                address="123 Test Street",
                password="unused-test-fixture"
            )
            db.session.add(customer)
            db.session.flush()

            ticket = ServiceTicket(
                description="Validation test",
                vin="1HGCM82633A123456",
                customer_id=customer.id
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        url = f"/service-tickets/{ticket_id}/edit"

        invalid_requests = [
            ("empty body", {}),
            ("malformed JSON", {
                "data": "{",
                "content_type": "application/json"
            }),
            ("array body", {"json": []}),
            ("non-list IDs", {"json": {"add_ids": "1"}}),
            ("string ID", {"json": {"add_ids": ["1"]}}),
            ("boolean ID", {"json": {"add_ids": [True]}}),
            ("conflicting IDs", {
                "json": {"add_ids": [1], "remove_ids": [1]}
            })
        ]

        for label, request_options in invalid_requests:
            with self.subTest(case=label):
                response = self.client.put(url, **request_options)

                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)
            self.assertEqual(len(ticket.mechanics), 0)

    def test_edit_mechanics_missing_id_leaves_assignments_unchanged(self):
        from application.models import Customer, Mechanic

        with self.app.app_context():
            customer = Customer(
                name="Missing ID Customer",
                email="missing-id@example.com",
                phone="4075559102",
                address="456 Test Street",
                password="unused-test-fixture"
            )
            mechanic = Mechanic(
                name="Demo Mechanic",
                email="demo-mechanic@example.com",
                phone="4075559103",
                address="789 Garage Road",
                salary=65000
            )
            db.session.add_all([customer, mechanic])
            db.session.flush()

            ticket = ServiceTicket(
                description="Missing mechanic test",
                vin="1HGCM82633A123457",
                customer_id=customer.id
            )
            db.session.add(ticket)
            db.session.commit()

            ticket_id = ticket.id
            mechanic_id = mechanic.id
            missing_id = mechanic_id + 1000

        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={
                "add_ids": [mechanic_id, missing_id],
                "remove_ids": []
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json()["error"],
            f"Mechanic id: {missing_id} not found."
        )

        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, ticket_id)
            self.assertEqual(len(ticket.mechanics), 0)    