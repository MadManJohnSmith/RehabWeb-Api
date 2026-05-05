"""Vistas API — Dashboard (HU-01)."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.services.dashboard_metrics import build_dashboard_payload


class MeDashboardAPIView(APIView):
    """
    GET /api/v1/me/dashboard/

    Devuelve métricas agregadas para el terapeuta autenticado (token DRF o sesión).
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        payload = build_dashboard_payload(request.user)
        return Response(payload)
