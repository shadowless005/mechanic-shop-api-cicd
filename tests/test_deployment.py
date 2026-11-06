import unittest
from pathlib import Path

import yaml
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash

from application import create_app
from application.extensions import db
from application.models import Customer
from config import ProductionConfig, TestingConfig, database_uri


class TestDeployment(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_render_postgres_urls_use_psycopg2(self):
        for prefix in ('postgres://', 'postgresql://', 'postgresql+psycopg2://'):
            self.assertEqual(database_uri(prefix + 'demo:example@localhost/shop'),
                             'postgresql+psycopg2://demo:example@localhost/shop')
        self.assertIsNone(database_uri(None))
        self.assertEqual(database_uri('sqlite://'), 'sqlite://')

    def test_production_fails_without_environment_settings(self):
        for uri, secret in [(None, 'example'), ('postgresql://localhost/shop', None)]:
            class MissingConfig(ProductionConfig):
                SQLALCHEMY_DATABASE_URI = uri
                SECRET_KEY = secret
            with self.subTest(uri=uri), self.assertRaisesRegex(RuntimeError, 'DATABASE_URL and SECRET_KEY'):
                create_app(MissingConfig)

    def test_production_rejects_sqlite_fallback(self):
        class WrongDatabase(ProductionConfig):
            SQLALCHEMY_DATABASE_URI = 'sqlite://'
            SECRET_KEY = 'example'
        with self.assertRaisesRegex(RuntimeError, 'PostgreSQL'):
            create_app(WrongDatabase)

    def test_swagger_local_targets_local_server(self):
        response = self.app.test_client().get('/api/swagger.json', base_url='http://localhost:5001')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['host'], 'localhost:5001')
        self.assertEqual(response.json['schemes'], ['http'])

    def test_swagger_production_targets_live_https(self):
        class ProductionWithoutConnection(ProductionConfig):
            SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://demo:example@localhost/not_connected'
            SECRET_KEY = 'example'
        production = create_app(ProductionWithoutConnection)
        response = production.test_client().get('/api/swagger.json')
        self.assertEqual(response.json['host'], 'mechanic-shop-api-cicd.onrender.com')
        self.assertEqual(response.json['schemes'], ['https'])
        with production.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_upgrade_existing_schema_preserves_customer_and_is_repeatable(self):
        with self.app.app_context():
            db.drop_all()
            with db.engine.begin() as connection:
                connection.execute(text('''CREATE TABLE customers (
                    id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL,
                    email VARCHAR(360) UNIQUE NOT NULL, phone VARCHAR(20) UNIQUE NOT NULL,
                    address VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL)'''))
                connection.execute(text("INSERT INTO customers VALUES (1, 'Legacy', 'legacy@example.com', 'legacy-phone', 'Demo', 'legacy-password')"))
        for _ in range(2):
            result = self.app.test_cli_runner().invoke(args=['upgrade-db'])
            self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            customer = db.session.get(Customer, 1)
            self.assertEqual(customer.name, 'Legacy')
            self.assertEqual(customer.password, 'legacy-password')
            self.assertFalse(customer.is_staff)
            self.assertIn('service_tickets', inspect(db.engine).get_table_names())

    def test_reset_legacy_password_keeps_regular_role(self):
        with self.app.app_context():
            customer = Customer(name='Legacy', email='legacy@example.com', phone='legacy',
                                address='Demo', password='plaintext-old', is_staff=False)
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id
        result = self.app.test_cli_runner().invoke(args=['reset-password', '--email', 'legacy@example.com'],
                                                   input='new-demo-password\nnew-demo-password\n')
        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            customer = db.session.get(Customer, customer_id)
            self.assertTrue(check_password_hash(customer.password, 'new-demo-password'))
            self.assertFalse(customer.is_staff)
        response = self.app.test_client().post('/customers/login', json={
            'email': 'legacy@example.com', 'password': 'new-demo-password'})
        self.assertEqual(response.status_code, 200)

    def test_health_checks_database_schema(self):
        client = self.app.test_client()
        self.assertEqual(client.get('/health').status_code, 200)
        with self.app.app_context():
            db.drop_all()
        response = client.get('/health')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {'status': 'unavailable', 'database': 'unavailable'})

    def test_workflow_gates_deployment_and_uses_built_artifacts(self):
        root = Path(__file__).resolve().parents[1]
        workflow = yaml.safe_load((root / '.github/workflows/main.yaml').read_text())
        self.assertIn('main', workflow['on']['push']['branches'])
        jobs = workflow['jobs']
        self.assertEqual(jobs['test']['needs'], 'build')
        self.assertEqual(jobs['deploy']['needs'], 'test')
        self.assertIn("github.event_name != 'pull_request'", jobs['deploy']['if'])
        self.assertTrue(any('download-artifact' in step.get('uses', '') for step in jobs['test']['steps']))
        deploy = jobs['deploy']['steps'][0]
        self.assertIn('--fail-with-body', deploy['run'])
        self.assertIn('commitId', deploy['run'])
        self.assertEqual(set(deploy['env']), {'SERVICE_ID', 'RENDER_API_KEY'})
        requirements = (root / 'requirements.txt').read_text().lower()
        self.assertIn('gunicorn==', requirements)
        self.assertIn('psycopg2-binary==', requirements)
        self.assertNotIn('python-dotenv', requirements)
