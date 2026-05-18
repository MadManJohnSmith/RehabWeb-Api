"""
Serializers for RehabWeb_API.

Define your serializers here.
"""

from rest_framework import serializers

from RehabWeb_API.models import Session, SessionExercise, TherapistPatient
from RehabWeb_API.services.clinical_export import MAX_EXPORT_RANGE_DAYS
from RehabWeb_API.services.performance_series import MAX_COMPARE_PATIENTS


class ClinicalExportRequestSerializer(serializers.Serializer):
    """
    Cuerpo esperado del front (camelCase), alineado con `ClinicalExportFiltersDto`.

    POST /api/v1/reports/export/
    """

    patientId = serializers.IntegerField(min_value=1)
    dateFrom = serializers.DateField()
    dateTo = serializers.DateField()
    format = serializers.ChoiceField(choices=('pdf', 'xlsx'))

    def validate(self, attrs):
        start = attrs['dateFrom']
        end = attrs['dateTo']
        if start > end:
            raise serializers.ValidationError(
                {'dateTo': ['La fecha hasta no puede ser anterior a la fecha desde.']}
            )
        if (end - start).days > MAX_EXPORT_RANGE_DAYS:
            raise serializers.ValidationError(
                {
                    'dateTo': [
                        f'El rango no puede superar {MAX_EXPORT_RANGE_DAYS} días.',
                    ],
                }
            )
        return attrs


class PerformanceCompareRequestSerializer(serializers.Serializer):
    """
    POST /api/v1/performance/compare/

    Lista de IDs enteros (PK de ``Patient``), sin duplicados, máximo
    ``MAX_COMPARE_PATIENTS``.
    """

    patientIds = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
    )

    def validate_patientIds(self, value: list[int]) -> list[int]:
        if len(value) > MAX_COMPARE_PATIENTS:
            raise serializers.ValidationError(
                f'Se permiten como máximo {MAX_COMPARE_PATIENTS} pacientes por solicitud.'
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError('No se permiten IDs de paciente duplicados.')
        return value


class SessionExerciseSerializer(serializers.ModelSerializer):
    sortOrder = serializers.IntegerField(source='sort_order', read_only=True)

    class Meta:
        model = SessionExercise
        fields = ('id', 'name', 'sets', 'reps', 'notes', 'sortOrder')


class SessionListSerializer(serializers.ModelSerializer):
    patientId = serializers.IntegerField(source='patient_id', read_only=True)
    patientName = serializers.CharField(source='patient.full_name', read_only=True)
    occurredAt = serializers.DateTimeField(source='occurred_at', read_only=True)
    programLabel = serializers.CharField(source='program_label', read_only=True)
    durationMin = serializers.IntegerField(
        source='duration_min',
        read_only=True,
        allow_null=True,
    )
    adherencePercent = serializers.IntegerField(
        source='adherence_percent',
        read_only=True,
        allow_null=True,
    )
    score = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = (
            'id',
            'patientId',
            'patientName',
            'occurredAt',
            'programLabel',
            'durationMin',
            'score',
            'status',
            'adherencePercent',
        )

    def get_score(self, obj):
        return float(obj.score) if obj.score is not None else None


class SessionDetailSerializer(SessionListSerializer):
    notes = serializers.CharField(read_only=True)
    exercises = SessionExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = SessionListSerializer.Meta.fields + ('notes', 'exercises')


class TherapistPatientRowSerializer(serializers.ModelSerializer):
    """Fila de paciente vinculado (lista, detalle, respuesta de link) — HU-06."""

    patientId = serializers.IntegerField(source='patient_id', read_only=True)
    linkId = serializers.IntegerField(source='id', read_only=True)
    associationId = serializers.CharField(source='patient.external_id', read_only=True)
    fullName = serializers.CharField(source='patient.full_name', read_only=True)
    # source explícito: el campo modelo es `primary_diagnosis`; sin él DRF
    # busca instance.primaryDiagnosis (no existe) y omite la clave del JSON.
    primaryDiagnosis = serializers.CharField(
        source='primary_diagnosis', read_only=True, allow_blank=True,
    )
    clinicalStatus = serializers.CharField(source='clinical_status', read_only=True)
    lastSessionAt = serializers.DateTimeField(
        source='last_session_at',
        read_only=True,
        allow_null=True,
    )
    deletedAt = serializers.DateTimeField(source='deleted_at', read_only=True, allow_null=True)
    isUnlinked = serializers.SerializerMethodField()

    class Meta:
        model = TherapistPatient
        fields = (
            'patientId',
            'linkId',
            'associationId',
            'fullName',
            'primaryDiagnosis',
            'clinicalStatus',
            'lastSessionAt',
            'deletedAt',
            'isUnlinked',
        )

    def get_isUnlinked(self, obj):
        return obj.deleted_at is not None


class PatientLinkRequestSerializer(serializers.Serializer):
    """POST /api/v1/patients/link/ — HU-06."""

    associationId = serializers.CharField(max_length=64, required=False, allow_blank=True)
    fullName = serializers.CharField(max_length=200)
    primaryDiagnosis = serializers.CharField(max_length=500, required=False, allow_blank=True)
    clinicalStatus = serializers.ChoiceField(
        choices=('riesgo', 'activo', 'alta'),
        required=False,
        default='activo',
    )


class TherapistPatientPatchSerializer(serializers.Serializer):
    """PATCH /api/v1/therapist-patients/{linkId}/ — HU-06."""

    primaryDiagnosis = serializers.CharField(max_length=500, required=False, allow_blank=True)
    clinicalStatus = serializers.ChoiceField(
        choices=('riesgo', 'activo', 'alta'),
        required=False,
    )
