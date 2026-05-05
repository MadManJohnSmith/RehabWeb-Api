"""
Views package for RehabWeb_API.

Define your API views here.
"""

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

__all__ = (
    'HealthAPIView',
    'LogoutAPIView',
    'MeDashboardAPIView',
    'InactivityAlertListAPIView',
    'PatientFichaAPIView',
    'PatientLinkAPIView',
    'TherapistPatientListAPIView',
    'TherapistPatientPatchAPIView',
    'TherapistPatientRestoreAPIView',
    'TherapistPatientUnlinkAPIView',
    'PatientPerformanceSeriesAPIView',
    'PerformanceCompareAPIView',
    'ReportExportAPIView',
    'SessionViewSet',
)

