"""
Agregación de métricas para el tablero (HU-01).

Salida en claves **camelCase** para alinear con el contrato del front Angular.
Los compañeros deben ejecutar migraciones y sembrar datos antes de validar en MySQL.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from RehabWeb_API.models import MetricPoint, Session, Therapist, TherapistPatient
from RehabWeb_API.services.inactivity_rules import get_inactive_patients_for_therapist
from RehabWeb_API.services.therapist_access import get_therapist_for_user
RECENT_SESSIONS_LIMIT = 10
ROM_TEMPORAL_LIMIT_ROWS = 52  # tope defensivo por paciente (AC-03)
METRIC_ROWS_HARD_CAP = 500  # tope global de filas leídas de MetricPoint


def _decimal_to_json_number(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _trend_for_observed_sequence(observed: list[Decimal]) -> list[str]:
    """
    Tendencia N vs N-1 sobre valores observados.
    Devuelve una etiqueta por punto: 'initial' | 'improved' | 'regressed' | 'unchanged'.
    Alineado con la UI (verde / coral / gris): el front puede mapear estos tokens.
    """
    out: list[str] = []
    for i, _ in enumerate(observed):
        if i == 0:
            out.append('initial')
            continue
        prev, curr = observed[i - 1], observed[i]
        if curr > prev:
            out.append('improved')
        elif curr < prev:
            out.append('regressed')
        else:
            out.append('unchanged')
    return out


def _aggregate_metric_rows(
    rows: list[MetricPoint],
) -> list[dict[str, Any]]:
    """
    Promedia meta/observado por (sort_order, period_label) cuando varios pacientes
    aportan el mismo periodo (vista cohorte del terapeuta).
    """
    buckets: dict[tuple[int, str], dict[str, Any]] = {}
    order_keys: list[tuple[int, str]] = []

    for row in rows:
        key = (row.sort_order, row.period_label)
        if key not in buckets:
            buckets[key] = {
                'sortOrder': row.sort_order,
                'periodLabel': row.period_label,
                'metaSum': Decimal('0'),
                'obsSum': Decimal('0'),
                'count': 0,
            }
            order_keys.append(key)
        b = buckets[key]
        b['metaSum'] += row.meta_value
        b['obsSum'] += row.observed_value
        b['count'] += 1

    out: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for key in order_keys:
        if key in seen:
            continue
        seen.add(key)
        b = buckets[key]
        n = b['count']
        out.append(
            {
                'sortOrder': b['sortOrder'],
                'periodLabel': b['periodLabel'],
                'metaValue': _decimal_to_json_number(b['metaSum'] / n),
                'observedValue': _decimal_to_json_number(b['obsSum'] / n),
            }
        )
    return out


def _attach_trends(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed = [
        Decimal(str(p['observedValue']))
        for p in series
        if p.get('observedValue') is not None
    ]
    trends = _trend_for_observed_sequence(observed)
    for i, point in enumerate(series):
        point['trend'] = trends[i] if i < len(trends) else 'initial'
    return series


def _empty_payload(*, therapist_linked: bool) -> dict[str, Any]:
    return {
        'therapistLinked': therapist_linked,
        'inactivitySummary': {
            'inactiveCount': 0,
            'thresholdDays': 3,
            'patients': [],
        },
        'romByWeek': [],
        'temporalSeries': [],
        'recentSessions': [],
        'summaryRings': [],
    }


def build_dashboard_payload(user: AbstractUser) -> dict[str, Any]:
    """
    Construye el cuerpo JSON del dashboard para el usuario autenticado.
    """
    therapist = get_therapist_for_user(user)
    if therapist is None:
        return _empty_payload(therapist_linked=False)

    links = list(
        TherapistPatient.objects.filter(
            therapist=therapist,
            deleted_at__isnull=True,
        ).select_related('patient')
    )
    patient_ids = [link.patient_id for link in links]

    if not patient_ids:
        base = _empty_payload(therapist_linked=True)
        base['summaryRings'] = _compute_summary_rings(therapist, [])
        return base

    inactive_patients = get_inactive_patients_for_therapist(therapist)

    metric_limit = min(
        METRIC_ROWS_HARD_CAP,
        ROM_TEMPORAL_LIMIT_ROWS * max(len(patient_ids), 1),
    )

    rom_rows = list(
        MetricPoint.objects.filter(
            patient_id__in=patient_ids,
            metric_type=MetricPoint.MetricType.ROM_WEEK,
        ).only(
            'sort_order',
            'period_label',
            'meta_value',
            'observed_value',
            'patient_id',
        )[:metric_limit]
    )
    temporal_rows = list(
        MetricPoint.objects.filter(
            patient_id__in=patient_ids,
            metric_type=MetricPoint.MetricType.TEMPORAL,
        ).only(
            'sort_order',
            'period_label',
            'meta_value',
            'observed_value',
            'patient_id',
        )[:metric_limit]
    )

    rom_by_week = _aggregate_metric_rows(rom_rows)
    rom_by_week.sort(key=lambda x: (x['sortOrder'], x['periodLabel']))

    temporal_series = _aggregate_metric_rows(temporal_rows)
    temporal_series.sort(key=lambda x: (x['sortOrder'], x['periodLabel']))
    temporal_series = _attach_trends(temporal_series)

    recent_list = list(
        Session.objects.filter(therapist=therapist, patient_id__in=patient_ids)
        .select_related('patient')
        .order_by('-occurred_at')[:RECENT_SESSIONS_LIMIT]
    )
    recent_sessions = [
        {
            'id': s.id,
            'patientId': s.patient_id,
            'patientName': s.patient.full_name,
            'occurredAt': s.occurred_at.isoformat(),
            'programLabel': s.program_label or '',
            'durationMin': s.duration_min,
            'score': _decimal_to_json_number(s.score),
            'status': s.status or '',
            'adherencePercent': s.adherence_percent,
        }
        for s in recent_list
    ]

    summary_rings = _compute_summary_rings(therapist, recent_list)

    return {
        'therapistLinked': True,
        'inactivitySummary': {
            'inactiveCount': len(inactive_patients),
            'thresholdDays': 3,
            'patients': inactive_patients,
        },
        'romByWeek': rom_by_week,
        'temporalSeries': temporal_series,
        'recentSessions': recent_sessions,
        'summaryRings': summary_rings,
    }


def _compute_summary_rings(
    therapist: Therapist,
    recent_sessions: list[Session],
) -> list[dict[str, Any]]:
    """KPIs simples para anillos / tarjetas del dashboard (extensible).

    ``recent_sessions`` ya viene acotado por ``RECENT_SESSIONS_LIMIT``; la
    métrica de adherencia es por tanto **una media de la ventana reciente**,
    no histórica — se refleja en el label para evitar lecturas erróneas.
    """
    rings: list[dict[str, Any]] = []

    active_links = TherapistPatient.objects.filter(
        therapist=therapist,
        deleted_at__isnull=True,
    ).count()
    ring_cap = max(active_links, 10)
    rings.append(
        {
            'key': 'activePatients',
            'label': 'Pacientes activos',
            'value': active_links,
            'maxValue': ring_cap,
            'unit': 'count',
        }
    )

    adher_values = [
        s.adherence_percent
        for s in recent_sessions
        if s.adherence_percent is not None
    ]
    if adher_values:
        avg = sum(adher_values) / len(adher_values)
        rings.append(
            {
                'key': 'avgAdherenceRecent',
                'label': f'Adherencia media (últimas {len(adher_values)})',
                'value': round(avg, 1),
                'maxValue': 100.0,
                'unit': 'percent',
                'sampleSize': len(adher_values),
            }
        )

    score_values = [
        float(s.score)
        for s in recent_sessions
        if s.score is not None
    ]
    if score_values:
        avg_score = sum(score_values) / len(score_values)
        rings.append(
            {
                'key': 'avgScoreRecent',
                'label': f'Score medio (últimas {len(score_values)})',
                'value': round(avg_score, 2),
                'maxValue': 10.0,
                'unit': 'score',
                'sampleSize': len(score_values),
            }
        )

    return rings
