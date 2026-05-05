"""
Consultas reutilizables para vínculos terapeuta–paciente (HU-06).
"""

from __future__ import annotations

from django.db.models import OuterRef, Subquery

from RehabWeb_API.models import Session, Therapist, TherapistPatient


def therapist_patient_base_queryset(therapist: Therapist):
    """
    ``TherapistPatient`` del terapeuta con ``last_session_at`` anotado
    (última ``Session`` del par terapeuta–paciente).
    """
    last_sq = (
        Session.objects.filter(
            therapist_id=therapist.pk,
            patient_id=OuterRef('patient_id'),
        )
        .order_by('-occurred_at')
        .values('occurred_at')[:1]
    )
    return (
        TherapistPatient.objects.filter(therapist=therapist)
        .select_related('patient')
        .annotate(last_session_at=Subquery(last_sq))
    )
