from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class DashboardTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(name='A', email='a@t.com', password='x', role='ADM_MAXIMO')
        cls.gerente = User.objects.create_user(name='M', email='m@t.com', password='x', role='GERENTE')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')

    def test_garcom_forbidden(self):
        self.client.force_authenticate(self.garcom)
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)

    def test_gerente_forbidden(self):
        # dashboard é exclusivo do ADM_MAXIMO
        self.client.force_authenticate(self.gerente)
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)

    def test_admin_gets_overview_shape(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get('/api/dashboard/')
        self.assertEqual(r.status_code, 200)
        for key in ['today', 'monthly_revenue', 'tables', 'queue', 'top_products', 'daily_revenue']:
            self.assertIn(key, r.data)
        self.assertEqual(len(r.data['daily_revenue']), 7)
