"""Tests HTTP del historial de sesiones (HU-05)."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class SessionListAuthTests(APITestCase):
    def test_anonymous_401(self):
        self.assertEqual(self.client.get(reverse('session-list')).status_code, 401)

    @patch(
        'RehabWeb_API.views.sessions.get_therapist_for_user',
        return_value=None,
    )
    def test_no_therapist_403(self, _mock_th):
        user = User.objects.create_user('s5', 's5@e.com', 'pw12345678')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}'
        )
        self.assertEqual(self.client.get(reverse('session-list')).status_code, 403)
