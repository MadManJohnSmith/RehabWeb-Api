"""
Modelos de dominio RehabWeb / PhysioMetrics (Módulo 5).

HU-01 consume Session, MetricPoint y vínculos TherapistPatient; el resto de HUs
ampliará el uso de estos mismos modelos.
"""

from django.conf import settings
from django.db import models


class Therapist(models.Model):
    """Perfil 1:1 del profesional autenticado (HU-06 / plan equipo)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_profile',
    )

    class Meta:
        verbose_name = 'Terapeuta'
        verbose_name_plural = 'Terapeutas'

    def __str__(self) -> str:
        return f'Terapeuta({self.user.get_username()})'


class Patient(models.Model):
    """Persona atendida."""

    external_id = models.CharField(
        'Identificador externo',
        max_length=64,
        blank=True,
        db_index=True,
    )
    full_name = models.CharField('Nombre completo', max_length=200)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self) -> str:
        return self.full_name


class ClinicalStatus(models.TextChoices):
    RIESGO = 'riesgo', 'Riesgo'
    ACTIVO = 'activo', 'Activo'
    ALTA = 'alta', 'Alta'


class TherapistPatient(models.Model):
    """Relación terapeuta ↔ paciente (HU-06); `deleted_at` = soft delete."""

    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name='patient_links',
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='therapist_links',
    )
    primary_diagnosis = models.CharField(
        'Diagnóstico principal',
        max_length=500,
        blank=True,
    )
    clinical_status = models.CharField(
        max_length=20,
        choices=ClinicalStatus,
        default=ClinicalStatus.ACTIVO,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Vínculo terapeuta-paciente'
        verbose_name_plural = 'Vínculos terapeuta-paciente'
        constraints = [
            models.UniqueConstraint(
                fields=('therapist', 'patient'),
                condition=models.Q(deleted_at__isnull=True),
                name='uniq_active_therapist_patient',
            ),
        ]
        indexes = [
            models.Index(fields=('therapist', 'deleted_at')),
            models.Index(fields=('therapist', 'clinical_status')),
        ]

    def __str__(self) -> str:
        return f'{self.therapist} → {self.patient}'


class Session(models.Model):
    """Sesión de rehabilitación (HU-03, HU-05, dashboard HU-01)."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    occurred_at = models.DateTimeField('Fecha y hora')
    program_label = models.CharField(max_length=200, blank=True)
    duration_min = models.PositiveSmallIntegerField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    adherence_percent = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'
        ordering = ('-occurred_at',)
        indexes = [
            models.Index(fields=('patient', 'occurred_at')),
            models.Index(fields=('therapist', 'occurred_at')),
        ]

    def __str__(self) -> str:
        return f'Sesión {self.patient_id} @ {self.occurred_at:%Y-%m-%d}'


class SessionExercise(models.Model):
    """Ejercicios realizados en una sesión (detalle HU-05)."""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='exercises',
    )
    name = models.CharField('Nombre', max_length=200)
    sets = models.PositiveSmallIntegerField(null=True, blank=True)
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Ejercicio de sesión'
        verbose_name_plural = 'Ejercicios de sesión'
        ordering = ('sort_order', 'id')

    def __str__(self) -> str:
        return f'{self.name} (sesión {self.session_id})'


class InactivityAlert(models.Model):
    """
    Snapshot materializado por el job diario (HU-03).

    La API puede servir datos en vivo; esta tabla respalda auditoría y el criterio
    de “última ejecución del comando”.
    """

    class Severity(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'
        NO_SESSIONS = 'no_sessions', 'Sin sesiones registradas'

    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name='inactivity_alerts',
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='inactivity_alerts',
    )
    days_since_last_session = models.PositiveIntegerField(
        'Días desde última sesión',
        null=True,
        blank=True,
    )
    last_session_at = models.DateTimeField(null=True, blank=True)
    severity = models.CharField(
        max_length=32,
        choices=Severity,
        default=Severity.LOW,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alerta de inactividad'
        verbose_name_plural = 'Alertas de inactividad'
        constraints = [
            models.UniqueConstraint(
                fields=('therapist', 'patient'),
                name='uniq_inactivity_therapist_patient',
            ),
        ]
        indexes = [
            models.Index(fields=('therapist', 'updated_at')),
        ]

    def __str__(self) -> str:
        return f'Inactividad {self.patient_id} (terapeuta {self.therapist_id})'


class MetricPoint(models.Model):
    """Punto para ROM semanal o serie temporal meta vs observado (HU-01, HU-04)."""

    class MetricType(models.TextChoices):
        ROM_WEEK = 'rom_week', 'ROM semanal'
        TEMPORAL = 'temporal', 'Serie temporal'

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='metric_points',
    )
    metric_type = models.CharField(max_length=32, choices=MetricType)
    period_label = models.CharField(max_length=64)
    sort_order = models.PositiveIntegerField(default=0)
    meta_value = models.DecimalField(max_digits=10, decimal_places=3)
    observed_value = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        verbose_name = 'Punto de métrica'
        verbose_name_plural = 'Puntos de métrica'
        ordering = ('metric_type', 'sort_order', 'period_label')
        indexes = [
            models.Index(fields=('patient', 'metric_type', 'sort_order')),
        ]

    def __str__(self) -> str:
        return f'{self.metric_type} {self.period_label} (paciente {self.patient_id})'
