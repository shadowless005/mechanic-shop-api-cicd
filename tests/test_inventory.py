import unittest

from application import create_app
from application.extensions import db
from config import TestingConfig


class TestInventory(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

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
