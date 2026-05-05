"""Rutas versionadas de la API REST (prefijo /api/v1/)."""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from RehabWeb_API.views.auth_api import LogoutAPIView
from RehabWeb_API.views.dashboard import MeDashboardAPIView
from RehabWeb_API.views.health import HealthAPIView
from RehabWeb_API.views.inactivity import InactivityAlertListAPIView
from RehabWeb_API.views.patient_management import (
    PatientFichaAPIView,
    PatientLinkAPIView,
    TherapistPatientListAPIView,
    TherapistPatientPatchAPIView,
    TherapistPatientRestoreAPIView,
    TherapistPatientUnlinkAPIView,
)
from RehabWeb_API.views.performance import (
    PatientPerformanceSeriesAPIView,
    PerformanceCompareAPIView,
)
from RehabWeb_API.views.reports import ReportExportAPIView
from RehabWeb_API.views.sessions import SessionViewSet

router = DefaultRouter()
router.register('sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('health/', HealthAPIView.as_view(), name='api-health'),
    path('auth/login/', obtain_auth_token, name='api-auth-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api-auth-logout'),
    path('me/dashboard/', MeDashboardAPIView.as_view(), name='me-dashboard'),
    path('reports/export/', ReportExportAPIView.as_view(), name='reports-export'),
    path(
        'inactivity-alerts/',
        InactivityAlertListAPIView.as_view(),
        name='inactivity-alerts',
    ),
    path('patients/link/', PatientLinkAPIView.as_view(), name='patient-link'),
    path(
        'patients/<int:patient_id>/performance-series/',
        PatientPerformanceSeriesAPIView.as_view(),
        name='patient-performance-series',
    ),
    path('patients/<int:pk>/', PatientFichaAPIView.as_view(), name='patient-detail'),
    path('patients/', TherapistPatientListAPIView.as_view(), name='patient-list'),
    path(
        'therapist-patients/<int:link_id>/unlink/',
        TherapistPatientUnlinkAPIView.as_view(),
        name='therapist-patient-unlink',
    ),
    path(
        'therapist-patients/<int:link_id>/restore/',
        TherapistPatientRestoreAPIView.as_view(),
        name='therapist-patient-restore',
    ),
    path(
        'therapist-patients/<int:link_id>/',
        TherapistPatientPatchAPIView.as_view(),
        name='therapist-patient-detail',
    ),
    path(
        'performance/compare/',
        PerformanceCompareAPIView.as_view(),
        name='performance-compare',
    ),
    path('', include(router.urls)),
]
