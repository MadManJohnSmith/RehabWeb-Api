"""Filtros django-filter para la API."""

import django_filters
from django.db.models import CharField, Q
from django.db.models.functions import Cast, TruncDate

from RehabWeb_API.models import Session, TherapistPatient


class SessionFilter(django_filters.FilterSet):
    """Query params alineados con el front (camelCase)."""

    patientId = django_filters.NumberFilter(field_name='patient_id')
    sessionId = django_filters.NumberFilter(field_name='id')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Session
        fields = ('patientId', 'sessionId')

    def filter_search(self, queryset, name, value):
        if not value or not value.strip():
            return queryset
        term = value.strip()
        exact_id_match = Q()
        if term.isdigit():
            exact_id_match = Q(id=int(term))
        # additionally allow matching by numeric patient PK or by patient's external id
        patient_id_match = Q()
        if term.isdigit():
            patient_id_match = Q(patient_id=int(term))

        return queryset.annotate(
            occurred_date_text=Cast(TruncDate('occurred_at'), CharField()),
        ).filter(
            exact_id_match
            | patient_id_match
            | Q(patient__full_name__icontains=term)
            | Q(patient__external_id__icontains=term)
            | Q(program_label__icontains=term)
            | Q(occurred_date_text__icontains=term)
            | Q(notes__icontains=term)
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
        if value is True:
            return queryset
        return queryset.filter(deleted_at__isnull=True)

    def filter_q(self, queryset, name, value):
        if not value or not value.strip():
            return queryset
        term = value.strip()
        return queryset.filter(
            Q(patient__full_name__icontains=term)
            | Q(patient__external_id__icontains=term)
            | Q(primary_diagnosis__icontains=term)
        )
