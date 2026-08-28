from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.menu.models import MenuCategory, MenuItem
from apps.tables.models import Table, TableStatus
from .models import Order, OrderStatus, ItemStatus, ItemSector

User = get_user_model()


class OrderFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.cozinha = User.objects.create_user(name='C', email='c@t.com', password='x', role='COZINHA')
        cls.recep = User.objects.create_user(name='R', email='r@t.com', password='x', role='RECEPCAO')
        cls.table = Table.objects.create(number=1, seats=4)
        cat = MenuCategory.objects.create(name='Parrilla')
        cls.bife = MenuItem.objects.create(
            category=cat, name='Bife', sector=ItemSector.PARRILLA, price='25.00', sku='BIFE',
            ncm='02013000', cfop='5101', csosn='102', origem='0',
            unit_commercial='UN', unit_taxable='UN', pis_cst='49', cofins_cst='49',
        )

    def open_order(self, user=None):
        self.client.force_authenticate(user or self.garcom)
        return self.client.post('/api/orders/', {'table': self.table.id, 'people_count': 2}, format='json')

    def add_item(self, order_id, quantity=1, user=None):
        self.client.force_authenticate(user or self.garcom)
        return self.client.post(f'/api/orders/{order_id}/add_item/',
                                {'menu_item': self.bife.id, 'quantity': quantity}, format='json')

    def test_open_order_occupies_table(self):
        r = self.open_order()
        self.assertEqual(r.status_code, 201)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.OCUPADA)

    def test_cozinha_cannot_open_order(self):
        self.assertEqual(self.open_order(self.cozinha).status_code, 403)

    def test_recepcao_can_open_order(self):
        self.assertEqual(self.open_order(self.recep).status_code, 201)

    def test_duplicate_open_order_rejected(self):
        self.open_order()
        self.assertEqual(self.open_order().status_code, 400)

    def test_add_item_from_menu_recalculates_and_snapshots(self):
        order_id = self.open_order().data['id']
        r = self.add_item(order_id, quantity=2)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['product_name'], 'Bife')
        self.assertEqual(r.data['fiscal_ncm'], '02013000')
        self.assertEqual(str(Order.objects.get(pk=order_id).total_amount), '50.00')

    def test_free_text_item_is_rejected(self):
        order_id = self.open_order().data['id']
        r = self.client.post(f'/api/orders/{order_id}/add_item/',
                             {'product_name': 'Avulso', 'unit_price': '5.00', 'sector': 'BAR'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_any_authenticated_user_can_add_menu_item(self):
        order_id = self.open_order().data['id']
        self.assertEqual(self.add_item(order_id, user=self.cozinha).status_code, 201)

    def test_cannot_add_item_to_finalized_order(self):
        order_id = self.open_order().data['id']
        self.client.post(f'/api/orders/{order_id}/update_status/', {'status': OrderStatus.FINALIZADO}, format='json')
        self.assertEqual(self.add_item(order_id).status_code, 400)

    def test_finalize_sends_table_to_cleaning(self):
        order_id = self.open_order().data['id']
        r = self.client.post(f'/api/orders/{order_id}/update_status/', {'status': OrderStatus.FINALIZADO}, format='json')
        self.assertEqual(r.status_code, 200)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, TableStatus.LIMPEZA)

    def test_remove_item_cancels_and_recalculates(self):
        order_id = self.open_order().data['id']
        item_id = self.add_item(order_id, quantity=2).data['id']
        r = self.client.delete(f'/api/orders/{order_id}/items/{item_id}/')
        self.assertEqual(r.status_code, 200)
        order = Order.objects.get(pk=order_id)
        self.assertEqual(str(order.total_amount), '0.00')
        self.assertEqual(order.items.get(pk=item_id).status, ItemStatus.CANCELADO)
