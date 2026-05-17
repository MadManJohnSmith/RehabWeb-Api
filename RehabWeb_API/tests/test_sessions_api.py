"""Tests HTTP del historial de sesiones (HU-05)."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from RehabWeb_API.models import Patient, Session, Therapist, TherapistPatient


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


def _token_client(client, user):
    client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')


class SessionListSearchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('s5search', 's5search@e.com', 'pw12345678')
        self.therapist = Therapist.objects.create(user=self.user)
        _token_client(self.client, self.user)

        self.patient_a = Patient.objects.create(external_id='PA-1', full_name='Ana López')
        self.patient_b = Patient.objects.create(external_id='PB-2', full_name='Bea Ruiz')
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient_a)
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient_b)

        self.session_a = Session.objects.create(
            therapist=self.therapist,
            patient=self.patient_a,
            occurred_at=timezone.make_aware(datetime(2026, 2, 1, 10, 0)),
            program_label='Movilidad básica',
            duration_min=45,
            score=Decimal('82.50'),
            status='completada',
        )
        Session.objects.create(
            therapist=self.therapist,
            patient=self.patient_b,
            occurred_at=timezone.make_aware(datetime(2026, 3, 5, 11, 0)),
            program_label='Equilibrio',
            duration_min=30,
            score=Decimal('91.00'),
            status='completada',
        )

    def _search(self, term):
        return self.client.get(reverse('session-list'), {'search': term})

    def test_search_matches_session_id(self):
        r = self._search(str(self.session_a.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['id'], self.session_a.id)

    def test_search_matches_patient_name(self):
        r = self._search('Ana')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['patientName'], 'Ana López')

    def test_search_matches_program(self):
        r = self._search('Movilidad')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['programLabel'], 'Movilidad básica')

    def test_search_matches_date(self):
        r = self._search('2026-02-01')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['id'], self.session_a.id)

    def test_filter_param_session_id(self):
        r = self.client.get(reverse('session-list'), {'sessionId': str(self.session_a.id)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['id'], self.session_a.id)
