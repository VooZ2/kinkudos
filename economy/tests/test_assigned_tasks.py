from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    AssignedTaskStatus,
    ChildProfile,
    LedgerKind,
    RequestStatus,
    Reward,
    Task,
    TaskClaim,
    TaskCompletion,
    Theme,
)
from economy.services import (
    approve_reward_request,
    approve_task_claim,
    assign_tasks,
    assigned_tasks_block_rewards,
    cancel_assigned_task,
    complete_assigned_task,
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
        self.assertIsNone(items[1].task)
        self.assertEqual(items[1].title_snapshot, "Feed the cat")
        self.assertEqual(items[1].reward_snapshot, 7)
        self.task.reward = 99
        self.task.save(update_fields=["reward"])
        items[0].refresh_from_db()
        self.assertEqual(items[0].reward_snapshot, 20)

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

    @patch("economy.views.notify_assigned_tasks")
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
        with patch("economy.views.timezone.localdate", return_value=tomorrow):
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
