from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import QueueTicket, TicketStatus

User = get_user_model()


class QueueTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.recep = User.objects.create_user(name='R', email='r@t.com', password='x', role='RECEPCAO')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')

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
