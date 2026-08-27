from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.tables.models import Table, TableStatus
from .models import Order, OrderStatus, ItemStatus, ItemSector

User = get_user_model()


class OrderFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.cozinha = User.objects.create_user(name='C', email='c@t.com', password='x', role='COZINHA')
        cls.table = Table.objects.create(number=1, seats=4)

    def open_order(self, user=None):
        self.client.force_authenticate(user or self.garcom)
        return self.client.post('/api/orders/', {'table': self.table.id, 'people_count': 2}, format='json')

    def test_open_order_occupies_table(self):
        r = self.open_order()
        self.assertEqual(r.status_code, 201)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.OCUPADA)

    def test_cozinha_cannot_open_order(self):
        r = self.open_order(self.cozinha)
        self.assertEqual(r.status_code, 403)

    def test_duplicate_open_order_rejected(self):
        self.open_order()
        r = self.open_order()
        self.assertEqual(r.status_code, 400)

    def test_add_item_recalculates_total(self):
        order_id = self.open_order().data['id']
        r = self.client.post(f'/api/orders/{order_id}/add_item/', {
            'product_name': 'Bife', 'quantity': 2, 'unit_price': '25.00', 'sector': ItemSector.PARRILLA,
        }, format='json')
        self.assertEqual(r.status_code, 201)
        order = Order.objects.get(pk=order_id)
        self.assertEqual(str(order.total_amount), '50.00')

    def test_cannot_add_item_to_finalized_order(self):
        order_id = self.open_order().data['id']
        self.client.post(f'/api/orders/{order_id}/update_status/', {'status': OrderStatus.FINALIZADO}, format='json')
        r = self.client.post(f'/api/orders/{order_id}/add_item/', {
            'product_name': 'X', 'quantity': 1, 'unit_price': '5.00', 'sector': ItemSector.BAR,
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_finalize_sends_table_to_cleaning(self):
        order_id = self.open_order().data['id']
        r = self.client.post(f'/api/orders/{order_id}/update_status/', {'status': OrderStatus.FINALIZADO}, format='json')
        self.assertEqual(r.status_code, 200)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.LIMPEZA)

    def test_remove_item_cancels_and_recalculates(self):
        order_id = self.open_order().data['id']
        item_id = self.client.post(f'/api/orders/{order_id}/add_item/', {
            'product_name': 'Bife', 'quantity': 2, 'unit_price': '25.00', 'sector': ItemSector.PARRILLA,
        }, format='json').data['id']
        r = self.client.delete(f'/api/orders/{order_id}/items/{item_id}/')
        self.assertEqual(r.status_code, 200)
        order = Order.objects.get(pk=order_id)
        self.assertEqual(str(order.total_amount), '0.00')
        self.assertEqual(order.items.get(pk=item_id).status, ItemStatus.CANCELADO)
