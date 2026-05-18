"""Vistas API — Comparativa de desempeño (HU-04)."""

from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.serializers import PerformanceCompareRequestSerializer
from RehabWeb_API.services.performance_series import (
    compute_group_bounds,
    resolve_patient_for_therapist,
    resolve_patients_batch,
)
from RehabWeb_API.services.therapist_access import get_therapist_for_user


class PatientPerformanceSeriesAPIView(APIView):
    """
    GET /api/v1/patients/<patient_id>/performance-series/

    Serie temporal (meta vs observado) para un paciente vinculado al terapeuta.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, patient_id: int, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')

        status, payload = resolve_patient_for_therapist(therapist, patient_id)
        if status == 'not_found':
            raise Http404('Paciente no encontrado.')
        if status == 'forbidden':
            raise PermissionDenied('No tienes acceso a los datos de este paciente.')
        return Response(payload)


class PerformanceCompareAPIView(APIView):
    """
    POST /api/v1/performance/compare/

    Cuerpo: ``{ "patientIds": [1, 2, 3] }`` (PKs de paciente).
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')

        serializer = PerformanceCompareRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['patientIds']

        # Resolución batch: 3 queries totales en lugar de ~3×N.
        status_by_id, payload_by_id = resolve_patients_batch(therapist, ids)

        for pid in ids:
            st = status_by_id.get(pid)
            if st == 'not_found':
                return Response(
                    {'detail': f'El paciente {pid} no existe.'},
                    status=400,
                )
            if st == 'forbidden':
                return Response(
                    {'detail': f'No tienes acceso al paciente {pid}.'},
                    status=403,
                )

        patients_payload = [payload_by_id[pid] for pid in ids]
        group_bounds = compute_group_bounds(patients_payload)
        return Response(
            {
                'patients': patients_payload,
                'groupBounds': group_bounds,
            }
        )
