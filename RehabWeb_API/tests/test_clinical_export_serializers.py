"""Validación del cuerpo de exportación clínica (HU-02)."""

from datetime import date

from django.test import SimpleTestCase

from RehabWeb_API.serializers import ClinicalExportRequestSerializer


class ClinicalExportRequestSerializerTests(SimpleTestCase):
    def test_valid_payload(self):
        ser = ClinicalExportRequestSerializer(
            data={
                'patientId': 1,
                'dateFrom': '2026-01-01',
                'dateTo': '2026-01-31',
                'format': 'pdf',
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_date_order_invalid(self):
        ser = ClinicalExportRequestSerializer(
            data={
                'patientId': 1,
                'dateFrom': '2026-02-01',
                'dateTo': '2026-01-01',
                'format': 'xlsx',
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn('dateTo', ser.errors)

    def test_range_too_long(self):
        ser = ClinicalExportRequestSerializer(
            data={
                'patientId': 1,
                'dateFrom': '2024-01-01',
                'dateTo': '2026-06-01',
                'format': 'pdf',
            }
        )
        self.assertFalse(ser.is_valid())
