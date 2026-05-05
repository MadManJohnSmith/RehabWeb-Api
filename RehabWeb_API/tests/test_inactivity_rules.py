"""Regla temporal de inactividad (HU-03)."""

from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from RehabWeb_API.services.inactivity_rules import INACTIVITY_THRESHOLD


class InactivityThresholdTests(SimpleTestCase):
    def test_within_threshold_not_inactive(self):
        now = timezone.now()
        last = now - timedelta(days=2)
        self.assertFalse((now - last) > INACTIVITY_THRESHOLD)

    def test_beyond_threshold_inactive(self):
        now = timezone.now()
        last = now - timedelta(days=4)
        self.assertTrue((now - last) > INACTIVITY_THRESHOLD)
