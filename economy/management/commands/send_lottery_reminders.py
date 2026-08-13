from economy.management.commands.run_scheduled_reminders import (
    Command as ScheduledRemindersCommand,
)


class Command(ScheduledRemindersCommand):
    """Legacy alias kept for existing cron and older unit files."""

    help = (
        ScheduledRemindersCommand.help
        + " Prefer manage.py run_scheduled_reminders."
    )
