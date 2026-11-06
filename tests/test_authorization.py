import unittest

from application import create_app
from application.extensions import db, cache
from application.models import Customer, Mechanic, Inventory, ServiceTicket
from application.utils.util import encode_token
from config import TestingConfig
from auth_helpers import make_customer


class TestAuthorization(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            cache.clear()
            db.drop_all()
            db.create_all()
            self.owner, self.owner_headers = make_customer('owner')
            self.other, self.other_headers = make_customer('other')
            self.staff, self.staff_headers = make_customer('staff', staff=True)
            mechanic = Mechanic(name='Mechanic', email='mechanic@example.com',
                                phone='mechanic', address='Shop', salary=50000)
            inventory = Inventory(name='Brakes', price=49.99)
            ticket = ServiceTicket(description='Repair', vin='1HGCM82633A123456',
                                   customer_id=self.owner)
            other_ticket = ServiceTicket(description='Private repair', vin='1HGCM82633A123457',
                                         customer_id=self.other)
            ticket.mechanics.append(mechanic)
            db.session.add_all([mechanic, inventory, ticket, other_ticket])
            db.session.commit()
            self.mechanic = mechanic.id
            self.inventory = inventory.id
            self.ticket = ticket.id
            self.other_ticket = other_ticket.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            cache.clear()
            db.engine.dispose()

    def test_customer_directory_checks_role_even_after_cache_warmed(self):
        self.assertEqual(self.client.get('/customers/', headers=self.staff_headers).status_code, 200)
        for headers, status in [({}, 401), (self.owner_headers, 403)]:
            with self.subTest(status=status):
                response = self.client.get('/customers/', headers=headers)
                self.assertEqual(response.status_code, status)
                self.assertNotIn('email', response.get_json())

    def test_customer_detail_is_owner_or_staff_only(self):
        for headers, status in [({}, 401), (self.owner_headers, 200),
                                (self.other_headers, 403), (self.staff_headers, 200)]:
            with self.subTest(status=status, headers=headers):
                response = self.client.get(f'/customers/{self.owner}', headers=headers)
                self.assertEqual(response.status_code, status)
                self.assertNotIn('password', response.get_json())

    def test_ticket_list_is_filtered_by_owner(self):
        for headers, expected in [(self.owner_headers, [self.ticket]),
                                  (self.other_headers, [self.other_ticket]),
                                  (self.staff_headers, [self.ticket, self.other_ticket])]:
            response = self.client.get('/service-tickets/', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([t['id'] for t in response.json], expected)
        self.assertEqual(self.client.get('/service-tickets/').status_code, 401)

    def test_customer_can_create_own_ticket_but_not_someone_elses(self):
        payload = dict(description='New repair', vin='1HGCM82633A123456', customer_id=self.owner)
        response = self.client.post('/service-tickets/', json=payload, headers=self.owner_headers)
        self.assertEqual(response.status_code, 201)
        payload['customer_id'] = self.other
        self.assertEqual(self.client.post('/service-tickets/', json=payload,
                                         headers=self.owner_headers).status_code, 403)
        self.assertEqual(self.client.post('/service-tickets/', json=payload).status_code, 401)
        with self.app.app_context():
            self.assertEqual(db.session.query(ServiceTicket).count(), 3)

    def test_ticket_customer_must_exist(self):
        response = self.client.post('/service-tickets/', headers=self.staff_headers,
                                    json=dict(description='Repair', vin='1HGCM82633A123456', customer_id=99999))
        self.assertEqual(response.status_code, 404)
        with self.app.app_context():
            self.assertEqual(db.session.query(ServiceTicket).count(), 2)

    def test_all_assignment_routes_deny_nonstaff_without_mutating(self):
        urls = [f'/service-tickets/{self.ticket}/assign-mechanic/{self.mechanic}',
                f'/service-tickets/{self.ticket}/remove-mechanic/{self.mechanic}',
                f'/service-tickets/{self.ticket}/edit',
                f'/service-tickets/{self.ticket}/add-inventory/{self.inventory}']
        for headers, status in [({}, 401), (self.owner_headers, 403)]:
            for url in urls:
                with self.subTest(url=url, status=status):
                    response = self.client.put(url, json={'remove_ids': [self.mechanic]}, headers=headers)
                    self.assertEqual(response.status_code, status)
        with self.app.app_context():
            ticket = db.session.get(ServiceTicket, self.ticket)
            self.assertEqual([m.id for m in ticket.mechanics], [self.mechanic])
            self.assertEqual(ticket.inventory, [])

    def test_mechanic_writes_require_staff(self):
        payload = dict(name='Changed', email='new@example.com', phone='new', address='Shop', salary=60000)
        for headers, status in [({}, 401), (self.owner_headers, 403)]:
            for method, url in [('POST', '/mechanics/'), ('PUT', f'/mechanics/{self.mechanic}'),
                                ('DELETE', f'/mechanics/{self.mechanic}')]:
                with self.subTest(method=method, status=status):
                    self.assertEqual(self.client.open(url, method=method, json=payload,
                                                      headers=headers).status_code, status)
        with self.app.app_context():
            self.assertEqual(db.session.query(Mechanic).count(), 1)
            self.assertEqual(db.session.get(Mechanic, self.mechanic).name, 'Mechanic')

    def test_deleted_customer_token_is_rejected(self):
        with self.app.app_context():
            customer_id, headers = make_customer('deleted')
            db.session.delete(db.session.get(Customer, customer_id))
            db.session.commit()
        self.assertEqual(self.client.get('/service-tickets/', headers=headers).status_code, 401)

    def test_registration_and_update_cannot_set_role_or_id(self):
        payload = dict(name='New', email='new@example.com', phone='new', address='Street', password='password')
        for field, value in [('is_staff', True), ('id', self.owner)]:
            with self.subTest(field=field):
                self.assertEqual(self.client.post('/customers/', json={**payload, field: value}).status_code, 400)
                self.assertEqual(self.client.put('/customers/', json={field: value},
                                                 headers=self.owner_headers).status_code, 400)
        with self.app.app_context():
            self.assertFalse(db.session.get(Customer, self.owner).is_staff)
            self.assertEqual(db.session.query(Customer).count(), 3)

    def test_customer_partial_update_preserves_password_and_identity(self):
        with self.app.app_context():
            original_password = db.session.get(Customer, self.owner).password
        response = self.client.put('/customers/', json={'address': 'New Street'}, headers=self.owner_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['address'], 'New Street')
        with self.app.app_context():
            customer = db.session.get(Customer, self.owner)
            self.assertEqual(customer.email, 'owner@example.com')
            self.assertEqual(customer.password, original_password)
            self.assertEqual(db.session.get(Customer, self.other).address, '123 Test Street')

    def test_customer_duplicate_email_and_phone_return_conflict(self):
        for field, value in [('email', 'owner@example.com'), ('phone', 'owner')]:
            with self.subTest(field=field):
                payload = dict(name='New', email='new@example.com', phone='new', address='Street', password='password')
                payload[field] = value
                self.assertEqual(self.client.post('/customers/', json=payload).status_code, 409)
                self.assertEqual(self.client.put('/customers/', json={field: value},
                                                 headers=self.other_headers).status_code, 409)
        self.assertEqual(self.client.put('/customers/', json={'address': 'Recovered'},
                                         headers=self.other_headers).status_code, 200)

    def test_mechanic_duplicate_email_and_phone_return_conflict(self):
        payload = dict(name='Second', email='second@example.com', phone='second', address='Shop', salary=50000)
        created = self.client.post('/mechanics/', json=payload, headers=self.staff_headers)
        self.assertEqual(created.status_code, 201)
        for field, value in [('email', 'mechanic@example.com'), ('phone', 'mechanic')]:
            duplicate = {**payload, field: value}
            with self.subTest(field=field):
                self.assertEqual(self.client.post('/mechanics/', json=duplicate,
                                                  headers=self.staff_headers).status_code, 409)
                self.assertEqual(self.client.put(f'/mechanics/{created.json["id"]}', json=duplicate,
                                                 headers=self.staff_headers).status_code, 409)
        self.assertEqual(self.client.get('/mechanics/').status_code, 200)

    def test_customer_with_tickets_cannot_be_deleted(self):
        response = self.client.delete('/customers/', headers=self.owner_headers)
        self.assertEqual(response.status_code, 409)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Customer, self.owner))
            self.assertIsNotNone(db.session.get(ServiceTicket, self.ticket))

    def test_ids_cannot_be_changed_on_inventory_mechanic_or_ticket(self):
        for url, method in [(f'/inventory/{self.inventory}', 'PUT'),
                            (f'/mechanics/{self.mechanic}', 'PUT'), ('/service-tickets/', 'POST')]:
            with self.subTest(url=url):
                response = self.client.open(url, method=method, json={'id': 999}, headers=self.staff_headers)
                self.assertEqual(response.status_code, 400)

    def test_malformed_json_returns_validation_errors(self):
        for url, method, headers in [('/customers/', 'POST', {}), ('/customers/login', 'POST', {}),
                                     ('/mechanics/', 'POST', self.staff_headers),
                                     ('/inventory/', 'POST', self.staff_headers),
                                     ('/service-tickets/', 'POST', self.owner_headers)]:
            with self.subTest(url=url):
                response = self.client.open(url, method=method, data='{', content_type='application/json', headers=headers)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)
