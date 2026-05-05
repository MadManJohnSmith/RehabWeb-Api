"""Tests HTTP de alertas de inactividad (HU-03)."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class InactivityAlertsAuthTests(APITestCase):
    def test_anonymous_returns_401(self):
        url = reverse('inactivity-alerts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    @patch('RehabWeb_API.views.inactivity.get_therapist_for_user', return_value=None)
    def test_no_therapist_returns_403(self, _mock):
        user = User.objects.create_user(
            username='n3',
            email='n3@example.com',
            password='secret12345',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get(reverse('inactivity-alerts'))
        self.assertEqual(response.status_code, 403)

    @patch('RehabWeb_API.views.inactivity.get_inactive_patients_for_therapist')
    @patch('RehabWeb_API.views.inactivity.get_therapist_for_user')
    def test_success_returns_payload(self, mock_th, mock_rows):
        mock_th.return_value = object()
        mock_rows.return_value = [
            {
                'patientId': 1,
                'fullName': 'Ana',
                'daysSinceLastSession': 5,
                'lastSessionAt': '2026-01-01T10:00:00+00:00',
            }
        ]
        user = User.objects.create_user(
            username='d3',
            email='d3@example.com',
            password='secret12345',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get(reverse('inactivity-alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['inactiveCount'], 1)
        self.assertEqual(response.data['thresholdDays'], 3)
        self.assertEqual(len(response.data['alerts']), 1)
