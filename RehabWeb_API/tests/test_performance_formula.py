"""Fórmula de progreso HU-04 (placeholder documentado)."""

from decimal import Decimal

from django.test import SimpleTestCase

from RehabWeb_API.services.performance_series import (
    compute_series_summary,
    recovery_score_percent,
)


class RecoveryScoreFormulaTests(SimpleTestCase):
    def test_half_progress(self):
        # O0=50, On=75, Mn=100 -> (75-50)/(100-50)*100 = 50%
        r = recovery_score_percent(
            Decimal('50'),
            Decimal('75'),
            Decimal('100'),
        )
        self.assertAlmostEqual(r, 50.0)

    def test_zero_denominator_returns_none(self):
        r = recovery_score_percent(
            Decimal('10'),
            Decimal('20'),
            Decimal('10'),
        )
        self.assertIsNone(r)

    def test_empty_series_summary(self):
        s = compute_series_summary([])
        self.assertIsNone(s['recoveryScorePercent'])


class ComputeSeriesSummaryTests(SimpleTestCase):
    def test_basic_series(self):
        series = [
            {
                'sortOrder': 0,
                'periodLabel': 'S1',
                'metaValue': 100.0,
                'observedValue': 50.0,
                'trend': 'initial',
            },
            {
                'sortOrder': 1,
                'periodLabel': 'S2',
                'metaValue': 100.0,
                'observedValue': 75.0,
                'trend': 'improved',
            },
        ]
        s = compute_series_summary(series)
        self.assertEqual(s['initialObserved'], 50.0)
        self.assertEqual(s['finalObserved'], 75.0)
        self.assertIsNotNone(s['recoveryScorePercent'])
