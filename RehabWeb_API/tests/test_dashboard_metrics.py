"""Tests de lógica pura del dashboard (sin tablas del app si no hay migraciones)."""

from decimal import Decimal

from django.test import SimpleTestCase

from RehabWeb_API.services.dashboard_metrics import (
    _aggregate_metric_rows,
    _attach_trends,
    _trend_for_observed_sequence,
)


class TrendSequenceTests(SimpleTestCase):
    def test_initial_and_improved(self):
        obs = [Decimal('10'), Decimal('12'), Decimal('11')]
        self.assertEqual(
            _trend_for_observed_sequence(obs),
            ['initial', 'improved', 'regressed'],
        )

    def test_unchanged(self):
        obs = [Decimal('5'), Decimal('5')]
        self.assertEqual(
            _trend_for_observed_sequence(obs),
            ['initial', 'unchanged'],
        )


class AggregateMetricRowsTests(SimpleTestCase):
    class _Row:
        __slots__ = (
            'sort_order',
            'period_label',
            'meta_value',
            'observed_value',
            'patient_id',
        )

        def __init__(
            self,
            *,
            sort_order: int,
            period_label: str,
            meta_value: Decimal,
            observed_value: Decimal,
            patient_id: int = 1,
        ):
            self.sort_order = sort_order
            self.period_label = period_label
            self.meta_value = meta_value
            self.observed_value = observed_value
            self.patient_id = patient_id

    def test_averages_same_period_two_patients(self):
        rows = [
            self._Row(
                sort_order=1,
                period_label='S1',
                meta_value=Decimal('10'),
                observed_value=Decimal('8'),
                patient_id=1,
            ),
            self._Row(
                sort_order=1,
                period_label='S1',
                meta_value=Decimal('20'),
                observed_value=Decimal('12'),
                patient_id=2,
            ),
        ]
        out = _aggregate_metric_rows(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['periodLabel'], 'S1')
        self.assertEqual(out[0]['metaValue'], 15.0)
        self.assertEqual(out[0]['observedValue'], 10.0)


class AttachTrendsTests(SimpleTestCase):
    def test_trends_keys(self):
        series = [
            {
                'sortOrder': 0,
                'periodLabel': 'A',
                'metaValue': 100.0,
                'observedValue': 50.0,
            },
            {
                'sortOrder': 1,
                'periodLabel': 'B',
                'metaValue': 100.0,
                'observedValue': 60.0,
            },
        ]
        out = _attach_trends(series)
        self.assertEqual(out[0]['trend'], 'initial')
        self.assertEqual(out[1]['trend'], 'improved')
