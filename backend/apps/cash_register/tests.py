from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.tables.models import Table, TableStatus
from apps.orders.models import Order, OrderItem, OrderStatus, ItemSector
from .models import CashRegister, CashRegisterStatus

User = get_user_model()


class CashRegisterTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.caixa = User.objects.create_user(name='Cx', email='cx@t.com', password='x', role='CAIXA')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.table = Table.objects.create(number=1, seats=4)

    def _open_register(self):
        self.client.force_authenticate(self.caixa)
        return self.client.post('/api/cash-register/registers/', {'initial_amount': '100.00'}, format='json')

    def _order(self, total=50):
        order = Order.objects.create(table=self.table, opened_by=self.garcom, status=OrderStatus.PRONTO)
        OrderItem.objects.create(order=order, product_name='X', quantity=1, unit_price=total, sector=ItemSector.BAR)
        order.recalculate_total()
        return order

    def test_garcom_cannot_open_register(self):
        self.client.force_authenticate(self.garcom)
        r = self.client.post('/api/cash-register/registers/', {'initial_amount': '100'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_double_open_is_400_not_500(self):
        self.assertEqual(self._open_register().status_code, 201)
        r = self.client.post('/api/cash-register/registers/', {'initial_amount': '50'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_payment_without_open_register_is_400(self):
        order = self._order()
        self.client.force_authenticate(self.caixa)
        r = self.client.post('/api/cash-register/payments/',
                             {'order': order.id, 'amount': '50.00', 'payment_method': 'PIX'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_payment_finalizes_order_and_cleans_table(self):
        self._open_register()
        order = self._order(80)
        r = self.client.post('/api/cash-register/payments/',
                             {'order': order.id, 'amount': '80.00', 'payment_method': 'CREDITO'}, format='json')
        self.assertEqual(r.status_code, 201)
        order.refresh_from_db()
        self.table.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.FINALIZADO)
        self.assertEqual(self.table.status, TableStatus.LIMPEZA)

    def test_cannot_pay_finalized_order(self):
        self._open_register()
        order = self._order()
        order.status = OrderStatus.FINALIZADO
        order.save(update_fields=['status'])
        r = self.client.post('/api/cash-register/payments/',
                             {'order': order.id, 'amount': '10', 'payment_method': 'PIX'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_close_requires_final_amount(self):
        reg_id = self._open_register().data['id']
        r = self.client.post(f'/api/cash-register/registers/{reg_id}/close/', {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_close_and_report(self):
        reg_id = self._open_register().data['id']
        order = self._order(60)
        self.client.post('/api/cash-register/payments/',
                         {'order': order.id, 'amount': '60.00', 'payment_method': 'DINHEIRO'}, format='json')
        rep = self.client.get(f'/api/cash-register/registers/{reg_id}/report/')
        self.assertEqual(rep.status_code, 200)
        self.assertEqual(str(rep.data['total_revenue']), '60.00')

        r = self.client.post(f'/api/cash-register/registers/{reg_id}/close/',
                             {'final_amount': '160.00'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(CashRegister.objects.get(pk=reg_id).status, CashRegisterStatus.FECHADO)
