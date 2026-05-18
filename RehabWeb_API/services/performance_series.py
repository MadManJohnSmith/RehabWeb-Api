"""
Series de desempeño (meta vs observado) para HU-04.

Usa ``MetricPoint`` con ``metric_type=temporal``. La fórmula de *recovery score*
está documentada como versión **placeholder** hasta disponer de la figura oficial
en `Historias de Usuario Modulo 5` (`image-20260311-233530.png`).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from RehabWeb_API.models import MetricPoint, Patient
from RehabWeb_API.services.therapist_access import get_active_therapist_patient_link

MAX_COMPARE_PATIENTS = 12
SERIES_ROW_CAP = 250
FORMULA_VERSION = 'hu04-placeholder-v1'


def _decimal_to_float(value: Decimal) -> float:
    return float(value)


def _trend_for_observed(values: list[float]) -> list[str]:
    out: list[str] = []
    for i, _ in enumerate(values):
        if i == 0:
            out.append('initial')
            continue
        prev, curr = values[i - 1], values[i]
        if curr > prev:
            out.append('improved')
        elif curr < prev:
            out.append('regressed')
        else:
            out.append('unchanged')
    return out


def fetch_temporal_metric_points(patient_id: int) -> list[MetricPoint]:
    return list(
        MetricPoint.objects.filter(
            patient_id=patient_id,
            metric_type=MetricPoint.MetricType.TEMPORAL,
        )
        .only(
            'sort_order',
            'period_label',
            'meta_value',
            'observed_value',
        )
        .order_by('sort_order', 'period_label')[:SERIES_ROW_CAP]
    )


def metric_points_to_series_rows(points: list[MetricPoint]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mp in points:
        rows.append(
            {
                'sortOrder': mp.sort_order,
                'periodLabel': mp.period_label,
                'metaValue': _decimal_to_float(mp.meta_value),
                'observedValue': _decimal_to_float(mp.observed_value),
            }
        )
    obs = [r['observedValue'] for r in rows]
    trends = _trend_for_observed(obs)
    for i, r in enumerate(rows):
        r['trend'] = trends[i] if i < len(trends) else 'initial'
    return rows


def recovery_score_percent(
    initial_observed: Decimal,
    final_observed: Decimal,
    final_meta: Decimal,
) -> float | None:
    """
    Placeholder HU-04: progreso relativo respecto a la meta del último periodo.

    .. math::

        R_{\\%} = 100 \\cdot \\frac{O_n - O_0}{M_n - O_0}

    Donde :math:`O_0` = observado del primer punto, :math:`O_n` = observado del
    último, :math:`M_n` = meta del último periodo (objetivo actual en la serie).

    Si el denominador es 0 se devuelve ``None`` (indeterminado).
    """
    denom = final_meta - initial_observed
    if denom == 0:
        return None
    return float((final_observed - initial_observed) / denom * 100)


def compute_series_summary(series: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen numérico + score a partir de filas ya serializadas."""
    if not series:
        return {
            'formulaVersion': FORMULA_VERSION,
            'initialMeta': None,
            'initialObserved': None,
            'finalMeta': None,
            'finalObserved': None,
            'recoveryScorePercent': None,
        }
    first, last = series[0], series[-1]
    o0 = Decimal(str(first['observedValue']))
    on = Decimal(str(last['observedValue']))
    mn = Decimal(str(last['metaValue']))
    m0 = Decimal(str(first['metaValue']))
    score = recovery_score_percent(o0, on, mn)
    return {
        'formulaVersion': FORMULA_VERSION,
        'initialMeta': first['metaValue'],
        'initialObserved': first['observedValue'],
        'finalMeta': last['metaValue'],
        'finalObserved': last['observedValue'],
        'initialPeriodLabel': first.get('periodLabel'),
        'finalPeriodLabel': last.get('periodLabel'),
        'recoveryScorePercent': score,
        'note': (
            'recoveryScorePercent es placeholder hasta validar con la figura oficial de la HU-04.'
        ),
    }


def build_patient_performance_payload(
    *,
    patient_id: int,
    full_name: str,
) -> dict[str, Any]:
    points = fetch_temporal_metric_points(patient_id)
    temporal_series = metric_points_to_series_rows(points)
    summary = compute_series_summary(temporal_series)
    return {
        'patientId': patient_id,
        'fullName': full_name,
        'temporalSeries': temporal_series,
        'summary': summary,
    }


def resolve_patient_for_therapist(
    therapist,
    patient_id: int,
) -> tuple[str, dict[str, Any] | None]:
    """
    Devuelve ``('not_found'|'forbidden'|'ok', payload|None)``.
    """
    if not Patient.objects.filter(pk=patient_id).exists():
        return 'not_found', None
    link = get_active_therapist_patient_link(therapist, patient_id)
    if link is None:
        return 'forbidden', None
    payload = build_patient_performance_payload(
        patient_id=patient_id,
        full_name=link.patient.full_name,
    )
    return 'ok', payload


def resolve_patients_batch(
    therapist,
    patient_ids: list[int],
) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
    """
    Versión batch de :func:`resolve_patient_for_therapist` para HU-04 compare.

    Resuelve N pacientes en O(1) queries por grupo (no por paciente):
    1× SELECT pacientes existentes, 1× SELECT vínculos activos del terapeuta,
    1× SELECT MetricPoint para todos los pacientes autorizados.

    Devuelve ``(status_by_id, payload_by_id)`` donde ``status`` ∈
    ``{'not_found', 'forbidden', 'ok'}``. Sólo los ``ok`` aparecen en
    ``payload_by_id``.
    """
    from RehabWeb_API.models import TherapistPatient

    ids = list(dict.fromkeys(patient_ids))
    if not ids:
        return {}, {}

    existing_ids = set(
        Patient.objects.filter(pk__in=ids).values_list('pk', flat=True)
    )
    authorized_links = {
        link.patient_id: link
        for link in TherapistPatient.objects
        .filter(
            therapist=therapist,
            patient_id__in=existing_ids,
            deleted_at__isnull=True,
        )
        .select_related('patient')
    }
    authorized_ids = set(authorized_links.keys())

    points_by_patient: dict[int, list[MetricPoint]] = {}
    if authorized_ids:
        for mp in (
            MetricPoint.objects.filter(
                patient_id__in=authorized_ids,
                metric_type=MetricPoint.MetricType.TEMPORAL,
            )
            .only(
                'patient_id',
                'sort_order',
                'period_label',
                'meta_value',
                'observed_value',
            )
            .order_by('patient_id', 'sort_order', 'period_label')
        ):
            points_by_patient.setdefault(mp.patient_id, []).append(mp)

    status_by_id: dict[int, str] = {}
    payload_by_id: dict[int, dict[str, Any]] = {}
    for pid in ids:
        if pid not in existing_ids:
            status_by_id[pid] = 'not_found'
            continue
        if pid not in authorized_ids:
            status_by_id[pid] = 'forbidden'
            continue
        link = authorized_links[pid]
        points = points_by_patient.get(pid, [])[:SERIES_ROW_CAP]
        temporal_series = metric_points_to_series_rows(points)
        summary = compute_series_summary(temporal_series)
        status_by_id[pid] = 'ok'
        payload_by_id[pid] = {
            'patientId': pid,
            'fullName': link.patient.full_name,
            'temporalSeries': temporal_series,
            'summary': summary,
        }
    return status_by_id, payload_by_id


def compute_group_bounds(patients_payload: list[dict[str, Any]]) -> dict[str, float]:
    """Límites sugeridos para escala común en gráfico grupal."""
    all_obs: list[float] = []
    all_meta: list[float] = []
    for block in patients_payload:
        for row in block.get('temporalSeries') or []:
            all_obs.append(row['observedValue'])
            all_meta.append(row['metaValue'])
    if not all_obs:
        return {
            'minObserved': 0.0,
            'maxObserved': 1.0,
            'minMeta': 0.0,
            'maxMeta': 1.0,
        }
    return {
        'minObserved': min(all_obs),
        'maxObserved': max(all_obs),
        'minMeta': min(all_meta),
        'maxMeta': max(all_meta),
    }
