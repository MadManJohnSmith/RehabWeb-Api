"""Tests HTTP — salud, login y logout (HU-07)."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class HealthAPIViewTests(APITestCase):
    def test_health_anonymous_200(self):
        r = self.client.get(reverse('api-health'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], 'ok')


class AuthTokenTests(APITestCase):
    def test_login_returns_token(self):
        User.objects.create_user('hu7login', 'hu7@e.com', 'pw_Test_12345')
        r = self.client.post(
            reverse('api-auth-login'),
            {'username': 'hu7login', 'password': 'pw_Test_12345'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)

    def test_login_invalid_400(self):
        User.objects.create_user('hu7b', 'hu7b@e.com', 'pw_Test_12345')
        r = self.client.post(
            reverse('api-auth-login'),
            {'username': 'hu7b', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(r.status_code, 400)

    def test_logout_deletes_token(self):
        user = User.objects.create_user('hu7out', 'hu7out@e.com', 'pw_Test_12345')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        r = self.client.post(reverse('api-auth-logout'))
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_logout_requires_auth(self):
        self.assertEqual(self.client.post(reverse('api-auth-logout')).status_code, 401)
