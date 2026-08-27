from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .fiscal import gtin_is_valid
from .models import MenuCategory, MenuItem
from .services import FiscalConferenceService

User = get_user_model()


def _item(**over):
    defaults = dict(name='Bife', sector='PARRILLA', price='50.00', sku='SKU-1',
                    ncm='02013000', cfop='5101', csosn='102', origem='0',
                    unit_commercial='UN', unit_taxable='UN', pis_cst='49', cofins_cst='49')
    defaults.update(over)
    return defaults


class GtinTests(APITestCase):
    def test_valid_and_invalid_gtin(self):
        self.assertTrue(gtin_is_valid('7891910000147'))
        self.assertFalse(gtin_is_valid('7891910000140'))
        self.assertFalse(gtin_is_valid('123'))


class FiscalConferenceTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = MenuCategory.objects.create(name='Parrilla')

    def _make(self, **over):
        return MenuItem.objects.create(category=self.cat, **_item(**over))

    def test_item_conforme(self):
        r = FiscalConferenceService.check_item(self._make())
        self.assertTrue(r['ok'])
        self.assertEqual(r['errors'], [])

    def test_ncm_invalido_gera_erro(self):
        r = FiscalConferenceService.check_item(self._make(sku='S2', ncm='123'))
        self.assertFalse(r['ok'])
        self.assertTrue(any('NCM' in e for e in r['errors']))

    def test_csosn_com_st_exige_cest(self):
        r = FiscalConferenceService.check_item(self._make(sku='S3', csosn='500', cfop='5405', cest=''))
        self.assertFalse(r['ok'])
        self.assertTrue(any('CEST' in e for e in r['errors']))

    def test_csosn_900_exige_aliquota_icms(self):
        r = FiscalConferenceService.check_item(self._make(sku='S4', csosn='900'))
        self.assertFalse(r['ok'])
        self.assertTrue(any('ICMS' in e for e in r['errors']))

    def test_catalog_report_agrega(self):
        self._make()
        self._make(sku='S5', ncm='1')
        rep = FiscalConferenceService.check_catalog(MenuItem.objects.all())
        self.assertEqual(rep['total'], 2)
        self.assertEqual(rep['com_pendencias'], 1)


class MenuApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(name='A', email='a@t.com', password='x', role='ADM_MAXIMO')
        cls.garcom = User.objects.create_user(name='G', email='g@t.com', password='x', role='GARCOM')
        cls.cat = MenuCategory.objects.create(name='Bebidas')

    def test_garcom_reads_but_cannot_write(self):
        self.client.force_authenticate(self.garcom)
        self.assertEqual(self.client.get('/api/menu/items/').status_code, 200)
        self.assertEqual(self.client.post('/api/menu/items/', _item(category=self.cat.id), format='json').status_code, 403)

    def test_manager_creates_item(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post('/api/menu/items/', _item(category=self.cat.id), format='json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data['fiscal_status']['ok'])

    def test_create_csosn500_without_cest_rejected(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post('/api/menu/items/', _item(category=self.cat.id, sku='B1',
                             csosn='500', cfop='5405', ncm='22030000'), format='json')
        self.assertEqual(r.status_code, 400)

    def test_fiscal_report_endpoint(self):
        self.client.force_authenticate(self.admin)
        MenuItem.objects.create(category=self.cat, **_item(sku='B2'))
        r = self.client.get('/api/menu/items/fiscal_report/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('conformes', r.data)
