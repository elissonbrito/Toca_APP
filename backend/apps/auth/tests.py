"""
Testes dos endpoints de autenticação JWT.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            name='Admin', email='admin@toca.com', password='123456', role='ADM_MAXIMO',
        )

    def login(self, email='admin@toca.com', password='123456'):
        return self.client.post('/api/auth/login/', {'email': email, 'password': password}, format='json')

    def test_login_ok(self):
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.data), {'access', 'refresh', 'user'})
        self.assertEqual(r.data['user']['email'], 'admin@toca.com')

    def test_login_bad_password_is_401(self):
        self.assertEqual(self.login(password='wrong').status_code, 401)

    def test_login_missing_field_is_400(self):
        r = self.client.post('/api/auth/login/', {'email': 'admin@toca.com'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_login_inactive_is_403(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.login().status_code, 403)

    def test_me_requires_token(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_me_with_token(self):
        access = self.login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        r = self.client.get('/api/auth/me/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['role'], 'ADM_MAXIMO')

    def test_refresh_rotates_token(self):
        refresh = self.login().data['refresh']
        r = self.client.post('/api/auth/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)

    def test_logout_blacklists_refresh(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        r = self.client.post('/api/auth/logout/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(r.status_code, 200)

        r = self.client.post('/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)
