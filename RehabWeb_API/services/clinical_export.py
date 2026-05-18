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
import re
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape as xml_escape

from django.utils import timezone

from RehabWeb_API.models import Session, TherapistPatient

if TYPE_CHECKING:
    from RehabWeb_API.models import Therapist

logger = logging.getLogger(__name__)

# Anti-abuso: rango máximo de fechas por exportación (AC-02 / plan HU-02).
MAX_EXPORT_RANGE_DAYS = 366

# Cap defensivo contra OOM cuando un paciente tiene historial extremadamente
# largo. Si el corte aplica, el resto debe pedirse en un rango más estrecho.
MAX_SESSIONS_PER_REPORT = 1000

# Whitelist para sanitizar nombres de archivo y evitar HTTP response splitting
# en el header Content-Disposition.
_FILENAME_SAFE_RE = re.compile(r'[^A-Za-z0-9._-]+')


def _esc(value) -> str:
    """Escapa entidades XML/HTML antes de pasar texto a ReportLab Paragraph.

    Sin esto, un diagnosis con `<b>` o `&` corrompería el PDF o abriría
    superficie de inyección de marcado controlada por el usuario.
    """
    if value is None:
        return ''
    return xml_escape(str(value))


def _safe_filename(base: str, extension: str) -> str:
    """Filtra caracteres no seguros para Content-Disposition."""
    cleaned = _FILENAME_SAFE_RE.sub('_', base)
    return f'{cleaned}.{extension}'


def _local_naive(value):
    """Convierte un datetime aware a la TZ local y le quita el tzinfo.

    Excel no maneja tzinfo; sin conversión previa, las celdas formateadas
    como local mostrarían la hora UTC.
    """
    if value is None:
        return ''
    if not isinstance(value, dt.datetime):
        return value
    if timezone.is_aware(value):
        return timezone.localtime(value).replace(tzinfo=None)
    return value.replace(tzinfo=None)


def _day_start_end(
    date_from: dt.date,
    date_to: dt.date,
) -> tuple[dt.datetime, dt.datetime]:
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(dt.datetime.combine(date_from, dt.time.min), tz)
    end = timezone.make_aware(dt.datetime.combine(date_to, dt.time.max), tz)
    return start, end


def fetch_sessions_for_report(
    therapist: Therapist,
    patient_id: int,
    date_from: dt.date,
    date_to: dt.date,
) -> tuple[list[Session], bool]:
    """
    Devuelve ``(sesiones, truncated)``. ``truncated`` indica que el rango
    superó ``MAX_SESSIONS_PER_REPORT`` y se aplicó un corte defensivo.

    Se piden ``MAX+1`` filas para detectar el truncamiento sin un COUNT(*)
    extra. ``prefetch_related('exercises')`` evita N+1 cuando el PDF
    enumera ejercicios por sesión.
    """
    start, end = _day_start_end(date_from, date_to)
    qs = (
        Session.objects.filter(
            therapist=therapist,
            patient_id=patient_id,
            occurred_at__gte=start,
            occurred_at__lte=end,
        )
        .select_related('patient')
        .prefetch_related('exercises')
        .order_by('occurred_at')
    )
    rows = list(qs[: MAX_SESSIONS_PER_REPORT + 1])
    truncated = len(rows) > MAX_SESSIONS_PER_REPORT
    if truncated:
        rows = rows[:MAX_SESSIONS_PER_REPORT]
    return rows, truncated


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
    truncated: bool = False,
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
    if truncated:
        ws.append(['Resultado truncado', f'Sí (máx. {MAX_SESSIONS_PER_REPORT} sesiones)'])
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
                _local_naive(s.occurred_at),
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
    truncated: bool = False,
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
    story.append(Paragraph(f'<b>Terapeuta:</b> {_esc(therapist_username)}', styles['Normal']))
    story.append(Paragraph(f'<b>Paciente:</b> {_esc(patient_name)}', styles['Normal']))
    story.append(
        Paragraph(
            f'<b>Diagnóstico (vínculo):</b> {_esc(diagnosis) or "—"}',
            styles['Normal'],
        )
    )
    story.append(
        Paragraph(
            f'<b>Periodo:</b> {date_from.isoformat()} — {date_to.isoformat()}',
            styles['Normal'],
        )
    )
    if truncated:
        story.append(
            Paragraph(
                f'<i>Nota: el rango supera el máximo permitido; se muestran '
                f'las primeras {MAX_SESSIONS_PER_REPORT} sesiones.</i>',
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
    sessions, truncated = fetch_sessions_for_report(
        therapist, patient_id, date_from, date_to
    )
    patient_name = link.patient.full_name
    diagnosis = link.primary_diagnosis or ''

    base = (
        f'informe_clinico_p{int(patient_id)}_'
        f'{date_from.isoformat()}_{date_to.isoformat()}'
    )

    if file_format == 'xlsx':
        content = build_xlsx_bytes(
            sessions,
            patient_name=patient_name,
            date_from=date_from,
            date_to=date_to,
            diagnosis=diagnosis,
            truncated=truncated,
        )
        filename = _safe_filename(base, 'xlsx')
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        content = build_pdf_bytes(
            sessions,
            patient_name=patient_name,
            date_from=date_from,
            date_to=date_to,
            diagnosis=diagnosis,
            therapist_username=therapist.user.get_username(),
            truncated=truncated,
        )
        filename = _safe_filename(base, 'pdf')
        mime = 'application/pdf'

    logger.info(
        'clinical_export user=%s patient_id=%s format=%s sessions=%s truncated=%s',
        therapist.user_id,
        patient_id,
        file_format,
        len(sessions),
        truncated,
    )
    return content, filename, mime
