"""Vistas API — Alertas de inactividad (HU-03)."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.services.inactivity_rules import get_inactive_patients_for_therapist
from RehabWeb_API.services.therapist_access import get_therapist_for_user


class InactivityAlertListAPIView(APIView):
    """
    GET /api/v1/inactivity-alerts/

    Lista pacientes inactivos (**más de 3 días** sin sesión o sin sesiones)
    para el terapeuta autenticado. Datos **en vivo** (misma regla que el dashboard).

    Query opcional: ``?patientId=`` para filtrar una fila.

    Respuesta: ``{ "thresholdDays": 3, "inactiveCount": n, "alerts": [...] }``.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta.')

        alerts = get_inactive_patients_for_therapist(therapist)
        patient_id = request.query_params.get('patientId')
        if patient_id is not None:
            try:
                pid = int(patient_id)
            except ValueError:
                return Response(
                    {'detail': 'patientId debe ser un entero.'},
                    status=400,
                )
            alerts = [a for a in alerts if a['patientId'] == pid]

        return Response(
            {
                'thresholdDays': 3,
                'inactiveCount': len(alerts),
                'alerts': alerts,
            }
        )
