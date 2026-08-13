from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    BirthDateChangeRequest,
    ChildProfile,
    GoalCompletionRequest,
    GoalMode,
    GoalStatus,
    LotteryTicket,
    Proposal,
    ProposalType,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsContribution,
    SavingsGoal,
    Task,
    TaskClaim,
)


class ParentPendingStateTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Very-safe-parent-123!",
        )
        self.child = ChildProfile.objects.create(name="Child", theme_selected=True)
        self.other_child = ChildProfile.objects.create(
            name="Other child",
            theme_selected=True,
        )
        self.task = Task.objects.create(title="Clean room", reward=10)

    def login_parent(self):
        self.client.force_login(self.parent)

    def test_authentication_and_child_scope_are_enforced(self):
        response = self.client.get(reverse("parent_pending_state"))
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()
        response = self.client.get(reverse("parent_pending_state"))
        self.assertEqual(response.status_code, 302)

    def test_zero_pending_requests_returns_empty_fragment_and_state_headers(self):
        self.login_parent()

        response = self.client.get(reverse("parent_pending_state"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 0)
        self.assertIn("No pending requests", payload["html"])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertIn("Cookie", response["Vary"])
        self.assertTrue(response["ETag"])

    def test_combined_pending_types_and_home_order_are_shared(self):
        older = TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title="Older task",
            reward_snapshot=10,
        )
        TaskClaim.objects.filter(pk=older.pk).update(
            submitted_at=timezone.now() - timedelta(minutes=5)
        )
        reward = Reward.objects.create(title="Ice cream", cost=20)
        RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.REWARD,
            title="New game",
            suggested_cost=30,
        )
        goal = SavingsGoal.objects.create(
            child=self.child,
            title="Bicycle",
            target_amount=10,
            mode=GoalMode.AVAILABLE,
            status=GoalStatus.ACTIVE,
        )
        self.child.balance = 10
        self.child.save(update_fields=["balance"])
        GoalCompletionRequest.objects.create(goal=goal)
        BirthDateChangeRequest.objects.create(
            child=self.child,
            previous_birth_date=date(2015, 1, 1),
            requested_birth_date=date(2015, 1, 2),
        )
        self.login_parent()

        state = self.client.get(reverse("parent_pending_state")).json()
        dashboard = self.client.get(reverse("parent_dashboard")).content.decode()

        self.assertEqual(state["count"], 5)
        self.assertEqual(dashboard.count('class="pending-request-row'), 5)
        self.assertLess(state["html"].index("Older task"), state["html"].index("Ice cream"))
        self.assertLess(state["html"].index("Ice cream"), state["html"].index("New game"))
        self.assertLess(state["html"].index("New game"), state["html"].index("Bicycle"))
        self.assertLess(state["html"].index("Bicycle"), state["html"].index("Birthday change"))
        self.assertIn(f'data-pending-revision="{state["revision"]}"', dashboard)
        self.assertIn('data-parent-home-badge', dashboard)

        older.delete()

    def test_revision_changes_for_same_count_content_replacement(self):
        claim = TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title="First task",
            reward_snapshot=10,
        )
        self.login_parent()
        first = self.client.get(reverse("parent_pending_state")).json()

        TaskClaim.objects.filter(pk=claim.pk).update(task_title="Replacement task")
        second_response = self.client.get(reverse("parent_pending_state"))
        second = second_response.json()

        self.assertEqual(first["count"], second["count"])
        self.assertNotEqual(first["revision"], second["revision"])
        self.assertIn("Replacement task", second["html"])

    def test_unchanged_etag_returns_304_without_fragment(self):
        self.login_parent()
        first = self.client.get(reverse("parent_pending_state"))

        second = self.client.get(
            reverse("parent_pending_state"),
            HTTP_IF_NONE_MATCH=first["ETag"],
        )

        self.assertEqual(second.status_code, 304)
        self.assertEqual(second.content, b"")
        self.assertEqual(second["Cache-Control"], "private, no-store")
        self.assertIn("Cookie", second["Vary"])
        self.assertEqual(second["ETag"], first["ETag"])

    def test_parent_pending_state_query_count_stays_lightweight(self):
        TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.login_parent()

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("parent_pending_state"))

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 20)


class ChildStateSignatureTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("parent")
        self.child = ChildProfile.objects.create(name="Child", theme_selected=True)
        self.other_child = ChildProfile.objects.create(
            name="Other child",
            theme_selected=True,
        )
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def signature(self):
        return self.client.get(reverse("child_state")).json()["signature"]

    def test_child_visible_parent_changes_update_signature(self):
        before = self.signature()
        self.child.min_balance = -25
        self.child.save(update_fields=["min_balance"])
        self.assertNotEqual(before, self.signature())

        task = Task.objects.create(title="Task", reward=10)
        claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
        )
        before = self.signature()
        TaskClaim.objects.filter(pk=claim.pk).update(status=RequestStatus.REJECTED)
        self.assertNotEqual(before, self.signature())

        reward = Reward.objects.create(title="Reward", cost=10)
        reward_request = RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        before = self.signature()
        RewardRequest.objects.filter(pk=reward_request.pk).update(status=RequestStatus.REJECTED)
        self.assertNotEqual(before, self.signature())

        batch = AssignedTaskBatch.objects.create(child=self.child, assigned_by=self.parent)
        before = self.signature()
        AssignedTask.objects.create(
            batch=batch,
            title_snapshot="Assigned",
            reward_snapshot=5,
        )
        self.assertNotEqual(before, self.signature())

        before = self.signature()
        Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.REWARD,
            title="Proposal",
            suggested_cost=15,
        )
        self.assertNotEqual(before, self.signature())

        goal = SavingsGoal.objects.create(
            child=self.child,
            title="Goal",
            target_amount=25,
            mode=GoalMode.SAVED,
        )
        before = self.signature()
        SavingsContribution.objects.create(goal=goal, amount=5)
        self.assertNotEqual(before, self.signature())

        before = self.signature()
        LotteryTicket.objects.create(
            child=self.child,
            week_start=timezone.localdate(),
            values=[1, 2, 3],
            prize_amount=0,
        )
        self.assertNotEqual(before, self.signature())

    def test_sibling_changes_do_not_update_this_child_signature(self):
        before = self.signature()
        self.other_child.balance = 99
        self.other_child.save(update_fields=["balance"])
        self.assertEqual(before, self.signature())

    def test_child_state_query_count_stays_lightweight(self):
        for index in range(8):
            task = Task.objects.create(title=f"Task {index}", reward=10)
            TaskClaim.objects.create(
                child=self.child,
                task=task,
                task_title=task.title,
                reward_snapshot=task.reward,
            )
            Reward.objects.create(title=f"Reward {index}", cost=5)

        self.client.get(reverse("child_state"))  # warm session / auth queries

        with CaptureQueriesContext(connection) as baseline:
            first = self.client.get(reverse("child_state"))
        self.assertEqual(first.status_code, 200)

        for index in range(8, 40):
            task = Task.objects.create(title=f"Task {index}", reward=10)
            TaskClaim.objects.create(
                child=self.child,
                task=task,
                task_title=task.title,
                reward_snapshot=task.reward,
            )

        with CaptureQueriesContext(connection) as grown:
            second = self.client.get(reverse("child_state"))
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(baseline), len(grown))
        self.assertLessEqual(len(grown), 35)


class RefreshFrontendContractTests(TestCase):
    def test_refresh_contract_uses_one_ten_second_visible_scheduler(self):
        script = Path("static/js/app.js").read_text(encoding="utf-8")
        self.assertIn("const REFRESH_INTERVAL_MS = 10000;", script)
        self.assertNotIn("setInterval(checkChildState", script)
        self.assertNotIn("setInterval(refreshPendingRequests", script)
        self.assertIn("window.addEventListener(\"pageshow\", forceParentStateCheck)", script)
        self.assertIn("window.addEventListener(\"pageshow\", forceChildStateCheck)", script)
        self.assertIn("If-None-Match", script)

    def test_parent_polling_requires_workspace_and_pending_fragment(self):
        script = Path("static/js/app.js").read_text(encoding="utf-8")

        self.assertIn('document.querySelector("[data-parent-shell]")', script)
        self.assertIn(
            'document.querySelector("[data-pending-requests-fragment]")',
            script,
        )
        self.assertIn("parentWorkspace && initialPendingFragment", script)
        self.assertEqual(script.count("let parentStateTimer = null"), 1)

    def test_evidence_lightbox_uses_delegation_for_refreshed_fragments(self):
        script = Path("static/js/app.js").read_text(encoding="utf-8")

        self.assertIn('event.target.closest?.("[data-evidence-full]")', script)
        self.assertNotIn(
            'document.querySelectorAll("[data-evidence-full]").forEach',
            script,
        )
        self.assertIn('navItem.querySelector(".parent-nav-icon") || navItem', script)


class ParentPollingTemplateScopeTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("polling-parent")
        self.client.force_login(self.parent)

    def test_parent_workspace_exposes_pending_state_configuration(self):
        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'parentStateUrl: "')
        self.assertContains(response, reverse("parent_pending_state"))
        self.assertContains(response, "data-parent-shell")
        self.assertContains(response, "data-pending-requests-fragment")

    def test_authenticated_non_workspace_page_does_not_expose_parent_polling(self):
        response = self.client.get(reverse("changelog"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "parentStateUrl")
        self.assertNotContains(response, "data-parent-shell")
        self.assertNotContains(response, "data-pending-requests-fragment")
