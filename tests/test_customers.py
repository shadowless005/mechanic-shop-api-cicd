import unittest


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

        response = self.client.get("/customers/")

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

        response = self.client.get(
            f"/customers/{customer_id}"
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
        response = self.client.get("/customers/9999")

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"],
            "Customer not found."
        )       

