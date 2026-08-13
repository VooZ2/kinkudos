from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class ScheduledRemindersCommandTests(SimpleTestCase):
    def test_later_steps_run_when_lottery_step_fails(self):
        calls = []

        def boom():
            calls.append("lottery")
            raise RuntimeError("lottery failed")

        def nudge():
            calls.append("nudge")
            return ["nudge-1"]

        def presets():
            calls.append("presets")
            return ["preset-1"]

        with (
            patch(
                "economy.management.commands.run_scheduled_reminders.send_due_lottery_reminders",
                side_effect=boom,
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.send_due_assigned_task_nudges",
                side_effect=nudge,
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.run_due_assignment_presets",
                side_effect=presets,
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.FamilySettings"
            ) as family_settings,
        ):
            family_settings.load.return_value.timezone_name = "UTC"
            with self.assertRaises(SystemExit) as raised:
                call_command(
                    "run_scheduled_reminders",
                    stdout=StringIO(),
                    stderr=StringIO(),
                )

        self.assertEqual(calls, ["lottery", "nudge", "presets"])
        self.assertIn("lottery reminders", str(raised.exception))

    def test_legacy_alias_delegates_to_scheduled_reminders(self):
        with (
            patch(
                "economy.management.commands.run_scheduled_reminders.send_due_lottery_reminders",
                return_value=[],
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.send_due_assigned_task_nudges",
                return_value=[],
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.run_due_assignment_presets",
                return_value=[],
            ),
            patch(
                "economy.management.commands.run_scheduled_reminders.FamilySettings"
            ) as family_settings,
        ):
            family_settings.load.return_value.timezone_name = "UTC"
            call_command(
                "send_lottery_reminders",
                stdout=StringIO(),
                stderr=StringIO(),
            )
