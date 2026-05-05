"""Tests HTTP del endpoint de exportación (HU-02)."""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class ReportExportAuthTests(APITestCase):
    def test_anonymous_returns_401(self):
        url = reverse('reports-export')
        response = self.client.post(
            url,
            data={
                'patientId': 1,
                'dateFrom': '2026-01-01',
                'dateTo': '2026-01-15',
                'format': 'pdf',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    @patch('RehabWeb_API.views.reports.get_therapist_for_user', return_value=None)
    def test_no_therapist_profile_returns_403(self, _mock_th):
        user = User.objects.create_user(
            username='noprofile',
            email='n@example.com',
            password='secret12345',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = reverse('reports-export')
        response = self.client.post(
            url,
            data={
                'patientId': 1,
                'dateFrom': '2026-01-01',
                'dateTo': '2026-01-15',
                'format': 'pdf',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    @patch('RehabWeb_API.views.reports.render_clinical_export')
    @patch('RehabWeb_API.views.reports.get_active_therapist_patient_link')
    @patch('RehabWeb_API.views.reports.get_therapist_for_user')
    def test_success_returns_attachment(
        self, mock_therapist, mock_link, mock_render,
    ):
        mock_therapist.return_value = MagicMock()
        mock_link.return_value = MagicMock()
        mock_render.return_value = (
            b'%PDF-1.4 minimal',
            'informe_clinico_p1_2026-01-01_2026-01-15.pdf',
            'application/pdf',
        )

        user = User.objects.create_user(
            username='doc2',
            email='d2@example.com',
            password='secret12345',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = reverse('reports-export')
        response = self.client.post(
            url,
            data={
                'patientId': 1,
                'dateFrom': '2026-01-01',
                'dateTo': '2026-01-15',
                'format': 'pdf',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response['Content-Type'])
        self.assertGreater(len(response.content), 5)
