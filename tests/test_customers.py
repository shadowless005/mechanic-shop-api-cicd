import unittest
from auth_helpers import make_customer
from application.utils.util import encode_token

from werkzeug.security import check_password_hash
from application.models import Customer

from application import create_app
from application.extensions import db
from config import TestingConfig


class TestCustomers(unittest.TestCase):

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
            db.engine.dispose()

    def test_create_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        response = self.client.post(
            "/customers/",
            json=payload
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["name"], "John Doe")
        self.assertEqual(data["email"], "john@example.com")

    def test_get_all_customers(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        with self.app.app_context():
            customer = db.session.execute(db.select(Customer)).scalar_one()
            customer.is_staff = True
            db.session.commit()
            headers = {"Authorization": f"Bearer {encode_token(customer.id)}"}
        response = self.client.get("/customers/", headers=headers)

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "John Doe")
        self.assertEqual(data[0]["email"], "john@example.com")
    
    def test_get_customer_by_id(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        create_response = self.client.post(
            "/customers/",
            json=payload
        )

        customer_id = create_response.get_json()["id"]

        with self.app.app_context():
            headers = {"Authorization": f"Bearer {encode_token(customer_id)}"}
        response = self.client.get(
            f"/customers/{customer_id}", headers=headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["id"], customer_id)
        self.assertEqual(data["name"], "John Doe")
        self.assertEqual(data["email"], "john@example.com")
        
    def test_login_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        credentials = {
            "email": "john@example.com",
            "password": "password123"
        }

        response = self.client.post(
            "/customers/login",
            json=credentials
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Successfully Logged In")
        self.assertIn("auth_token", data)


    def test_update_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        login_response = self.client.post(
            "/customers/login",
            json={
                "email": "john@example.com",
                "password": "password123"
            }
        )

        token = login_response.get_json()["auth_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        update_payload = {
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "456 Oak Street",
            "password": "password123"
        }

        response = self.client.put(
            "/customers/",
            json=update_payload,
            headers=headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["name"], "John Smith")
        self.assertEqual(data["address"], "456 Oak Street")        

    def test_delete_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        login_response = self.client.post(
            "/customers/login",
            json={
                "email": "john@example.com",
                "password": "password123"
            }
        )

        token = login_response.get_json()["auth_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = self.client.delete(
            "/customers/",
            headers=headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("successfully deleted", data["message"])

    def test_get_my_tickets(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        login_response = self.client.post(
            "/customers/login",
            json={
                "email": "john@example.com",
                "password": "password123"
            }
        )

        token = login_response.get_json()["auth_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = self.client.get(
            "/customers/my-tickets",
            headers=headers
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data, [])

    def test_login_invalid_credentials(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "4075551234",
            "address": "123 Main St",
            "password": "password123"
        }

        self.client.post(
            "/customers/",
            json=payload
        )

        response = self.client.post(
            "/customers/login",
            json={
                "email": "john@example.com",
                "password": "wrongpassword"
            }
        )

        self.assertEqual(response.status_code, 401)

        data = response.get_json()

        self.assertEqual(
            data["message"],
            "Invalid email or password"
        )

    def test_get_customer_not_found(self):
        with self.app.app_context():
            _, headers = make_customer("missing-reader", staff=True)
        response = self.client.get("/customers/9999", headers=headers)

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"],
            "Customer not found."
        )       

    def test_customer_password_is_hashed(self):
        payload = {
            "name": "Hash Test",
            "email": "hash@example.com",
            "phone": "4075559001",
            "address": "123 Test Street",
            "password": "original-password"
        }

        response = self.client.post("/customers/", json=payload)

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertNotIn("password", data)

        with self.app.app_context():
            customer = db.session.get(Customer, data["id"])

            self.assertNotEqual(customer.password, payload["password"])
            self.assertTrue(
                check_password_hash(customer.password, payload["password"])
            )

    def test_updated_password_is_hashed_and_used_for_login(self):
        payload = {
            "name": "Password Update",
            "email": "password-update@example.com",
            "phone": "4075559002",
            "address": "456 Test Street",
            "password": "original-password"
        }

        created = self.client.post("/customers/", json=payload)
        self.assertEqual(created.status_code, 201)
        customer_id = created.get_json()["id"]

        login = self.client.post(
            "/customers/login",
            json={
                "email": payload["email"],
                "password": payload["password"]
            }
        )
        self.assertEqual(login.status_code, 200)
        token = login.get_json()["auth_token"]

        updated_payload = {
            **payload,
            "password": "replacement-password"
        }

        response = self.client.put(
            "/customers/",
            json=updated_payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

        with self.app.app_context():
            customer = db.session.get(Customer, customer_id)

            self.assertNotEqual(customer.password, "replacement-password")
            self.assertTrue(
                check_password_hash(customer.password, "replacement-password")
            )
            self.assertFalse(
                check_password_hash(customer.password, "original-password")
            )

        old_login = self.client.post(
            "/customers/login",
            json={
                "email": payload["email"],
                "password": "original-password"
            }
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/customers/login",
            json={
                "email": payload["email"],
                "password": "replacement-password"
            }
        )
        self.assertEqual(new_login.status_code, 200)
        self.assertIn("auth_token", new_login.get_json())
