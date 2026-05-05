"""Salud del servicio y conexión a base de datos (HU-07)."""

from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthAPIView(APIView):
    """
    GET /api/v1/health/

    Comprueba que la aplicación responde y que la base de datos acepta consultas.
    Sin autenticación (útil para balanceadores y arranque local).
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            return Response(
                {'status': 'error', 'database': 'unavailable'},
                status=503,
            )
        return Response({'status': 'ok'})
