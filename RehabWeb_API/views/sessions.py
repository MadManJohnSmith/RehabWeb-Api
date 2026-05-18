"""Vistas API — Historial de sesiones (HU-05)."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from RehabWeb_API.filters import SessionFilter
from RehabWeb_API.models import Session, TherapistPatient
from RehabWeb_API.pagination import APIPageNumberPagination
from RehabWeb_API.serializers import SessionDetailSerializer, SessionListSerializer
from RehabWeb_API.services.therapist_access import get_therapist_for_user


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ``GET /api/v1/sessions/`` — lista paginada, orden por defecto ``-occurred_at``.

    ``GET /api/v1/sessions/<id>/`` — detalle con notas y ejercicios.

    Filtros: ``patientId``, ``search`` (programa o notas, ``icontains``).
    """

    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SessionFilter
    ordering_fields = ('occurred_at', 'id')
    ordering = ('-occurred_at',)
    pagination_class = APIPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SessionDetailSerializer
        return SessionListSerializer

    def _get_therapist(self):
        """Resuelve el Therapist UNA vez por request y lo cachea en self."""
        cached = getattr(self, '_therapist_cache', None)
        if cached is not None or hasattr(self, '_therapist_cache'):
            return cached
        self._therapist_cache = get_therapist_for_user(self.request.user)
        return self._therapist_cache

    def _require_therapist(self):
        therapist = self._get_therapist()
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')
        return therapist

    def get_queryset(self):
        therapist = self._get_therapist()
        if therapist is None:
            return Session.objects.none()
        patient_ids = TherapistPatient.objects.filter(
            therapist=therapist,
            deleted_at__isnull=True,
        ).values_list('patient_id', flat=True)
        qs = Session.objects.filter(
            therapist=therapist,
            patient_id__in=patient_ids,
        ).select_related('patient')
        if self.action == 'retrieve':
            qs = qs.prefetch_related('exercises')
        return qs

    def list(self, request, *args, **kwargs):
        self._require_therapist()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self._require_therapist()
        return super().retrieve(request, *args, **kwargs)
