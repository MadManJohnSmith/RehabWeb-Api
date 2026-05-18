"""Filtros django-filter para la API.

Incluye filtros explícitos por `sessionId` y `patientId`, y un filtro
`search` que busca en nombre de paciente, `external_id`, programa, fecha
y notas. Esto permite que la UI use tanto parámetros específicos como la
barra de búsqueda genérica.
"""

import django_filters
from django.db.models import CharField, Q
from django.db.models.functions import Cast, TruncDate

from RehabWeb_API.models import Session, TherapistPatient


class SessionFilter(django_filters.FilterSet):
    """Query params alineados con el front (camelCase)."""

    # filtros explícitos (números)
    sessionId = django_filters.NumberFilter(field_name='id')
    patientId = django_filters.NumberFilter(field_name='patient_id')

    # búsqueda libre que cubre nombre, external id, programa, fecha y notas
    search = django_filters.CharFilter(method='filter_search')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    date_from = django_filters.DateFilter(field_name='occurred_at', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='occurred_at', lookup_expr='date__lte')

    class Meta:
        model = Session
        fields = ('patientId', 'sessionId', 'status', 'date_from', 'date_to')

    def filter_search(self, queryset, name, value):
        if not value or not value.strip():
            return queryset
        term = value.strip()

        # coincidencia exacta por id numérico cuando el término es dígito
        exact_id_match = Q()
        if term.isdigit():
            exact_id_match = Q(id=int(term))

        # coincidencia por patient PK cuando el término es dígito
        patient_id_match = Q()
        if term.isdigit():
            patient_id_match = Q(patient_id=int(term))

        # truncamos la fecha a día para permitir búsquedas por fecha YYYY-MM-DD
        return (
            queryset.annotate(
                occurred_date_text=Cast(TruncDate('occurred_at'), CharField()),
            )
            .filter(
                exact_id_match
                | patient_id_match
                | Q(patient__full_name__icontains=term)
                | Q(patient__external_id__icontains=term)
                | Q(program_label__icontains=term)
                | Q(occurred_date_text__icontains=term)
                | Q(notes__icontains=term)
            )
        )


class TherapistPatientListFilter(django_filters.FilterSet):
    """Filtros para lista de pacientes del terapeuta (HU-06)."""

    clinicalStatus = django_filters.CharFilter(field_name='clinical_status')
    includeDeleted = django_filters.BooleanFilter(method='filter_include_deleted')
    q = django_filters.CharFilter(method='filter_q')

    class Meta:
        model = TherapistPatient
        fields = ('clinicalStatus',)

    def filter_include_deleted(self, queryset, name, value):
        # No-op: la inclusión/exclusión real se decide en la vista para que
        # aplique también cuando el parámetro NO está presente (default =
        # ocultar borrados). Aquí lo dejamos declarado para que django-filter
        # siga exponiéndolo en el schema/OpenAPI.
        return queryset

    def filter_q(self, queryset, name, value):
        if not value or not value.strip():
            return queryset
        term = value.strip()
        return queryset.filter(
            Q(patient__full_name__icontains=term)
            | Q(patient__external_id__icontains=term)
            | Q(primary_diagnosis__icontains=term)
        )
