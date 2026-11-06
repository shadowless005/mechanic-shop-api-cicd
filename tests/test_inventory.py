import unittest

from application import create_app
from application.extensions import db
from config import TestingConfig

from werkzeug.security import generate_password_hash
from application.models import Customer, Inventory
from application.utils.util import encode_token


class TestInventory(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            staff = Customer(
                name="Inventory Staff",
                email="inventory-staff@example.com",
                phone="4075559201",
                address="123 Shop Street",
                password=generate_password_hash("staff-test-password"),
                is_staff=True
            )
            db.session.add(staff)
            db.session.commit()

            token = encode_token(staff.id)

        # Existing inventory tests exercise authorized staff requests.
        self.client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_inventory_item(self):
        payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        response = self.client.post(
            "/inventory/",
            json=payload
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["name"], "Brake Pads")
        self.assertEqual(data["price"], 49.99)

    def test_get_all_inventory_items(self):
        payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        self.client.post(
            "/inventory/",
            json=payload
        )

        response = self.client.get("/inventory/")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Brake Pads")
        self.assertEqual(data[0]["price"], 49.99)     

    def test_get_inventory_item_by_id(self):
        payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        create_response = self.client.post(
            "/inventory/",
            json=payload
        )

        inventory_id = create_response.get_json()["id"]

        response = self.client.get(
            f"/inventory/{inventory_id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["id"], inventory_id)
        self.assertEqual(data["name"], "Brake Pads")
        self.assertEqual(data["price"], 49.99)      
    def test_update_inventory_item(self):
        payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        create_response = self.client.post(
            "/inventory/",
            json=payload
        )

        inventory_id = create_response.get_json()["id"]

        update_payload = {
            "price": 59.99
        }

        response = self.client.put(
            f"/inventory/{inventory_id}",
            json=update_payload
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["name"], "Brake Pads")
        self.assertEqual(data["price"], 59.99)

    def test_delete_inventory_item(self):
        payload = {
            "name": "Brake Pads",
            "price": 49.99
        }

        create_response = self.client.post(
            "/inventory/",
            json=payload
        )

        inventory_id = create_response.get_json()["id"]

        response = self.client.delete(
            f"/inventory/{inventory_id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(
            data["message"],
            "Inventory item deleted successfully."
        )        
    def test_inventory_item_not_found(self):
        response = self.client.get("/inventory/9999")

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"],
            "Inventory item not found."
        )
    def test_inventory_writes_require_staff(self):
        created = self.client.post(
            "/inventory/",
            json={"name": "Brake Pads", "price": 49.99}
        )
        self.assertEqual(created.status_code, 201)
        inventory_id = created.get_json()["id"]

        with self.app.app_context():
            customer = Customer(
                name="Regular Customer",
                email="regular@example.com",
                phone="4075559202",
                address="456 Test Street",
                password=generate_password_hash("customer-test-password")
            )
            db.session.add(customer)
            db.session.commit()
            customer_token = encode_token(customer.id)

        # A fresh client has no default staff authorization.
        client = self.app.test_client()

        cases = [
            ("anonymous", {}, 401),
            (
                "regular customer",
                {"Authorization": f"Bearer {customer_token}"},
                403
            )
        ]

        for label, headers, expected_status in cases:
            for method, url, payload in [
                (
                    "POST",
                    "/inventory/",
                    {"name": "Unauthorized Item", "price": 10}
                ),
                (
                    "PUT",
                    f"/inventory/{inventory_id}",
                    {"price": 999}
                ),
                (
                    "DELETE",
                    f"/inventory/{inventory_id}",
                    None
                )
            ]:
                with self.subTest(user=label, method=method):
                    response = client.open(
                        url,
                        method=method,
                        headers=headers,
                        json=payload
                    )
                    self.assertEqual(
                        response.status_code,
                        expected_status
                    )

        with self.app.app_context():
            item = db.session.get(Inventory, inventory_id)
            self.assertIsNotNone(item)
            self.assertEqual(item.price, 49.99)
            self.assertEqual(Inventory.query.count(), 1)
    
