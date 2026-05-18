"""Vistas API — Registro de pacientes y vínculos (HU-06)."""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.filters import TherapistPatientListFilter
from RehabWeb_API.models import Patient, TherapistPatient
from RehabWeb_API.serializers import (
    PatientLinkRequestSerializer,
    TherapistPatientPatchSerializer,
    TherapistPatientRowSerializer,
)
from RehabWeb_API.services.patient_links import therapist_patient_base_queryset
from RehabWeb_API.services.therapist_access import get_therapist_for_user
from RehabWeb_API.pagination import APIPageNumberPagination

logger = logging.getLogger(__name__)


class TherapistPatientListAPIView(generics.ListAPIView):
    """
    ``GET /api/v1/patients/`` — vínculos del terapeuta con última sesión anotada.

    Query: ``q``, ``clinicalStatus``, ``includeDeleted`` (boolean).
    """

    serializer_class = TherapistPatientRowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = TherapistPatientListFilter
    ordering_fields = ('id', 'patient__full_name')
    ordering = ('-id',)
    pagination_class = APIPageNumberPagination

    def get_queryset(self):
        therapist = get_therapist_for_user(self.request.user)
        if therapist is None:
            return TherapistPatient.objects.none()
        qs = therapist_patient_base_queryset(therapist)
        # Por defecto ocultamos los vínculos soft-deleted; el cliente puede
        # pedirlos con ``?includeDeleted=true``. El método del FilterSet
        # solo se ejecuta si el parámetro está presente, por lo que la
        # exclusión por defecto debe hacerse aquí.
        raw = self.request.query_params.get('includeDeleted', '')
        if raw.strip().lower() not in ('true', '1', 'yes', 'on'):
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def list(self, request, *args, **kwargs):
        if get_therapist_for_user(request.user) is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        return super().list(request, *args, **kwargs)


class PatientFichaAPIView(APIView):
    """``GET /api/v1/patients/<pk>/`` — ficha (vínculo preferente activo)."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        base = therapist_patient_base_queryset(therapist).filter(patient_id=pk)
        link = base.filter(deleted_at__isnull=True).first()
        if link is None:
            link = base.order_by('-id').first()
        if link is None:
            raise Http404
        return Response(TherapistPatientRowSerializer(link).data)


class PatientLinkAPIView(APIView):
    """``POST /api/v1/patients/link/`` — crear o reutilizar paciente y vínculo."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')

        ser = PatientLinkRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        assoc = (data.get('associationId') or '').strip()
        full_name = data['fullName'].strip()
        diag = (data.get('primaryDiagnosis') or '').strip()
        cstat = data['clinicalStatus']

        if not full_name:
            return Response(
                {'fullName': ['Este campo no puede estar vacío.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            link, http_status = self._link_atomic(
                therapist=therapist,
                assoc=assoc,
                full_name=full_name,
                diag=diag,
                cstat=cstat,
            )
        except _PatientConflictError:
            return Response(
                {'detail': 'Este paciente ya está vinculado a otro terapeuta.'},
                status=status.HTTP_409_CONFLICT,
            )
        except IntegrityError:
            # Carrera contra otra request: ya hay un vínculo activo del
            # mismo terapeuta con este paciente. Devolvemos el actual.
            logger.warning(
                'PatientLink integrity race user=%s assoc=%s',
                getattr(request.user, 'pk', None),
                assoc,
            )
            existing_patient = (
                Patient.objects.filter(external_id=assoc).first()
                if assoc else None
            )
            if existing_patient is None:
                return Response(
                    {'detail': 'No fue posible vincular al paciente.'},
                    status=status.HTTP_409_CONFLICT,
                )
            existing_link = TherapistPatient.objects.filter(
                therapist=therapist,
                patient=existing_patient,
                deleted_at__isnull=True,
            ).first()
            if existing_link is None:
                return Response(
                    {'detail': 'No fue posible vincular al paciente.'},
                    status=status.HTTP_409_CONFLICT,
                )
            link = existing_link
            http_status = status.HTTP_200_OK

        refreshed = therapist_patient_base_queryset(therapist).filter(pk=link.pk).first()
        return Response(
            TherapistPatientRowSerializer(refreshed).data,
            status=http_status,
        )

    @staticmethod
    def _link_atomic(*, therapist, assoc, full_name, diag, cstat):
        """
        Toda la lógica de resolver/crear paciente y vínculo dentro de un
        bloque ``transaction.atomic`` con ``select_for_update`` sobre el
        paciente para cerrar la carrera de chequeo-y-creación entre
        terapeutas.

        Devuelve ``(link, http_status)``.
        Lanza ``_PatientConflictError`` si el paciente ya está vinculado
        activo a otro terapeuta.
        """
        with transaction.atomic():
            patient = None
            if assoc:
                patient = (
                    Patient.objects
                    .select_for_update()
                    .filter(external_id=assoc)
                    .first()
                )

            if patient is None:
                patient = Patient.objects.create(
                    external_id=assoc,
                    full_name=full_name,
                )
            else:
                # Ya tenemos el lock; verificar conflicto con otro terapeuta
                # DESPUÉS del select_for_update evita el TOCTOU clásico.
                conflict = (
                    TherapistPatient.objects
                    .filter(patient=patient, deleted_at__isnull=True)
                    .exclude(therapist=therapist)
                    .exists()
                )
                if conflict:
                    raise _PatientConflictError()
                if patient.full_name != full_name:
                    patient.full_name = full_name
                    patient.save(update_fields=['full_name'])

            active_self = TherapistPatient.objects.filter(
                therapist=therapist,
                patient=patient,
                deleted_at__isnull=True,
            ).first()
            if active_self:
                active_self.primary_diagnosis = diag
                active_self.clinical_status = cstat
                active_self.save(
                    update_fields=('primary_diagnosis', 'clinical_status'),
                )
                return active_self, status.HTTP_200_OK

            soft = (
                TherapistPatient.objects.filter(
                    therapist=therapist,
                    patient=patient,
                    deleted_at__isnull=False,
                )
                .order_by('-id')
                .first()
            )
            if soft:
                soft.deleted_at = None
                soft.primary_diagnosis = diag
                soft.clinical_status = cstat
                soft.save(
                    update_fields=(
                        'deleted_at',
                        'primary_diagnosis',
                        'clinical_status',
                    ),
                )
                return soft, status.HTTP_200_OK

            link = TherapistPatient.objects.create(
                therapist=therapist,
                patient=patient,
                primary_diagnosis=diag,
                clinical_status=cstat,
            )
            return link, status.HTTP_201_CREATED


class _PatientConflictError(Exception):
    """Señaliza conflicto de vínculo activo con otro terapeuta."""


class TherapistPatientPatchAPIView(APIView):
    """``PATCH /api/v1/therapist-patients/<link_id>/``."""

    permission_classes = (IsAuthenticated,)

    def patch(self, request, link_id, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        link = TherapistPatient.objects.filter(
            id=link_id,
            therapist=therapist,
        ).first()
        if link is None:
            raise Http404

        ser = TherapistPatientPatchSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data
        if 'primaryDiagnosis' in vd:
            link.primary_diagnosis = vd['primaryDiagnosis']
        if 'clinicalStatus' in vd:
            link.clinical_status = vd['clinicalStatus']
        if vd:
            link.save()

        refreshed = therapist_patient_base_queryset(therapist).filter(pk=link.pk).first()
        return Response(TherapistPatientRowSerializer(refreshed).data)


class TherapistPatientUnlinkAPIView(APIView):
    """``POST /api/v1/therapist-patients/<link_id>/unlink/`` — soft delete."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, link_id, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        link = TherapistPatient.objects.filter(
            id=link_id,
            therapist=therapist,
        ).first()
        if link is None:
            raise Http404
        if link.deleted_at is not None:
            return Response(
                {'detail': 'El vínculo ya está desvinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link.deleted_at = timezone.now()
        link.save(update_fields=('deleted_at',))
        refreshed = therapist_patient_base_queryset(therapist).filter(pk=link.pk).first()
        return Response(TherapistPatientRowSerializer(refreshed).data)


class TherapistPatientRestoreAPIView(APIView):
    """``POST /api/v1/therapist-patients/<link_id>/restore/``."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, link_id, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        link = TherapistPatient.objects.filter(
            id=link_id,
            therapist=therapist,
        ).first()
        if link is None:
            raise Http404
        if link.deleted_at is None:
            return Response(
                {'detail': 'El vínculo ya está activo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link.deleted_at = None
        link.save(update_fields=('deleted_at',))
        refreshed = therapist_patient_base_queryset(therapist).filter(pk=link.pk).first()
        return Response(TherapistPatientRowSerializer(refreshed).data)
