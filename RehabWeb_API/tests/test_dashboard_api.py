"""Tests HTTP del endpoint de dashboard (HU-01)."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class MeDashboardAuthTests(APITestCase):
    def test_anonymous_returns_401(self):
        url = reverse('me-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    @patch(
        'RehabWeb_API.views.dashboard.build_dashboard_payload',
        return_value={
            'therapistLinked': True,
            'inactivitySummary': {
                'inactiveCount': 0,
                'thresholdDays': 3,
                'patients': [],
            },
            'romByWeek': [],
            'temporalSeries': [],
            'recentSessions': [],
            'summaryRings': [],
        },
    )
    def test_authenticated_returns_payload(self, _mock_payload):
        user = User.objects.create_user(
            username='doc',
            email='doc@example.com',
            password='test-pass-123',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = reverse('me-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['therapistLinked'])
