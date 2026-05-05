"""Resolución de terapeuta y vínculos activos (HU-01, HU-02, …)."""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser

from RehabWeb_API.models import Therapist, TherapistPatient


def get_therapist_for_user(user: AbstractUser) -> Therapist | None:
    """Perfil `Therapist` asociado al usuario autenticado, o `None`."""
    return (
        Therapist.objects.filter(user=user)
        .select_related('user')
        .first()
    )


def get_active_therapist_patient_link(
    therapist: Therapist,
    patient_id: int,
) -> TherapistPatient | None:
    """Vínculo activo (sin soft delete) entre terapeuta y paciente."""
    return (
        TherapistPatient.objects.filter(
            therapist=therapist,
            patient_id=patient_id,
            deleted_at__isnull=True,
        )
        .select_related('patient')
        .first()
    )
