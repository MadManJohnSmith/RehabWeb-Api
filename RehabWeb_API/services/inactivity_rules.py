"""
Reglas de inactividad (HU-03) compartidas con el dashboard (HU-01).

- Última sesión: máximo ``Session.occurred_at`` por **par (terapeuta, paciente)**.
- Inactivo: sin sesiones **o** ``(ahora - última sesión) > timedelta(days=3)`` (más de 72 h).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Max
from django.utils import timezone

from RehabWeb_API.models import Session, Therapist, TherapistPatient

INACTIVITY_THRESHOLD = timedelta(days=3)


def last_session_times_by_patient(
    therapist: Therapist,
    patient_ids: list[int],
) -> dict[int, Any]:
    """``patient_id`` → última ``occurred_at`` (aware) o ausencia de clave si no hay sesiones."""
    if not patient_ids:
        return {}
    return {
        row['patient_id']: row['last_at']
        for row in Session.objects.filter(
            therapist=therapist,
            patient_id__in=patient_ids,
        )
        .values('patient_id')
        .annotate(last_at=Max('occurred_at'))
    }


def get_inactive_patients_for_therapist(
    therapist: Therapist,
    *,
    now=None,
) -> list[dict[str, Any]]:
    """
    Filas listas para JSON (camelCase) alineadas con el banner / tabla de alertas.

    Cada elemento: ``patientId``, ``fullName``, ``daysSinceLastSession``, ``lastSessionAt``.
    """
    now = now or timezone.now()
    links = list(
        TherapistPatient.objects.filter(
            therapist=therapist,
            deleted_at__isnull=True,
        ).select_related('patient')
    )
    patient_ids = [link.patient_id for link in links]
    last_by_patient = last_session_times_by_patient(therapist, patient_ids)

    rows: list[dict[str, Any]] = []
    for link in links:
        pid = link.patient_id
        last_at = last_by_patient.get(pid)
        if last_at is None:
            inactive = True
            days_since = None
        else:
            inactive = (now - last_at) > INACTIVITY_THRESHOLD
            days_since = (now.date() - last_at.date()).days

        if inactive:
            rows.append(
                {
                    'patientId': pid,
                    'fullName': link.patient.full_name,
                    'daysSinceLastSession': days_since,
                    'lastSessionAt': last_at.isoformat() if last_at else None,
                }
            )
    rows.sort(
        key=lambda r: (
            r['daysSinceLastSession'] if r['daysSinceLastSession'] is not None else 10**6
        ),
        reverse=True,
    )
    return rows
