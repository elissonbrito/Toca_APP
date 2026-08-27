from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Table, TableStatus

User = get_user_model()


class TablePermissionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(name='Adm', email='adm@t.com', password='x', role='ADM_MAXIMO')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.table = Table.objects.create(number=1, seats=4)

    def test_garcom_cannot_create_table(self):
        self.client.force_authenticate(self.garcom)
        r = self.client.post('/api/tables/', {'number': 99, 'seats': 2}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_manager_can_create_table(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post('/api/tables/', {'number': 99, 'seats': 2}, format='json')
        self.assertEqual(r.status_code, 201)

    def test_garcom_can_change_status(self):
        self.client.force_authenticate(self.garcom)
        r = self.client.post(f'/api/tables/{self.table.id}/status/', {'status': TableStatus.LIMPEZA}, format='json')
        self.assertEqual(r.status_code, 200)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.LIMPEZA)

    def test_invalid_status_rejected(self):
        self.client.force_authenticate(self.garcom)
        r = self.client.post(f'/api/tables/{self.table.id}/status/', {'status': 'XPTO'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_list_requires_auth(self):
        self.assertEqual(self.client.get('/api/tables/').status_code, 401)
