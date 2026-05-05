"""Serializers de sesión (HU-05)."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone

from RehabWeb_API.serializers import SessionDetailSerializer, SessionListSerializer


class SessionSerializerShapeTests(SimpleTestCase):
    def test_list_serializer_camel_case(self):
        patient = SimpleNamespace(full_name='Paciente Demo')
        obj = SimpleNamespace(
            id=1,
            patient_id=10,
            patient=patient,
            occurred_at=timezone.make_aware(datetime(2026, 2, 1, 10, 0)),
            program_label='Movilidad',
            duration_min=45,
            score=Decimal('82.50'),
            status='completada',
            adherence_percent=88,
        )
        data = SessionListSerializer(obj).data
        self.assertEqual(data['patientId'], 10)
        self.assertEqual(data['patientName'], 'Paciente Demo')
        self.assertEqual(data['programLabel'], 'Movilidad')
        self.assertEqual(data['score'], 82.5)
        self.assertIn('occurredAt', data)

    def test_detail_includes_notes_and_exercises(self):
        patient = SimpleNamespace(full_name='P')
        ex = SimpleNamespace(
            id=1,
            name='Sentadilla',
            sets=3,
            reps=10,
            notes='',
            sort_order=0,
        )
        obj = SimpleNamespace(
            id=2,
            patient_id=1,
            patient=patient,
            occurred_at=timezone.now(),
            program_label='',
            duration_min=None,
            score=None,
            status='',
            adherence_percent=None,
            notes='Nota clínica',
            exercises=[ex],
        )
        data = SessionDetailSerializer(obj).data
        self.assertEqual(data['notes'], 'Nota clínica')
        self.assertEqual(len(data['exercises']), 1)
        self.assertEqual(data['exercises'][0]['name'], 'Sentadilla')
