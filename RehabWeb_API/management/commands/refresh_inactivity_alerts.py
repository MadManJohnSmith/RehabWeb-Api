"""
Sincroniza la tabla ``InactivityAlert`` con la regla de negocio actual.

Programar diariamente (cron / Programador de tareas), por ejemplo 06:00:

    0 6 * * * cd /ruta/proyecto && .venv/bin/python manage.py refresh_inactivity_alerts
"""

from django.core.management.base import BaseCommand

from RehabWeb_API.services.inactivity_sync import sync_all_inactivity_alerts


class Command(BaseCommand):
    help = (
        'Recalcula alertas de inactividad (>3 días sin sesión) y actualiza InactivityAlert.'
    )

    def handle(self, *args, **options):
        n_therapists, total_inactive_slots = sync_all_inactivity_alerts()
        self.stdout.write(
            self.style.SUCCESS(
                f'Terapeutas procesados: {n_therapists}. '
                f'Suma de pacientes inactivos (por terapeuta): {total_inactive_slots}.'
            )
        )
