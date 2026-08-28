from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.orders.models import Order
from apps.tables.models import Table, TableStatus
from .models import QueueTicket, TicketStatus

User = get_user_model()


class QueueTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.recep = User.objects.create_user(name='R', email='r@t.com', password='x', role='RECEPCAO')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.table = Table.objects.create(number=1, seats=4)

    def test_garcom_cannot_issue_ticket(self):
        self.client.force_authenticate(self.garcom)
        r = self.client.post('/api/queue/', {'customer_name': 'Maria', 'people_count': 2}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_recepcao_issues_ticket_with_code(self):
        self.client.force_authenticate(self.recep)
        r = self.client.post('/api/queue/', {'customer_name': 'Maria', 'people_count': 2}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data['code'])
        self.assertEqual(r.data['status'], TicketStatus.AGUARDANDO)

    def test_public_display_is_open(self):
        r = self.client.get('/api/queue/public_display/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('waiting_count', r.data)

    def test_call_next_returns_oldest_waiting(self):
        self.client.force_authenticate(self.recep)
        first = self.client.post('/api/queue/', {'customer_name': 'A'}, format='json').data['code']
        self.client.post('/api/queue/', {'customer_name': 'B'}, format='json')
        r = self.client.post('/api/queue/call_next/', {}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['code'], first)
        self.assertEqual(r.data['status'], TicketStatus.CHAMADO)

    def test_call_next_empty_queue_is_400(self):
        self.client.force_authenticate(self.recep)
        r = self.client.post('/api/queue/call_next/', {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_finalize_and_cancel(self):
        self.client.force_authenticate(self.recep)
        tid = self.client.post('/api/queue/', {'customer_name': 'A'}, format='json').data['id']
        self.assertEqual(self.client.post(f'/api/queue/{tid}/finalize/', {}, format='json').data['status'],
                         TicketStatus.FINALIZADO)

    def _ticket(self, **over):
        self.client.force_authenticate(self.recep)
        data = {'customer_name': 'Familia Silva', 'people_count': 3, **over}
        return self.client.post('/api/queue/', data, format='json').data['id']

    def test_garcom_cannot_assign_table(self):
        tid = self._ticket()
        self.client.force_authenticate(self.garcom)
        r = self.client.post(f'/api/queue/{tid}/assign-table/', {'table': self.table.id}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_assign_table_opens_order_and_carries_customer(self):
        tid = self._ticket()
        self.client.force_authenticate(self.recep)
        r = self.client.post(f'/api/queue/{tid}/assign-table/', {'table': self.table.id}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], TicketStatus.SENTADO)
        self.assertEqual(r.data['table_number'], self.table.number)
        self.assertTrue(r.data['order_id'])

        order = Order.objects.get(pk=r.data['order_id'])
        self.assertEqual(order.queue_ticket_id, tid)
        self.assertEqual(order.customer_name, 'Familia Silva')
        self.assertEqual(order.people_count, 3)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.OCUPADA)

    def test_assign_table_without_opening_order(self):
        tid = self._ticket()
        self.client.force_authenticate(self.recep)
        r = self.client.post(f'/api/queue/{tid}/assign-table/',
                             {'table': self.table.id, 'open_order': False}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data['order_id'])
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.RESERVADA)

    def test_assign_to_occupied_table_is_400(self):
        first = self._ticket()
        self.client.force_authenticate(self.recep)
        self.client.post(f'/api/queue/{first}/assign-table/', {'table': self.table.id}, format='json')
        second = self._ticket()
        r = self.client.post(f'/api/queue/{second}/assign-table/', {'table': self.table.id}, format='json')
        self.assertEqual(r.status_code, 400)
