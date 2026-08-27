from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.tables.models import Table
from apps.orders.models import Order, OrderItem, OrderStatus, ItemStatus, ItemSector

User = get_user_model()


class KitchenTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.cozinha = User.objects.create_user(name='C', email='c@t.com', password='x', role='COZINHA')
        cls.parrilla = User.objects.create_user(name='P', email='p@t.com', password='x', role='PARRILLA')
        cls.table = Table.objects.create(number=1, seats=4)

    def _order_with_items(self):
        order = Order.objects.create(table=self.table, opened_by=self.garcom)
        coz = OrderItem.objects.create(order=order, product_name='Batata', quantity=1,
                                       unit_price=10, sector=ItemSector.COZINHA)
        par = OrderItem.objects.create(order=order, product_name='Bife', quantity=1,
                                       unit_price=40, sector=ItemSector.PARRILLA)
        return order, coz, par

    def test_garcom_cannot_view_queue(self):
        self.client.force_authenticate(self.garcom)
        self.assertEqual(self.client.get('/api/kitchen/orders/?sector=COZINHA').status_code, 403)

    def test_queue_filtered_by_sector(self):
        self._order_with_items()
        self.client.force_authenticate(self.cozinha)
        r = self.client.get('/api/kitchen/orders/?sector=COZINHA')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]['sector'], ItemSector.COZINHA)

    def test_invalid_sector_rejected(self):
        self.client.force_authenticate(self.cozinha)
        self.assertEqual(self.client.get('/api/kitchen/orders/?sector=XPTO').status_code, 400)

    def test_order_becomes_ready_when_all_items_ready(self):
        order, coz, par = self._order_with_items()
        self.client.force_authenticate(self.cozinha)
        self.client.patch(f'/api/kitchen/items/{coz.id}/status/', {'status': ItemStatus.PRONTO}, format='json')
        order.refresh_from_db()
        self.assertNotEqual(order.status, OrderStatus.PRONTO)  # parrilla ainda pendente

        self.client.force_authenticate(self.parrilla)
        self.client.patch(f'/api/kitchen/items/{par.id}/status/', {'status': ItemStatus.PRONTO}, format='json')
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PRONTO)

    def test_invalid_item_status_rejected(self):
        _, coz, _ = self._order_with_items()
        self.client.force_authenticate(self.cozinha)
        r = self.client.patch(f'/api/kitchen/items/{coz.id}/status/', {'status': 'XPTO'}, format='json')
        self.assertEqual(r.status_code, 400)
