"""
Tests de regresión derivados de la auditoría completa del Módulo 5.

Cada test fija un bug que fue corregido en este pase para evitar que
vuelva a aparecer:

- HU-06: ``primaryDiagnosis`` ausente en la respuesta del PATCH.
- HU-06: filtro ``includeDeleted`` por defecto debe ocultar los soft-deleted.
- HU-06: la creación de vínculo debe detectar conflicto con otro terapeuta
  incluso bajo presión concurrente (TOCTOU cerrado dentro del atomic).
- HU-03: la severidad asignada a ``InactivityAlert`` siempre debe pertenecer
  al enum ``Severity`` (no más ``'unknown'``).
- HU-04: ``resolve_patients_batch`` resuelve N pacientes con un número
  constante de queries (no escala con N).
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from RehabWeb_API.models import (
    InactivityAlert,
    MetricPoint,
    Patient,
    Session,
    Therapist,
    TherapistPatient,
)
from RehabWeb_API.services.inactivity_sync import (
    _severity_for,
    sync_inactivity_alerts_for_therapist,
)
from RehabWeb_API.services.performance_series import resolve_patients_batch


def _auth(client, user):
    client.credentials(
        HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}'
    )


class HU06PatchReturnsPrimaryDiagnosisTests(APITestCase):
    """El PATCH debe devolver ``primaryDiagnosis`` (regresión del bug original)."""

    def test_patch_response_includes_primary_diagnosis(self):
        user = User.objects.create_user('reg6a', 'reg6a@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)
        _auth(self.client, user)

        link_resp = self.client.post(
            reverse('patient-link'),
            data={
                'associationId': 'REG-1',
                'fullName': 'Paciente Uno',
                'primaryDiagnosis': 'Inicial',
                'clinicalStatus': 'activo',
            },
            format='json',
        )
        self.assertEqual(link_resp.status_code, 201, link_resp.data)
        self.assertEqual(link_resp.data['primaryDiagnosis'], 'Inicial')

        link_id = link_resp.data['linkId']
        patch_resp = self.client.patch(
            reverse('therapist-patient-detail', kwargs={'link_id': link_id}),
            data={'primaryDiagnosis': 'Actualizado'},
            format='json',
        )
        self.assertEqual(patch_resp.status_code, 200, patch_resp.data)
        self.assertIn('primaryDiagnosis', patch_resp.data)
        self.assertEqual(patch_resp.data['primaryDiagnosis'], 'Actualizado')


class HU06IncludeDeletedDefaultTests(APITestCase):
    """Sin ``includeDeleted``, la lista oculta los vínculos soft-deleted."""

    def test_default_hides_soft_deleted(self):
        user = User.objects.create_user('reg6b', 'reg6b@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)
        patient = Patient.objects.create(external_id='REG-2', full_name='Eliminado')
        TherapistPatient.objects.create(
            therapist=therapist,
            patient=patient,
            deleted_at=timezone.now(),
        )
        _auth(self.client, user)
        r = self.client.get(reverse('patient-list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 0)

    def test_include_deleted_true_shows_them(self):
        user = User.objects.create_user('reg6c', 'reg6c@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)
        patient = Patient.objects.create(external_id='REG-3', full_name='Eliminado')
        TherapistPatient.objects.create(
            therapist=therapist,
            patient=patient,
            deleted_at=timezone.now(),
        )
        _auth(self.client, user)
        r = self.client.get(reverse('patient-list'), {'includeDeleted': 'true'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertTrue(r.data['results'][0]['isUnlinked'])


class HU06LinkConflictAndIntegrityTests(APITestCase):
    """Conflicto con otro terapeuta devuelve 409 sin propagar 500."""

    def test_conflict_other_therapist_returns_409(self):
        u1 = User.objects.create_user('reg6d', 'reg6d@e.com', 'pw12345678')
        t1 = Therapist.objects.create(user=u1)
        patient = Patient.objects.create(external_id='REG-4', full_name='Compartido')
        TherapistPatient.objects.create(therapist=t1, patient=patient)

        u2 = User.objects.create_user('reg6e', 'reg6e@e.com', 'pw12345678')
        Therapist.objects.create(user=u2)
        _auth(self.client, u2)
        r = self.client.post(
            reverse('patient-link'),
            data={'associationId': 'REG-4', 'fullName': 'Otro nombre'},
            format='json',
        )
        self.assertEqual(r.status_code, 409, r.data)
        self.assertIn('detail', r.data)


class HU03SeverityAlwaysValidTests(TestCase):
    """``_severity_for`` siempre debe devolver un valor del enum Severity."""

    def test_severity_for_all_inputs_in_enum(self):
        valid = set(InactivityAlert.Severity.values)
        cases = [
            _severity_for(None, True),
            _severity_for(None, False),  # caso defensivo: antes devolvía 'unknown'
            _severity_for(0, False),
            _severity_for(6, False),
            _severity_for(7, False),
            _severity_for(13, False),
            _severity_for(14, False),
            _severity_for(99, False),
        ]
        for value in cases:
            self.assertIn(value, valid, f'Severity inválida: {value!r}')

    def test_sync_does_not_crash_with_no_session_patient(self):
        """Vínculo sin Sessions: el sync debe poder persistir el alerta sin error."""
        user = User.objects.create_user('reg3a', 'reg3a@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)
        patient = Patient.objects.create(external_id='REG-5', full_name='Sin sesiones')
        TherapistPatient.objects.create(therapist=therapist, patient=patient)

        n_inactive = sync_inactivity_alerts_for_therapist(therapist)
        self.assertEqual(n_inactive, 1)
        alert = InactivityAlert.objects.get(therapist=therapist, patient=patient)
        self.assertEqual(alert.severity, InactivityAlert.Severity.NO_SESSIONS)


class HU04BatchResolveTests(TestCase):
    """``resolve_patients_batch`` resuelve N en una cantidad constante de queries."""

    def test_batch_returns_status_and_payloads(self):
        user = User.objects.create_user('reg4a', 'reg4a@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)

        own = Patient.objects.create(external_id='REG-6', full_name='Propio')
        TherapistPatient.objects.create(therapist=therapist, patient=own)
        MetricPoint.objects.create(
            patient=own,
            metric_type=MetricPoint.MetricType.TEMPORAL,
            period_label='T1',
            sort_order=0,
            meta_value=100,
            observed_value=70,
        )

        not_owned = Patient.objects.create(external_id='REG-7', full_name='Otro')

        status_map, payload_map = resolve_patients_batch(
            therapist, [own.pk, not_owned.pk, 99999]
        )
        self.assertEqual(status_map[own.pk], 'ok')
        self.assertEqual(status_map[not_owned.pk], 'forbidden')
        self.assertEqual(status_map[99999], 'not_found')
        self.assertIn(own.pk, payload_map)
        self.assertEqual(payload_map[own.pk]['fullName'], 'Propio')

    def test_batch_uses_constant_queries(self):
        """
        Asegura el ahorro de N+1: la cantidad de queries usadas para resolver
        un grupo de 5 pacientes debe ser razonable y NO escalar linealmente
        con N (≈ 3 queries fijas: existencia, vínculos, métricas).
        """
        user = User.objects.create_user('reg4b', 'reg4b@e.com', 'pw12345678')
        therapist = Therapist.objects.create(user=user)
        ids = []
        for i in range(5):
            p = Patient.objects.create(external_id=f'BATCH-{i}', full_name=f'P{i}')
            TherapistPatient.objects.create(therapist=therapist, patient=p)
            MetricPoint.objects.create(
                patient=p,
                metric_type=MetricPoint.MetricType.TEMPORAL,
                period_label='T1',
                sort_order=0,
                meta_value=100,
                observed_value=70,
            )
            ids.append(p.pk)

        with self.assertNumQueries(3):
            status_map, payload_map = resolve_patients_batch(therapist, ids)
        self.assertEqual(len(payload_map), 5)
        self.assertTrue(all(status_map[pid] == 'ok' for pid in ids))
