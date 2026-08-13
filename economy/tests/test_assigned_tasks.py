from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    AssignedTaskStatus,
    AssignmentPreset,
    AssignmentPresetCadence,
    AssignmentPresetWeekendMode,
    ChildProfile,
    DeviceToken,
    LedgerKind,
    PushSubscription,
    RequestStatus,
    Reward,
    Task,
    TaskClaim,
    TaskCompletion,
    Theme,
)
from economy.services import (
    apply_assignment_preset,
    approve_reward_request,
    approve_task_claim,
    assign_tasks,
    assigned_tasks_block_rewards,
    assignment_preset_matches_date,
    cancel_assigned_task,
    complete_assigned_task,
    run_due_assignment_presets,
    save_assignment_preset,
    send_due_assigned_task_nudges,
    submit_reward_request,
    unavailable_assignment_task_ids,
)


class AssignedTaskServiceTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Very-safe-pass-123!",
        )
        self.child = ChildProfile.objects.create(
            name="Child",
            min_balance=-100,
            theme_selected=True,
        )
        self.other_child = ChildProfile.objects.create(
            name="Other",
            min_balance=-100,
            theme_selected=True,
        )
        self.task = Task.objects.create(title="Tidy room", reward=20, icon="🧹")

    def create_batch(self, *, blocks_rewards=True):
        return assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            custom_title="Feed the cat",
            custom_points=7,
            blocks_rewards=blocks_rewards,
        )

    def test_assignment_snapshots_catalog_and_custom_tasks(self):
        batch = self.create_batch()
        items = list(batch.items.order_by("pk"))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title_snapshot, "Tidy room")
        self.assertEqual(items[0].reward_snapshot, 20)
        self.assertEqual(items[0].icon_snapshot, "🧹")
        self.assertEqual(items[0].note_snapshot, "")
        self.assertIsNone(items[1].task)
        self.assertEqual(items[1].title_snapshot, "Feed the cat")
        self.assertEqual(items[1].reward_snapshot, 7)
        self.task.reward = 99
        self.task.save(update_fields=["reward"])
        items[0].refresh_from_db()
        self.assertEqual(items[0].reward_snapshot, 20)

    def test_assignment_snapshots_optional_notes(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            custom_title="Feed the cat",
            custom_points=7,
            task_notes={self.task.pk: "Clothes next to the dryer, not inside."},
            custom_note="Use the blue bowl.",
        )
        catalog_item = batch.items.get(task=self.task)
        custom_item = batch.items.get(task__isnull=True)
        self.assertEqual(
            catalog_item.note_snapshot,
            "Clothes next to the dryer, not inside.",
        )
        self.assertEqual(custom_item.note_snapshot, "Use the blue bowl.")

    def test_assignment_schedules_three_hour_nudge(self):
        before = timezone.now()
        batch = self.create_batch()
        after = timezone.now()
        self.assertIsNotNone(batch.nudge_at)
        self.assertIsNone(batch.nudge_sent_at)
        self.assertGreaterEqual(batch.nudge_at, before + timedelta(hours=3))
        self.assertLessEqual(batch.nudge_at, after + timedelta(hours=3))

    @patch("economy.push.notify_assigned_tasks_nudge")
    def test_due_nudge_sends_once_while_pending(self, notify):
        batch = self.create_batch(blocks_rewards=False)
        device, _ = DeviceToken.issue(created_by=self.parent, label="phone")
        PushSubscription.objects.create(
            child=self.child,
            device=device,
            endpoint="https://push.example/nudge",
            p256dh="nudge-key",
            auth="nudge-auth",
        )
        batch.nudge_at = timezone.now() - timedelta(minutes=1)
        batch.save(update_fields=["nudge_at"])
        first = send_due_assigned_task_nudges()
        second = send_due_assigned_task_nudges()
        batch.refresh_from_db()
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        self.assertIsNotNone(batch.nudge_sent_at)
        notify.assert_called_once()

    @patch("economy.push.notify_assigned_tasks_nudge")
    def test_due_nudge_skips_when_no_pending_items(self, notify):
        batch = self.create_batch(blocks_rewards=False)
        complete_assigned_task(
            assigned_task=batch.items.get(task=self.task),
            child=self.child,
        )
        cancel_assigned_task(
            assigned_task=batch.items.get(task__isnull=True),
            actor=self.parent,
        )
        batch.nudge_at = timezone.now() - timedelta(minutes=1)
        batch.save(update_fields=["nudge_at"])
        sent = send_due_assigned_task_nudges()
        batch.refresh_from_db()
        self.assertEqual(sent, [])
        self.assertIsNotNone(batch.nudge_sent_at)
        notify.assert_not_called()

    def test_completion_awards_immediately_and_only_once(self):
        item = self.create_batch().items.get(task=self.task)
        entry = complete_assigned_task(assigned_task=item, child=self.child)
        self.child.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(self.child.balance, 20)
        self.assertEqual(entry.kind, LedgerKind.ASSIGNED_TASK)
        self.assertEqual(item.status, AssignedTaskStatus.COMPLETED)
        self.assertEqual(item.ledger_entry, entry)
        self.assertTrue(
            TaskCompletion.objects.filter(child=self.child, task=self.task).exists()
        )
        with self.assertRaises(ValidationError):
            complete_assigned_task(assigned_task=item, child=self.child)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 20)

    def test_expired_task_cannot_be_completed_and_stops_blocking(self):
        batch = self.create_batch()
        batch.assigned_on = timezone.localdate() - timedelta(days=1)
        batch.save(update_fields=["assigned_on"])
        item = batch.items.first()
        self.assertTrue(item.is_expired)
        self.assertFalse(assigned_tasks_block_rewards(self.child))
        with self.assertRaisesMessage(ValidationError, "expired"):
            complete_assigned_task(assigned_task=item, child=self.child)

    def test_blocked_reward_requests_resume_when_all_items_complete(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            blocks_rewards=True,
        )
        reward = Reward.objects.create(title="Movie", cost=1)
        with self.assertRaisesMessage(ValidationError, "assigned tasks"):
            submit_reward_request(child=self.child, reward=reward)
        complete_assigned_task(
            assigned_task=batch.items.get(),
            child=self.child,
        )
        request = submit_reward_request(child=self.child, reward=reward)
        self.assertEqual(request.status, RequestStatus.PENDING)

    def test_unblocked_assignment_does_not_block_reward_requests(self):
        self.create_batch(blocks_rewards=False)
        reward = Reward.objects.create(title="Movie", cost=1)
        request = submit_reward_request(child=self.child, reward=reward)
        self.assertEqual(request.status, RequestStatus.PENDING)

    def test_existing_reward_request_can_still_be_approved_while_blocked(self):
        reward = Reward.objects.create(title="Movie", cost=1)
        request = submit_reward_request(child=self.child, reward=reward)
        self.create_batch()
        entry = approve_reward_request(request=request, actor=self.parent)
        request.refresh_from_db()
        self.assertEqual(request.status, RequestStatus.APPROVED)
        self.assertEqual(entry.delta, -1)

    def test_pending_claim_active_assignment_and_completion_are_unavailable(self):
        TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.assertIn(self.task.pk, unavailable_assignment_task_ids(self.child))
        self.child.task_claims.all().delete()
        batch = self.create_batch(blocks_rewards=False)
        self.assertIn(self.task.pk, unavailable_assignment_task_ids(self.child))
        complete_assigned_task(
            assigned_task=batch.items.get(task=self.task),
            child=self.child,
        )
        self.assertIn(self.task.pk, unavailable_assignment_task_ids(self.child))

    def test_approved_claim_is_recorded_as_completed_today(self):
        claim = TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        approve_task_claim(claim=claim, actor=self.parent)
        self.assertIn(self.task.pk, unavailable_assignment_task_ids(self.child))

    def test_cancelled_catalog_task_can_be_assigned_again_same_day(self):
        batch = self.create_batch(blocks_rewards=False)
        cancel_assigned_task(
            assigned_task=batch.items.get(task=self.task),
            actor=self.parent,
        )
        self.assertNotIn(self.task.pk, unavailable_assignment_task_ids(self.child))

    def test_completed_catalog_task_is_available_again_next_day(self):
        batch = self.create_batch(blocks_rewards=False)
        complete_assigned_task(
            assigned_task=batch.items.get(task=self.task),
            child=self.child,
        )
        yesterday = timezone.localdate() - timedelta(days=1)
        batch.assigned_on = yesterday
        batch.save(update_fields=["assigned_on"])
        TaskCompletion.objects.filter(child=self.child, task=self.task).update(
            completed_on=yesterday
        )
        self.assertNotIn(self.task.pk, unavailable_assignment_task_ids(self.child))

    def test_task_completion_is_unique_per_child_task_and_day(self):
        today = timezone.localdate()
        TaskCompletion.objects.create(
            child=self.child,
            task=self.task,
            completed_on=today,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TaskCompletion.objects.create(
                    child=self.child,
                    task=self.task,
                    completed_on=today,
                )
        TaskCompletion.objects.create(
            child=self.child,
            task=self.task,
            completed_on=today - timedelta(days=1),
        )


class AssignedTaskViewTests(TestCase):
    def setUp(self):
        self.parent_password = "Very-safe-pass-123!"
        self.parent = get_user_model().objects.create_user(
            "parent",
            password=self.parent_password,
        )
        self.child = ChildProfile.objects.create(
            name="Child",
            min_balance=-100,
            theme_selected=True,
        )
        self.other_child = ChildProfile.objects.create(
            name="Other",
            min_balance=-100,
            theme_selected=True,
        )
        self.task = Task.objects.create(title="Tidy room", reward=20, icon="🧹")

    def login_child(self, child=None):
        session = self.client.session
        session["child_id"] = (child or self.child).pk
        session.save()

    @patch("economy.views.parent_actions.notify_assigned_tasks")
    def test_parent_assigns_multiple_and_custom_tasks_with_push(self, notify):
        second = Task.objects.create(title="Dishes", reward=10, icon="🍽️")
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_tasks", args=[self.child.pk]),
            {
                "task_ids": [self.task.pk, second.pk],
                "custom_title": "Feed the cat",
                "custom_points": 7,
                "blocks_rewards": "on",
            },
            follow=True,
        )
        self.assertContains(response, "Tasks were assigned")
        batch = self.child.assigned_task_batches.get()
        self.assertEqual(batch.items.count(), 3)
        self.assertTrue(batch.blocks_rewards)
        notify.assert_called_once_with(batch)

    @patch("economy.views.parent_actions.notify_assigned_tasks")
    def test_parent_assigns_tasks_with_notes(self, notify):
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_tasks", args=[self.child.pk]),
            {
                "task_ids": [self.task.pk],
                f"task_note_{self.task.pk}": "Clothes next to the dryer.",
                "custom_title": "Feed the cat",
                "custom_points": 7,
                "custom_note": "Use the blue bowl.",
            },
            follow=True,
        )
        self.assertContains(response, "Tasks were assigned")
        batch = self.child.assigned_task_batches.get()
        self.assertEqual(
            batch.items.get(task=self.task).note_snapshot,
            "Clothes next to the dryer.",
        )
        self.assertEqual(
            batch.items.get(task__isnull=True).note_snapshot,
            "Use the blue bowl.",
        )
        notify.assert_called_once_with(batch)

    def test_child_sees_assigned_note_under_title(self):
        assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            task_notes={self.task.pk: "Clothes next to the dryer, not inside."},
        )
        self.login_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "Tidy room")
        self.assertContains(response, "Clothes next to the dryer, not inside.")
        self.assertContains(response, "assigned-task-note", html=False)

    def test_child_sees_priority_list_and_completes_own_task(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        item = batch.items.get()
        self.login_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, 'id="paskirti-darbai"', html=False)
        self.assertContains(response, "Tidy room")
        self.assertNotContains(response, "assigned-task-note", html=False)
        response = self.client.post(
            reverse("child_complete_assigned_task", args=[item.pk]),
            follow=True,
        )
        self.assertContains(response, "received your points")
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 20)

    def test_child_cannot_complete_another_child_task(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        self.login_child(self.other_child)
        response = self.client.post(
            reverse(
                "child_complete_assigned_task",
                args=[batch.items.get().pk],
            )
        )
        self.assertEqual(response.status_code, 404)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 0)

    def test_all_seven_themes_have_assigned_task_copy(self):
        assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        self.login_child()
        for theme in Theme.values:
            self.child.theme = theme
            self.child.save(update_fields=["theme"])
            response = self.client.get(reverse("child_dashboard"))
            self.assertNotContains(response, ">assigned_title<", html=False)
            self.assertNotContains(response, ">assigned_complete<", html=False)

    def test_expired_tasks_disappear_from_child_dashboard(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        batch.assigned_on = timezone.localdate() - timedelta(days=1)
        batch.save(update_fields=["assigned_on"])
        self.login_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertNotContains(response, 'id="paskirti-darbai"', html=False)

    def test_parent_can_cancel_one_waiting_task(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            blocks_rewards=True,
        )
        item = batch.items.get()
        self.client.login(username="parent", password=self.parent_password)
        self.client.post(
            reverse("parent_cancel_assigned_task", args=[item.pk])
        )
        item.refresh_from_db()
        self.assertEqual(item.status, AssignedTaskStatus.CANCELLED)
        self.assertFalse(assigned_tasks_block_rewards(self.child))

    def test_parent_can_cancel_all_remaining_tasks_in_batch(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
            custom_title="Feed the cat",
            custom_points=7,
            blocks_rewards=True,
        )
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.post(
            reverse("parent_cancel_assigned_task_batch", args=[batch.pk]),
            follow=True,
        )
        self.assertContains(response, "remaining assigned tasks were cancelled")
        self.assertEqual(
            set(batch.items.values_list("status", flat=True)),
            {AssignedTaskStatus.CANCELLED},
        )
        self.assertFalse(assigned_tasks_block_rewards(self.child))

    def test_assign_dialog_lists_only_todays_batches(self):
        yesterday_task = Task.objects.create(title="Yesterday only", reward=5)
        today_task = Task.objects.create(title="Today only", reward=6)
        yesterday = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[yesterday_task],
        )
        yesterday.assigned_on = timezone.localdate() - timedelta(days=1)
        yesterday.save(update_fields=["assigned_on"])
        assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[today_task],
        )
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        child = next(
            item for item in response.context["children"] if item.pk == self.child.pk
        )
        titles = [
            assigned.title_snapshot
            for batch in child.assignment_batches
            for assigned in batch.items.all()
        ]
        self.assertContains(response, "Today's assigned tasks")
        self.assertEqual(titles, ["Today only"])

    def test_cancel_remaining_button_only_appears_for_waiting_batch(self):
        batch = assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Cancel remaining")
        complete_assigned_task(
            assigned_task=batch.items.get(),
            child=self.child,
        )
        response = self.client.get(reverse("parent_dashboard"))
        self.assertNotContains(response, "Cancel remaining")

    def test_direct_parent_award_disables_assignment_for_today(self):
        self.client.login(username="parent", password=self.parent_password)
        self.client.post(
            reverse("parent_award_task", args=[self.child.pk]),
            {"task_ids": [self.task.pk]},
        )
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(
            response,
            f'name="task_ids" value="{self.task.pk}" disabled',
            html=False,
        )

    def test_child_state_signature_changes_when_local_date_changes(self):
        self.login_child()
        today_response = self.client.get(reverse("child_state")).json()
        tomorrow = timezone.localdate() + timedelta(days=1)
        with patch("economy.views.child.timezone.localdate", return_value=tomorrow):
            tomorrow_response = self.client.get(reverse("child_state")).json()
        self.assertNotEqual(
            today_response["signature"],
            tomorrow_response["signature"],
        )

    def test_two_child_sessions_both_detect_new_assignment(self):
        first_client = self.client_class()
        second_client = self.client_class()
        for client in (first_client, second_client):
            session = client.session
            session["child_id"] = self.child.pk
            session.save()
        first_before = first_client.get(reverse("child_state")).json()["signature"]
        second_before = second_client.get(reverse("child_state")).json()["signature"]
        assign_tasks(
            child=self.child,
            actor=self.parent,
            tasks=[self.task],
        )
        first_after = first_client.get(reverse("child_state")).json()["signature"]
        second_after = second_client.get(reverse("child_state")).json()["signature"]
        self.assertNotEqual(first_before, first_after)
        self.assertNotEqual(second_before, second_after)
        self.assertEqual(first_after, second_after)


class AssignmentPresetTests(TestCase):
    parent_password = "Demo-safe-pass-123!"

    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "parent",
            password=self.parent_password,
        )
        self.child = ChildProfile.objects.create(
            name="Child",
            min_balance=-100,
            theme_selected=True,
        )
        self.task = Task.objects.create(title="Tidy room", reward=20, icon="🧹")

    def _save_daily(self, **kwargs):
        defaults = {
            "child": self.child,
            "actor": self.parent,
            "name": "Morning list",
            "tasks": [self.task],
            "cadence": AssignmentPresetCadence.DAILY,
            "run_at": time(7, 0),
        }
        defaults.update(kwargs)
        return save_assignment_preset(**defaults)

    def test_cadence_matching(self):
        monday = date(2026, 8, 10)
        saturday = date(2026, 8, 15)
        sunday = date(2026, 8, 16)
        weekdays = self._save_daily(
            name="School days",
            cadence=AssignmentPresetCadence.WEEKDAYS,
            weekday_mask=(1 << 0) | (1 << 2),
        )
        weekend = self._save_daily(
            name="Weekend both",
            cadence=AssignmentPresetCadence.WEEKEND,
            weekend_mode=AssignmentPresetWeekendMode.BOTH,
        )
        weekly = self._save_daily(
            name="Mondays",
            cadence=AssignmentPresetCadence.WEEKLY,
            weekly_weekday=0,
        )
        self.assertTrue(assignment_preset_matches_date(weekdays, monday))
        self.assertFalse(assignment_preset_matches_date(weekdays, saturday))
        self.assertTrue(assignment_preset_matches_date(weekend, saturday))
        self.assertTrue(assignment_preset_matches_date(weekend, sunday))
        self.assertFalse(assignment_preset_matches_date(weekend, monday))
        self.assertTrue(assignment_preset_matches_date(weekly, monday))
        self.assertFalse(assignment_preset_matches_date(weekly, saturday))

    def test_apply_preset_assigns_notes_and_custom_task(self):
        preset = save_assignment_preset(
            child=self.child,
            actor=self.parent,
            name="With notes",
            tasks=[self.task],
            task_notes={self.task.pk: "Fold towels."},
            custom_title="Feed the cat",
            custom_points=5,
            custom_note="Blue bowl.",
            blocks_rewards=True,
        )
        batch = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNotNone(batch)
        self.assertTrue(batch.blocks_rewards)
        self.assertEqual(batch.items.count(), 2)
        self.assertEqual(
            batch.items.get(task=self.task).note_snapshot,
            "Fold towels.",
        )
        self.assertEqual(
            batch.items.get(task__isnull=True).note_snapshot,
            "Blue bowl.",
        )

    @patch("economy.views.parent_actions.notify_assigned_tasks")
    def test_parent_save_apply_pause_and_delete(self, notify):
        self.client.login(username="parent", password=self.parent_password)
        response = self.client.post(
            reverse("parent_save_assignment_preset", args=[self.child.pk]),
            {
                "preset_name": "School mornings",
                "task_ids": [self.task.pk],
                f"task_note_{self.task.pk}": "Before breakfast.",
                "cadence": "weekdays",
                "weekdays": ["0", "1", "2", "3", "4"],
                "run_at": "07:30",
            },
            follow=True,
        )
        self.assertContains(response, "Saved set")
        preset = AssignmentPreset.objects.get(child=self.child)
        self.assertEqual(preset.weekday_mask, 31)
        self.assertEqual(preset.run_at, time(7, 30))
        self.assertContains(response, "School mornings")
        self.assertContains(response, "Saved sets")

        apply_response = self.client.post(
            reverse("parent_apply_assignment_preset", args=[preset.pk]),
            follow=True,
        )
        self.assertContains(apply_response, "Tasks were assigned")
        self.assertEqual(self.child.assigned_task_batches.count(), 1)
        notify.assert_called_once()

        pause_response = self.client.post(
            reverse("parent_toggle_assignment_preset", args=[preset.pk]),
            follow=True,
        )
        self.assertContains(pause_response, "Paused")
        preset.refresh_from_db()
        self.assertTrue(preset.is_paused)

        delete_response = self.client.post(
            reverse("parent_delete_assignment_preset", args=[preset.pk]),
            follow=True,
        )
        self.assertContains(delete_response, "Deleted")
        self.assertFalse(AssignmentPreset.objects.filter(pk=preset.pk).exists())

    @patch("economy.push.notify_assigned_tasks")
    def test_auto_run_once_per_day_and_skips_paused(self, notify_push):
        active = self._save_daily(name="Active set", run_at=time(7, 0))
        paused = self._save_daily(name="Paused set", run_at=time(7, 0))
        paused.is_paused = True
        paused.save(update_fields=["is_paused", "updated_at"])
        now = timezone.make_aware(
            datetime.combine(timezone.localdate(), time(8, 0))
        )
        created = run_due_assignment_presets(current_time=now)
        self.assertEqual(len(created), 1)
        active.refresh_from_db()
        paused.refresh_from_db()
        self.assertEqual(active.last_auto_assigned_on, timezone.localdate())
        self.assertIsNone(paused.last_auto_assigned_on)
        self.assertEqual(self.child.assigned_task_batches.count(), 1)
        notify_push.assert_called_once()

        second = run_due_assignment_presets(current_time=now)
        self.assertEqual(second, [])
        self.assertEqual(self.child.assigned_task_batches.count(), 1)

    def test_preset_limit_per_child(self):
        for index in range(5):
            self._save_daily(name=f"Set {index}")
        with self.assertRaises(ValidationError):
            self._save_daily(name="Too many")

    def test_repeated_apply_skips_custom_task_already_counting_today(self):
        preset = save_assignment_preset(
            child=self.child,
            actor=self.parent,
            name="Custom only",
            tasks=[],
            custom_title="Feed the cat",
            custom_points=5,
        )
        first = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNotNone(first)
        self.assertEqual(first.items.count(), 1)
        preset.refresh_from_db()
        self.assertEqual(preset.last_auto_assigned_on, timezone.localdate())

        second = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNone(second)
        self.assertEqual(self.child.assigned_task_batches.count(), 1)

        custom_item = first.items.get(task__isnull=True)
        complete_assigned_task(assigned_task=custom_item, child=self.child)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 5)

        third = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNone(third)
        self.assertEqual(self.child.assigned_task_batches.count(), 1)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 5)

    def test_manual_apply_blocks_same_day_auto_run(self):
        preset = self._save_daily(
            name="Manual first",
            tasks=[],
            custom_title="Water plants",
            custom_points=3,
            run_at=time(7, 0),
        )
        batch = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNotNone(batch)
        preset.refresh_from_db()
        self.assertEqual(preset.last_auto_assigned_on, timezone.localdate())

        now = timezone.make_aware(
            datetime.combine(timezone.localdate(), time(8, 0))
        )
        with patch("economy.push.notify_assigned_tasks") as notify_push:
            created = run_due_assignment_presets(current_time=now)
        self.assertEqual(created, [])
        notify_push.assert_not_called()
        self.assertEqual(self.child.assigned_task_batches.count(), 1)

    def test_cancelled_custom_task_can_be_reapplied_same_day(self):
        preset = save_assignment_preset(
            child=self.child,
            actor=self.parent,
            name="Custom cancel",
            tasks=[],
            custom_title="Feed the cat",
            custom_points=5,
        )
        first = apply_assignment_preset(preset=preset, actor=self.parent)
        cancel_assigned_task(
            assigned_task=first.items.get(),
            actor=self.parent,
        )
        second = apply_assignment_preset(preset=preset, actor=self.parent)
        self.assertIsNotNone(second)
        self.assertEqual(self.child.assigned_task_batches.count(), 2)
