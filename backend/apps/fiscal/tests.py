from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.menu.models import MenuCategory, MenuItem
from apps.orders.models import Order
from apps.tables.models import Table
from .access_key import build_access_key, dv_modulo11, format_access_key
from .models import FiscalSettings, InvoiceStatus

User = get_user_model()


class AccessKeyTests(APITestCase):
    def test_dv_modulo11_known_value(self):
        base = '3525' '0812345678000199' '65' '001' '000000001' '1' '14539077'
        self.assertEqual(len(base), 43)
        dv = dv_modulo11(base)
        self.assertEqual(len(build_access_key(
            uf='SP', cnpj='12345678000199', serie=1, numero=1,
            codigo_numerico=14539077, competencia=date(2025, 8, 1))), 44)

    def test_build_access_key_structure(self):
        key = build_access_key(uf='SP', cnpj='12.345.678/0001-99', serie=1, numero=42,
                               codigo_numerico=1, competencia=date(2025, 8, 1))
        self.assertEqual(len(key), 44)
        self.assertTrue(key.isdigit())
        self.assertEqual(key[:2], '35')          # cUF SP
        self.assertEqual(key[2:6], '2508')       # AAMM
        self.assertEqual(key[20:22], '65')       # modelo NFC-e
        self.assertEqual(key[-1], dv_modulo11(key[:43]))

    def test_format_access_key(self):
        key = '3' * 44
        self.assertEqual(len(format_access_key(key).split()), 11)


class NFCeFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.caixa = User.objects.create_user(name='Cx', email='cx@t.com', password='x', role='CAIXA')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.table = Table.objects.create(number=1, seats=4)
        cat = MenuCategory.objects.create(name='Parrilla')
        cls.mi = MenuItem.objects.create(
            category=cat, name='Ancho', sector='PARRILLA', price='99.90', sku='ANCHO',
            ncm='02013000', cfop='5101', csosn='102', origem='0',
            unit_commercial='UN', unit_taxable='UN', pis_cst='49', cofins_cst='49',
        )

    def _order(self):
        order = Order.objects.create(table=self.table, opened_by=self.garcom)
        from apps.orders.services import OrderService
        OrderService.add_item(order, menu_item=self.mi, quantity=1)
        return order

    def test_build_without_config_returns_nao_configurado(self):
        self.client.force_authenticate(self.caixa)
        order = self._order()
        r = self.client.post(f'/api/fiscal/nfce/from-order/{order.id}/', {}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['status'], InvoiceStatus.NAO_CONFIGURADO)

    def test_build_with_emitter_config_generates_key_and_xml(self):
        s = FiscalSettings.load()
        s.cnpj, s.uf, s.inscricao_estadual = '12345678000199', 'SP', '111111111111'
        s.razao_social, s.municipio_ibge = 'Toca LTDA', '3550308'
        s.save()

        self.client.force_authenticate(self.caixa)
        order = self._order()
        r = self.client.post(f'/api/fiscal/nfce/from-order/{order.id}/', {}, format='json')
        self.assertEqual(r.data['status'], InvoiceStatus.RASCUNHO)
        self.assertEqual(len(r.data['chave_acesso']), 44)

        xml = self.client.get(f'/api/fiscal/nfce/{r.data["id"]}/xml/')
        self.assertEqual(xml.status_code, 200)
        self.assertIn(b'<infNFe', xml.content)
        self.assertIn(b'<CSOSN>102</CSOSN>', xml.content)

    def test_sign_and_transmit_report_missing_requirements(self):
        s = FiscalSettings.load()
        s.cnpj, s.uf, s.inscricao_estadual, s.razao_social, s.municipio_ibge = (
            '12345678000199', 'SP', '111111111111', 'Toca LTDA', '3550308')
        s.save()
        self.client.force_authenticate(self.caixa)
        order = self._order()
        inv_id = self.client.post(f'/api/fiscal/nfce/from-order/{order.id}/', {}, format='json').data['id']

        sign = self.client.post(f'/api/fiscal/nfce/{inv_id}/sign/', {}, format='json')
        self.assertEqual(sign.data['status'], InvoiceStatus.NAO_CONFIGURADO)
        self.assertIn('faltando', sign.data)

        tx = self.client.post(f'/api/fiscal/nfce/{inv_id}/transmit/', {}, format='json')
        self.assertEqual(tx.data['resultado']['status'], 'NAO_CONFIGURADO')
        self.assertTrue(tx.data['resultado']['faltando'])

    def test_only_caixa_can_build(self):
        self.client.force_authenticate(self.garcom)
        order = self._order()
        r = self.client.post(f'/api/fiscal/nfce/from-order/{order.id}/', {}, format='json')
        self.assertEqual(r.status_code, 403)
