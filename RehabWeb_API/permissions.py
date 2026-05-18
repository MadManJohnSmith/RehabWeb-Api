"""
Custom permissions for RehabWeb_API.

Las vistas que necesiten validación a nivel de rol terapeuta pueden
declarar ``permission_classes = [IsAuthenticated, IsTherapist]`` en lugar
de duplicar el chequeo dentro del handler. La autorización fina sobre
el paciente sigue resolviéndose en ``services.therapist_access``.
"""

from rest_framework import permissions


class IsTherapist(permissions.BasePermission):
    """Permite la operación sólo si el usuario tiene perfil Therapist 1:1.

    Evita que el view tenga que llamar manualmente a
    ``get_therapist_for_user`` y devolver 403 ad-hoc, manteniendo la
    convención DRF de respuestas de permiso uniformes.
    """

    message = 'Se requiere rol de terapeuta.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return hasattr(user, 'therapist_profile')
