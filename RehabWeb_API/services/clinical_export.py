"""
Generación de informes clínicos exportables (HU-02).

PDF con ReportLab y Excel con openpyxl (dependencias puramente Python,
adecuadas para entornos Windows sin GTK).

Los compañeros deben ejecutar migraciones y tener datos reales para
probar el flujo completo contra MySQL.
"""

from __future__ import annotations

import datetime as dt
import logging
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING

from django.utils import timezone

from RehabWeb_API.models import Session, TherapistPatient

if TYPE_CHECKING:
    from RehabWeb_API.models import Therapist

logger = logging.getLogger(__name__)

# Anti-abuso: rango máximo de fechas por exportación (AC-02 / plan HU-02).
MAX_EXPORT_RANGE_DAYS = 366


def _day_start_end(
    date_from: dt.date,
    date_to: dt.date,
) -> tuple[dt.datetime, dt.datetime]:
    start = timezone.make_aware(dt.datetime.combine(date_from, dt.time.min))
    end = timezone.make_aware(dt.datetime.combine(date_to, dt.time.max))
    return start, end


def fetch_sessions_for_report(
    therapist: Therapist,
    patient_id: int,
    date_from: dt.date,
    date_to: dt.date,
) -> list[Session]:
    start, end = _day_start_end(date_from, date_to)
    return list(
        Session.objects.filter(
            therapist=therapist,
            patient_id=patient_id,
            occurred_at__gte=start,
            occurred_at__lte=end,
        )
        .select_related('patient')
        .order_by('occurred_at')
    )


def _safe_cell(value) -> str:
    if value is None:
        return ''
    if isinstance(value, Decimal):
        return str(value)
    return str(value).replace('\r\n', ' ').replace('\n', ' ')


def build_xlsx_bytes(
    sessions: list[Session],
    *,
    patient_name: str,
    date_from: dt.date,
    date_to: dt.date,
    diagnosis: str,
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = 'Sesiones'
    ws.append(
        [
            'Paciente',
            patient_name,
        ]
    )
    ws.append(['Diagnóstico (vínculo)', diagnosis])
    ws.append(['Periodo', f'{date_from.isoformat()} — {date_to.isoformat()}'])
    ws.append([])
    ws.append(
        [
            'Fecha y hora',
            'Programa',
            'Duración (min)',
            'Score',
            'Adherencia %',
            'Estado',
            'Notas',
        ]
    )
    for s in sessions:
        ws.append(
            [
                s.occurred_at.isoformat(),
                s.program_label or '',
                s.duration_min if s.duration_min is not None else '',
                float(s.score) if s.score is not None else '',
                s.adherence_percent if s.adherence_percent is not None else '',
                s.status or '',
                _safe_cell(s.notes)[:2000],
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_pdf_bytes(
    sessions: list[Session],
    *,
    patient_name: str,
    date_from: dt.date,
    date_to: dt.date,
    diagnosis: str,
    therapist_username: str,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title='Informe clínico')
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('Informe clínico — RehabWeb', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'<b>Terapeuta:</b> {therapist_username}', styles['Normal']))
    story.append(Paragraph(f'<b>Paciente:</b> {patient_name}', styles['Normal']))
    story.append(Paragraph(f'<b>Diagnóstico (vínculo):</b> {diagnosis or "—"}', styles['Normal']))
    story.append(
        Paragraph(
            f'<b>Periodo:</b> {date_from.isoformat()} — {date_to.isoformat()}',
            styles['Normal'],
        )
    )
    story.append(Spacer(1, 18))

    table_data = [
        [
            'Fecha',
            'Programa',
            'Min',
            'Score',
            'Adh.%',
            'Notas (extracto)',
        ]
    ]
    for s in sessions:
        table_data.append(
            [
                s.occurred_at.strftime('%Y-%m-%d %H:%M'),
                (s.program_label or '')[:24],
                str(s.duration_min) if s.duration_min is not None else '',
                str(s.score) if s.score is not None else '',
                str(s.adherence_percent) if s.adherence_percent is not None else '',
                _safe_cell(s.notes)[:60],
            ]
        )
    if len(table_data) == 1:
        table_data.append(['(Sin sesiones en el periodo)', '', '', '', '', ''])

    tbl = Table(table_data, repeatRows=1, hAlign='LEFT')
    tbl.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
    return buffer.getvalue()


def render_clinical_export(
    therapist: Therapist,
    link: TherapistPatient,
    date_from: dt.date,
    date_to: dt.date,
    file_format: str,
) -> tuple[bytes, str, str]:
    """
    Devuelve ``(contenido_binario, nombre_archivo_sugerido, content_type)``.

    La vista debe comprobar antes que ``link`` pertenece a ``therapist`` y está activo.
    """
    patient_id = link.patient_id
    sessions = fetch_sessions_for_report(therapist, patient_id, date_from, date_to)
    patient_name = link.patient.full_name
    diagnosis = link.primary_diagnosis or ''

    slug_from = date_from.isoformat()
    slug_to = date_to.isoformat()
    base = f'informe_clinico_p{patient_id}_{slug_from}_{slug_to}'

    if file_format == 'xlsx':
        content = build_xlsx_bytes(
            sessions,
            patient_name=patient_name,
            date_from=date_from,
            date_to=date_to,
            diagnosis=diagnosis,
        )
        filename = f'{base}.xlsx'
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        content = build_pdf_bytes(
            sessions,
            patient_name=patient_name,
            date_from=date_from,
            date_to=date_to,
            diagnosis=diagnosis,
            therapist_username=therapist.user.get_username(),
        )
        filename = f'{base}.pdf'
        mime = 'application/pdf'

    logger.info(
        'clinical_export user=%s patient_id=%s format=%s sessions=%s',
        therapist.user_id,
        patient_id,
        file_format,
        len(sessions),
    )
    return content, filename, mime
