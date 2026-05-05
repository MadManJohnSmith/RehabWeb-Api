"""Autenticación API complementaria al admin y browsable API (HU-07)."""

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutAPIView(APIView):
    """
    POST /api/v1/auth/logout/

    Elimina el token DRF del usuario autenticado. Tras esto, las peticiones con la
    clave anterior reciben 401 hasta un nuevo login.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
