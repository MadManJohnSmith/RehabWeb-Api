"""Serializers HU-04."""

from django.test import SimpleTestCase

from RehabWeb_API.serializers import PerformanceCompareRequestSerializer
from RehabWeb_API.services.performance_series import MAX_COMPARE_PATIENTS


class PerformanceCompareSerializerTests(SimpleTestCase):
    def test_valid_ids(self):
        ser = PerformanceCompareRequestSerializer(data={'patientIds': [1, 2, 3]})
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_rejects_duplicates(self):
        ser = PerformanceCompareRequestSerializer(data={'patientIds': [1, 1]})
        self.assertFalse(ser.is_valid())

    def test_rejects_too_many(self):
        ids = list(range(1, MAX_COMPARE_PATIENTS + 3))
        ser = PerformanceCompareRequestSerializer(data={'patientIds': ids})
        self.assertFalse(ser.is_valid())
