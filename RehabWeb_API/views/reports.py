"""Vistas API — Exportación de informes clínicos (HU-02)."""

import logging
from io import BytesIO

from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from RehabWeb_API.serializers import ClinicalExportRequestSerializer
from RehabWeb_API.services.clinical_export import render_clinical_export
from RehabWeb_API.services.therapist_access import (
    get_active_therapist_patient_link,
    get_therapist_for_user,
)

logger = logging.getLogger(__name__)


class ReportExportAPIView(APIView):
    """
    POST /api/v1/reports/export/

    Cuerpo JSON (camelCase): ``patientId``, ``dateFrom``, ``dateTo``, ``format`` (``pdf`` | ``xlsx``).

    Respuesta: archivo binario con cabeceras ``Content-Type`` y ``Content-Disposition``.
    Autenticación: token DRF ``Authorization: Token <clave>``.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ClinicalExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        therapist = get_therapist_for_user(request.user)
        if therapist is None:
            raise PermissionDenied('Se requiere perfil de terapeuta para exportar informes.')

        link = get_active_therapist_patient_link(therapist, data['patientId'])
        if link is None:
            raise PermissionDenied('No tienes permiso para exportar datos de este paciente.')

        try:
            content, filename, mime = render_clinical_export(
                therapist,
                link,
                data['dateFrom'],
                data['dateTo'],
                data['format'],
            )
        except Exception:
            logger.exception('Fallo al generar informe clínico')
            return Response(
                {'detail': 'No se pudo generar el archivo. Revisa los datos o inténtalo más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        buffer = BytesIO(content)
        buffer.seek(0)
        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type=mime,
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
