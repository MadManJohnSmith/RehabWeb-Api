"""
Materialización de alertas en tabla ``InactivityAlert`` (HU-03).

El comando ``refresh_inactivity_alerts`` llama a ``sync_all_inactivity_alerts``.
La API HTTP puede servir datos **en vivo** vía ``inactivity_rules`` sin depender
de esta tabla; la tabla queda para auditoría, informes y comprobación del job diario.
"""

from __future__ import annotations

import logging
from django.db import transaction
from django.utils import timezone

from RehabWeb_API.models import InactivityAlert, Therapist, TherapistPatient
from RehabWeb_API.services.inactivity_rules import (
    INACTIVITY_THRESHOLD,
    last_session_times_by_patient,
)

logger = logging.getLogger(__name__)


def _severity_for(days_since: int | None, has_never_session: bool) -> str:
    if has_never_session:
        return 'no_sessions'
    if days_since is None:
        return 'unknown'
    if days_since >= 14:
        return 'high'
    if days_since >= 7:
        return 'medium'
    return 'low'


def sync_inactivity_alerts_for_therapist(therapist: Therapist) -> int:
    """
    Actualiza filas ``InactivityAlert`` para un terapeuta.
    Devuelve cuántos pacientes quedaron marcados como inactivos.
    """
    now = timezone.now()
    links = list(
        TherapistPatient.objects.filter(
            therapist=therapist,
            deleted_at__isnull=True,
        ).select_related('patient')
    )
    patient_ids = [link.patient_id for link in links]
    last_map = last_session_times_by_patient(therapist, patient_ids)

    inactive_count = 0
    inactive_patient_ids: set[int] = set()

    with transaction.atomic():
        for link in links:
            pid = link.patient_id
            last_at = last_map.get(pid)
            if last_at is None:
                inactive = True
                days_since = None
            else:
                inactive = (now - last_at) > INACTIVITY_THRESHOLD
                days_since = (now.date() - last_at.date()).days

            if inactive:
                inactive_count += 1
                inactive_patient_ids.add(pid)
                InactivityAlert.objects.update_or_create(
                    therapist=therapist,
                    patient_id=pid,
                    defaults={
                        'days_since_last_session': days_since,
                        'last_session_at': last_at,
                        'severity': _severity_for(days_since, last_at is None),
                    },
                )

        if inactive_patient_ids:
            InactivityAlert.objects.filter(therapist=therapist).exclude(
                patient_id__in=inactive_patient_ids
            ).delete()
        else:
            InactivityAlert.objects.filter(therapist=therapist).delete()

    return inactive_count


def sync_all_inactivity_alerts() -> tuple[int, int]:
    """
    Recorre todos los terapeutas.
    Devuelve ``(n_terapeutas_procesados, total_pacientes_inactivos_sumados)``.
    """
    therapists = list(Therapist.objects.all().iterator())
    total_inactive = 0
    for th in therapists:
        n = sync_inactivity_alerts_for_therapist(th)
        total_inactive += n
        logger.info(
            'inactivity_sync therapist_id=%s inactive_patients=%s',
            th.pk,
            n,
        )
    return len(therapists), total_inactive
