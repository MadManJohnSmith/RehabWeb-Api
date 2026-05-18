"""Vistas API — Exportación de informes clínicos (HU-02)."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
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
    throttle_scope = 'reports_export'

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
        except ObjectDoesNotExist:
            return Response(
                {'detail': 'Paciente no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except MemoryError:
            logger.exception(
                'clinical_export OOM user=%s patient=%s',
                getattr(request.user, 'pk', None),
                data['patientId'],
            )
            return Response(
                {'detail': 'El informe excede la capacidad de procesamiento.'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        except Exception:  # noqa: BLE001 — barrera de último recurso con log
            logger.exception('Fallo al generar informe clínico')
            return Response(
                {'detail': 'No se pudo generar el archivo. Revisa los datos o inténtalo más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(content, content_type=mime)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = str(len(content))
        return response
