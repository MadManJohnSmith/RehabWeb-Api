"""Tests HTTP — registro de pacientes y vínculos (HU-06)."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from RehabWeb_API.models import Patient, Session, Therapist, TherapistPatient


def _token_client(client, user):
    client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')


class PatientListAuthTests(APITestCase):
    def test_anonymous_401(self):
        self.assertEqual(self.client.get(reverse('patient-list')).status_code, 401)

    @patch(
        'RehabWeb_API.views.patient_management.get_therapist_for_user',
        return_value=None,
    )
    def test_no_therapist_403(self, _mock_th):
        user = User.objects.create_user('hu6a', 'hu6a@e.com', 'pw12345678')
        _token_client(self.client, user)
        self.assertEqual(self.client.get(reverse('patient-list')).status_code, 403)


class PatientManagementFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('hu6flow', 'hu6flow@e.com', 'pw12345678')
        self.therapist = Therapist.objects.create(user=self.user)
        _token_client(self.client, self.user)

    def test_link_list_patch_unlink_restore_ficha(self):
        r = self.client.post(
            reverse('patient-link'),
            data={
                'associationId': 'EXT-1',
                'fullName': 'Ana López',
                'primaryDiagnosis': 'Tendinitis',
                'clinicalStatus': 'activo',
            },
            format='json',
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['fullName'], 'Ana López')
        self.assertEqual(r.data['associationId'], 'EXT-1')
        self.assertEqual(r.data['clinicalStatus'], 'activo')
        self.assertFalse(r.data['isUnlinked'])
        link_id = r.data['linkId']
        patient_id = r.data['patientId']

        Session.objects.create(
            therapist=self.therapist,
            patient_id=patient_id,
            occurred_at=timezone.now(),
            program_label='Test',
        )

        r_list = self.client.get(reverse('patient-list'))
        self.assertEqual(r_list.status_code, 200)
        self.assertEqual(r_list.data['count'], 1)
        row = r_list.data['results'][0]
        self.assertIsNotNone(row['lastSessionAt'])

        r_patch = self.client.patch(
            reverse('therapist-patient-detail', kwargs={'link_id': link_id}),
            data={'clinicalStatus': 'riesgo', 'primaryDiagnosis': 'Revisión'},
            format='json',
        )
        self.assertEqual(r_patch.status_code, 200)
        self.assertEqual(r_patch.data['clinicalStatus'], 'riesgo')
        self.assertEqual(r_patch.data['primaryDiagnosis'], 'Revisión')

        r_ficha = self.client.get(reverse('patient-detail', kwargs={'pk': patient_id}))
        self.assertEqual(r_ficha.status_code, 200)
        self.assertEqual(r_ficha.data['patientId'], patient_id)

        self.assertEqual(
            self.client.post(
                reverse('therapist-patient-unlink', kwargs={'link_id': link_id}),
            ).status_code,
            200,
        )
        r_after = self.client.get(reverse('patient-list'))
        self.assertEqual(r_after.data['count'], 0)

        r_inc = self.client.get(
            reverse('patient-list'),
            {'includeDeleted': 'true'},
        )
        self.assertEqual(r_inc.data['count'], 1)
        self.assertTrue(r_inc.data['results'][0]['isUnlinked'])

        self.assertEqual(
            self.client.post(
                reverse('therapist-patient-restore', kwargs={'link_id': link_id}),
            ).status_code,
            200,
        )
        r_ok = self.client.get(reverse('patient-list'))
        self.assertEqual(r_ok.data['count'], 1)
        self.assertFalse(r_ok.data['results'][0]['isUnlinked'])

    def test_ficha_404_sin_vinculo(self):
        orphan = Patient.objects.create(external_id='x', full_name='Solo')
        self.assertEqual(
            self.client.get(reverse('patient-detail', kwargs={'pk': orphan.pk})).status_code,
            404,
        )

    def test_link_conflicto_otro_terapeuta_409(self):
        self.client.post(
            reverse('patient-link'),
            data={'associationId': 'SHARED', 'fullName': 'Compartido'},
            format='json',
        )
        u2 = User.objects.create_user('hu6b', 'hu6b@e.com', 'pw12345678')
        Therapist.objects.create(user=u2)
        _token_client(self.client, u2)
        r = self.client.post(
            reverse('patient-link'),
            data={'associationId': 'SHARED', 'fullName': 'Otro nombre'},
            format='json',
        )
        self.assertEqual(r.status_code, 409)
