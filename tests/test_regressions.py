import unittest
from application.utils.util import encode_token
from application import create_app
from application.extensions import db, cache
from application.models import Customer
from config import TestingConfig


class TestRegressions(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            cache.clear()
            for n in range(2):
                db.session.add(Customer(name=f"Demo {n}", email=f"demo{n}@example.com",
                                        phone=f"555000{n}", address="Demo Street", password="demo", is_staff=True))
            db.session.commit()
            token = encode_token(db.session.execute(db.select(Customer)).scalars().first().id)
        self.client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            cache.clear()
            db.engine.dispose()

    def test_cached_customer_pages_are_distinct(self):
        first = self.client.get("/customers/?page=1&per_page=1")
        second = self.client.get("/customers/?page=2&per_page=1")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.json[0]["id"], second.json[0]["id"])
        self.assertEqual(self.client.get("/customers/?page=0").status_code, 400)

    def test_rejects_non_bearer_authorization(self):
        response = self.client.get("/customers/my-tickets", headers={"Authorization": "Basic fake"})
        self.assertEqual(response.status_code, 401)

    def test_swagger_specification(self):
        response = self.client.get("/api/swagger.json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

        specification = response.get_json()

        self.assertEqual(specification["swagger"], "2.0")
        self.assertIn("CustomerPayload", specification["definitions"])
        self.assertIn("bearerAuth", specification["securityDefinitions"])

        # Confirm every business API operation is documented.
        blueprint_names = {
            "customer", "mechanic", "service_ticket", "inventory"
        }

        for rule in self.app.url_map.iter_rules():
            if not any(
                rule.rule.startswith(prefix)
                for prefix in (
                    "/customers",
                    "/mechanics",
                    "/service-tickets",
                    "/inventory",
                )
            ):
                continue

            path = rule.rule
            for argument in rule.arguments:
                path = path.replace(
                    f"<int:{argument}>", f"{{{argument}}}"
                )

            self.assertIn(path, specification["paths"])

            for method in rule.methods - {"HEAD", "OPTIONS"}:
                self.assertIn(
                    method.lower(),
                    specification["paths"][path]
                )

    def test_swagger_access_rules_match_protected_operations(self):
        spec = self.client.get('/api/swagger.json').get_json()
        for path, operations in spec['paths'].items():
            for method, operation in operations.items():
                protected = (path.startswith('/service-tickets') or
                             (path.startswith('/customers') and path != '/customers/login' and
                              not (path == '/customers/' and method == 'post')) or
                             (path.startswith(('/mechanics', '/inventory')) and method in ('post', 'put', 'delete')))
                with self.subTest(path=path, method=method):
                    for key in ('tags', 'summary', 'description', 'responses'):
                        self.assertIn(key, operation)
                    if protected:
                        self.assertEqual(operation['security'], [{'bearerAuth': []}])
                        self.assertIn('401', operation['responses'])
                    for response in operation['responses'].values():
                        self.assertIn('schema', response)
                        self.assertIn('examples', response)

    def test_create_staff_command_and_login(self):
        result = self.app.test_cli_runner().invoke(args=[
            'create-staff', '--email', 'cli-staff@example.com', '--phone', 'cli-phone',
        ], input='cli-password\ncli-password\n')
        self.assertEqual(result.exit_code, 0, result.output)
        login = self.client.post('/customers/login', json={
            'email': 'cli-staff@example.com', 'password': 'cli-password'
        })
        self.assertEqual(login.status_code, 200)
        fresh = self.app.test_client()
        self.assertEqual(fresh.get('/customers/', headers={
            'Authorization': 'Bearer ' + login.json['auth_token']
        }).status_code, 200)
        repeated = self.app.test_cli_runner().invoke(args=[
            'create-staff', '--email', 'cli-staff@example.com', '--phone', 'cli-phone',
        ], input='different-password\ndifferent-password\n')
        self.assertNotEqual(repeated.exit_code, 0)
        self.assertEqual(self.client.post('/customers/login', json={
            'email': 'cli-staff@example.com', 'password': 'cli-password'
        }).status_code, 200)
