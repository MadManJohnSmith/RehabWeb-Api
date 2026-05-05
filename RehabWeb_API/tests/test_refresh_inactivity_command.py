"""Comando refresh_inactivity_alerts (HU-03)."""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class RefreshInactivityCommandTests(SimpleTestCase):
    @patch(
        'RehabWeb_API.management.commands.refresh_inactivity_alerts.sync_all_inactivity_alerts',
        return_value=(3, 7),
    )
    def test_command_calls_sync(self, _mock_sync):
        out = StringIO()
        call_command('refresh_inactivity_alerts', stdout=out)
        self.assertIn('3', out.getvalue())
        self.assertIn('7', out.getvalue())
