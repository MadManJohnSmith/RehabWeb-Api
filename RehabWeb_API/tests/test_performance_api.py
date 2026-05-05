"""Tests HTTP HU-04."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class PatientPerformanceSeriesAPITests(APITestCase):
    def test_anonymous_401(self):
        url = reverse('patient-performance-series', kwargs={'patient_id': 1})
        self.assertEqual(self.client.get(url).status_code, 401)

    @patch(
        'RehabWeb_API.views.performance.resolve_patient_for_therapist',
        return_value=('ok', {'patientId': 1, 'fullName': 'X', 'temporalSeries': [], 'summary': {}}),
    )
    @patch('RehabWeb_API.views.performance.get_therapist_for_user')
    def test_ok(self, mock_th, _mock_res):
        mock_th.return_value = object()
        user = User.objects.create_user('p4', 'p4@e.com', 'pw12345678')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')
        url = reverse('patient-performance-series', kwargs={'patient_id': 1})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['patientId'], 1)

    @patch(
        'RehabWeb_API.views.performance.resolve_patient_for_therapist',
        return_value=('not_found', None),
    )
    @patch('RehabWeb_API.views.performance.get_therapist_for_user')
    def test_not_found_404(self, mock_th, _mock_res):
        mock_th.return_value = object()
        user = User.objects.create_user('p4b', 'p4b@e.com', 'pw12345678')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')
        url = reverse('patient-performance-series', kwargs={'patient_id': 99})
        self.assertEqual(self.client.get(url).status_code, 404)


class PerformanceCompareAPITests(APITestCase):
    def test_anonymous_401(self):
        url = reverse('performance-compare')
        self.assertEqual(
            self.client.post(url, data={'patientIds': [1]}, format='json').status_code,
            401,
        )

    @patch('RehabWeb_API.views.performance.resolve_patient_for_therapist')
    @patch('RehabWeb_API.views.performance.get_therapist_for_user')
    def test_compare_ok(self, mock_th, mock_res):
        mock_th.return_value = object()

        def _res(_t, pid):
            return (
                'ok',
                {
                    'patientId': pid,
                    'fullName': f'P{pid}',
                    'temporalSeries': [
                        {
                            'sortOrder': 0,
                            'periodLabel': 'A',
                            'metaValue': 100.0,
                            'observedValue': 50.0,
                            'trend': 'initial',
                        }
                    ],
                    'summary': {},
                },
            )

        mock_res.side_effect = _res
        user = User.objects.create_user('p4c', 'p4c@e.com', 'pw12345678')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')
        url = reverse('performance-compare')
        r = self.client.post(url, data={'patientIds': [1, 2]}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['patients']), 2)
        self.assertIn('groupBounds', r.data)
