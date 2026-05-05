"""Generación binaria PDF/XLSX sin tocar ORM (HU-02)."""

from datetime import date

from django.test import SimpleTestCase

from RehabWeb_API.services.clinical_export import build_pdf_bytes, build_xlsx_bytes


class ClinicalExportBuildTests(SimpleTestCase):
    def test_xlsx_non_empty(self):
        raw = build_xlsx_bytes(
            [],
            patient_name='Paciente Demo',
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            diagnosis='Test',
        )
        self.assertGreater(len(raw), 50)
        self.assertTrue(raw.startswith(b'PK'))

    def test_pdf_non_empty(self):
        raw = build_pdf_bytes(
            [],
            patient_name='Paciente Demo',
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            diagnosis='Test',
            therapist_username='doc1',
        )
        self.assertGreater(len(raw), 100)
        self.assertTrue(raw.startswith(b'%PDF'))
