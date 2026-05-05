"""
Admin configuration for RehabWeb_API.

Register your models here.
"""

from django.contrib import admin

from RehabWeb_API.models import (
    InactivityAlert,
    MetricPoint,
    Patient,
    Session,
    SessionExercise,
    Therapist,
    TherapistPatient,
)


@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__username',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'external_id')
    search_fields = ('full_name', 'external_id')


@admin.register(TherapistPatient)
class TherapistPatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'therapist', 'patient', 'clinical_status', 'deleted_at')
    list_filter = ('clinical_status',)


@admin.register(InactivityAlert)
class InactivityAlertAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'therapist',
        'patient',
        'days_since_last_session',
        'severity',
        'updated_at',
    )
    list_filter = ('severity', 'therapist')
    date_hierarchy = 'updated_at'


class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'therapist', 'patient', 'occurred_at', 'program_label')
    list_filter = ('therapist',)
    date_hierarchy = 'occurred_at'
    inlines = (SessionExerciseInline,)


@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'name', 'sets', 'reps', 'sort_order')
    list_filter = ('session__therapist',)


@admin.register(MetricPoint)
class MetricPointAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'metric_type', 'period_label', 'sort_order')
    list_filter = ('metric_type',)
