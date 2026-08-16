from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from economy.models import (
    ChildProfile,
    GoalMode,
    GoalStatus,
    LedgerEntry,
    LedgerKind,
    RequestStatus,
    Reward,
    SavingsContributionState,
    SavingsGoal,
)
from economy.services import (
    add_saved_points,
    approve_goal_completion,
    create_savings_goal,
    delete_savings_goal,
    post_ledger_entry,
    request_goal_completion,
    return_saved_points,
    select_goal_mode,
    submit_reward_request,
)


class SavingsGoalServiceTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "goal-parent",
            password="Very-safe-pass-123!",
        )
        self.child = ChildProfile(name="Goal child", min_balance=0, theme_selected=True)
        self.child.set_pin("1234")
        self.child.save()

    def fund_child(self, amount):
        post_ledger_entry(
            child=self.child,
            delta=amount,
            kind=LedgerKind.ADJUSTMENT,
            description="Goal test funding",
            actor=self.parent,
        )

    def make_goal(self, target=100):
        return create_savings_goal(
            child=self.child,
            title="Bicycle",
            target_amount=target,
            actor=self.parent,
        )

    def test_saved_transfer_moves_spendable_points_and_tracks_contribution(self):
        self.fund_child(140)
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)

        add_saved_points(goal=goal, child=self.child, amount=50, actor=self.parent)

        self.child.refresh_from_db()
        goal.refresh_from_db()
        self.assertEqual(self.child.balance, 90)
        self.assertEqual(goal.saved_amount, 50)
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child).order_by("pk").last().kind,
            LedgerKind.SAVINGS_TRANSFER,
        )

    def test_saved_points_cannot_fund_rewards_or_credit_transfers(self):
        self.fund_child(100)
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=100)
        reward = Reward.objects.create(title="Screen time", cost=1)

        with self.assertRaisesMessage(
            ValidationError,
            "You do not have enough points for this reward.",
        ):
            submit_reward_request(child=self.child, reward=reward)

        post_ledger_entry(
            child=self.child,
            delta=-1,
            kind=LedgerKind.ADJUSTMENT,
            description="Credit test",
        )
        credit_goal = self.make_goal(target=200)
        select_goal_mode(goal=credit_goal, child=self.child, mode=GoalMode.SAVED)
        with self.assertRaisesMessage(
            ValidationError,
            "You can save only points you currently have available.",
        ):
            add_saved_points(goal=credit_goal, child=self.child, amount=1)
        self.assertEqual(goal.contributions.count(), 1)

    def test_saved_transfer_cannot_exceed_balance_or_goal_remainder(self):
        self.fund_child(140)
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=60)

        with self.assertRaisesMessage(
            ValidationError,
            "You can add at most 40 points to reach this goal.",
        ):
            add_saved_points(goal=goal, child=self.child, amount=41)
        self.assertEqual(goal.contributions.filter(state=SavingsContributionState.ACTIVE).count(), 1)

    def test_available_progress_ignores_credit_and_switching_current_goal_has_no_ledger_entry(self):
        self.fund_child(100)
        first = self.make_goal(target=150)
        second = create_savings_goal(
            child=self.child,
            title="Holiday",
            target_amount=200,
            actor=self.parent,
        )
        select_goal_mode(goal=first, child=self.child, mode=GoalMode.AVAILABLE)
        first.refresh_from_db()
        self.assertEqual(first.progress_amount, 100)

        post_ledger_entry(
            child=self.child,
            delta=-150,
            kind=LedgerKind.ADJUSTMENT,
            description="Spend into credit",
        )
        first.refresh_from_db()
        self.assertEqual(first.progress_amount, 0)
        ledger_count = LedgerEntry.objects.filter(child=self.child).count()

        select_goal_mode(goal=second, child=self.child, mode=GoalMode.AVAILABLE)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertIsNone(first.mode)
        self.assertEqual(second.mode, GoalMode.AVAILABLE)
        self.assertEqual(LedgerEntry.objects.filter(child=self.child).count(), ledger_count)

    def test_database_allows_only_one_current_goal_per_child(self):
        first = self.make_goal()
        SavingsGoal.objects.create(
            child=self.child,
            title="Holiday",
            target_amount=200,
            mode=GoalMode.SAVED,
        )
        first.mode = GoalMode.AVAILABLE
        first.save(update_fields=["mode"])
        second = SavingsGoal.objects.create(
            child=self.child,
            title="Computer",
            target_amount=300,
        )
        second.mode = GoalMode.AVAILABLE
        with self.assertRaises(IntegrityError):
            second.save(update_fields=["mode"])

    def test_returning_saved_points_restores_spendable_balance(self):
        self.fund_child(140)
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=50)

        returned = return_saved_points(goal=goal, actor=self.parent)

        self.child.refresh_from_db()
        goal.refresh_from_db()
        self.assertEqual(returned, 50)
        self.assertEqual(self.child.balance, 140)
        self.assertEqual(goal.saved_amount, 0)
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child, kind=LedgerKind.SAVINGS_RETURN)
            .values_list("delta", flat=True)
            .get(),
            50,
        )

    def test_deleting_goal_without_saved_points_archives_it_and_cancels_pending_request(self):
        self.fund_child(100)
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.AVAILABLE)
        completion_request = request_goal_completion(goal=goal, child=self.child)

        delete_savings_goal(goal=goal, actor=self.parent)

        goal.refresh_from_db()
        completion_request.refresh_from_db()
        self.assertEqual(goal.status, GoalStatus.CANCELLED)
        self.assertIsNone(goal.mode)
        self.assertEqual(completion_request.status, RequestStatus.CANCELLED)
        self.assertFalse(
            LedgerEntry.objects.filter(child=self.child, kind=LedgerKind.SAVINGS_RETURN).exists()
        )
        self.assertEqual(
            goal.events.filter(description="Goal deleted: Bicycle").get().description,
            "Goal deleted: Bicycle",
        )

    def test_deleting_saved_goal_returns_points_once_and_keeps_event_history(self):
        self.fund_child(100)
        goal = self.make_goal(target=50)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=50)
        completion_request = request_goal_completion(goal=goal, child=self.child)

        _deleted_goal, returned_amount = delete_savings_goal(
            goal=goal,
            actor=self.parent,
        )

        self.child.refresh_from_db()
        goal.refresh_from_db()
        completion_request.refresh_from_db()
        self.assertEqual(returned_amount, 50)
        self.assertEqual(self.child.balance, 100)
        self.assertEqual(goal.status, GoalStatus.CANCELLED)
        self.assertIsNone(goal.mode)
        self.assertEqual(completion_request.status, RequestStatus.CANCELLED)
        self.assertEqual(
            goal.contributions.get().state,
            SavingsContributionState.RETURNED,
        )
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child, kind=LedgerKind.SAVINGS_RETURN)
            .values_list("delta", flat=True)
            .count(),
            1,
        )
        self.assertEqual(
            goal.events.order_by("-pk").first().description,
            "Goal deleted: Bicycle · 50 points returned",
        )

        with self.assertRaises(SavingsGoal.DoesNotExist):
            delete_savings_goal(goal=goal, actor=self.parent)
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child, kind=LedgerKind.SAVINGS_RETURN)
            .count(),
            1,
        )

    def test_saved_goal_completion_consumes_saved_points_without_second_deduction(self):
        self.fund_child(100)
        goal = self.make_goal(target=50)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=50)
        completion_request = request_goal_completion(goal=goal, child=self.child)

        approve_goal_completion(completion_request=completion_request, actor=self.parent)

        self.child.refresh_from_db()
        goal.refresh_from_db()
        self.assertEqual(self.child.balance, 50)
        self.assertEqual(goal.status, GoalStatus.COMPLETED)
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child, delta__lt=0).count(),
            1,
        )
        self.assertEqual(
            goal.contributions.get().state,
            SavingsContributionState.CONSUMED,
        )

    def test_available_goal_completion_deducts_once_and_duplicate_approval_is_rejected(self):
        self.fund_child(100)
        goal = self.make_goal(target=60)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.AVAILABLE)
        completion_request = request_goal_completion(goal=goal, child=self.child)

        approve_goal_completion(completion_request=completion_request, actor=self.parent)

        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 40)
        self.assertEqual(
            LedgerEntry.objects.filter(child=self.child, kind=LedgerKind.GOAL_COMPLETION)
            .values_list("delta", flat=True)
            .get(),
            -60,
        )
        with self.assertRaisesMessage(
            ValidationError,
            "This goal request has already been resolved.",
        ):
            approve_goal_completion(completion_request=completion_request, actor=self.parent)

    def test_available_goal_approval_rechecks_balance_and_duplicate_requests_are_rejected(self):
        self.fund_child(100)
        goal = self.make_goal(target=80)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.AVAILABLE)
        completion_request = request_goal_completion(goal=goal, child=self.child)
        with self.assertRaisesMessage(
            ValidationError,
            "This goal is already waiting for parent approval.",
        ):
            request_goal_completion(goal=goal, child=self.child)

        post_ledger_entry(
            child=self.child,
            delta=-30,
            kind=LedgerKind.ADJUSTMENT,
            description="Spend before approval",
        )
        with self.assertRaisesMessage(
            ValidationError,
            "The goal cannot be completed because the available balance changed.",
        ):
            approve_goal_completion(completion_request=completion_request, actor=self.parent)
        completion_request.refresh_from_db()
        self.assertEqual(completion_request.status, RequestStatus.PENDING)

    def test_concurrent_completion_request_becomes_validation_error(self):
        self.fund_child(100)
        goal = self.make_goal(target=80)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.AVAILABLE)

        with patch(
            "economy.services.GoalCompletionRequest.objects.create",
            side_effect=IntegrityError("duplicate pending request"),
        ):
            with self.assertRaisesMessage(
                ValidationError,
                "This goal is already waiting for parent approval.",
            ):
                request_goal_completion(goal=goal, child=self.child)

    def test_child_goal_mode_endpoint_is_scoped_to_logged_in_child(self):
        other_child = ChildProfile(name="Other child", theme_selected=True)
        other_child.set_pin("5678")
        other_child.save()
        goal = SavingsGoal.objects.create(
            child=other_child,
            title="Other goal",
            target_amount=100,
        )
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.post(
            reverse("child_set_goal_mode", args=[goal.pk]),
            {"mode": GoalMode.SAVED},
        )

        self.assertEqual(response.status_code, 404)
        goal.refresh_from_db()
        self.assertIsNone(goal.mode)

    def test_child_without_goals_does_not_render_an_empty_goal_section(self):
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.get(reverse("child_dashboard"))

        self.assertNotContains(response, 'id="tikslai"', html=False)
        self.assertNotContains(response, "There are no active goals yet.")

    def test_saved_goal_dialog_uses_non_negative_available_balance(self):
        goal = self.make_goal()
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        post_ledger_entry(
            child=self.child,
            delta=-10,
            kind=LedgerKind.ADJUSTMENT,
            description="Goal test credit",
        )
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, "Available balance: 0 points")
        self.assertContains(response, 'data-goal-available="0"')
        self.assertContains(response, 'max="0"')

    def test_goal_mode_dialog_includes_csrf_token_for_confirmation(self):
        goal = self.make_goal()
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.get(reverse("child_dashboard"))

        html = response.content.decode()
        dialog_start = html.index(f'id="goal-mode-{goal.pk}"')
        dialog_end = html.index("</dialog>", dialog_start)
        self.assertIn('name="csrfmiddlewaretoken"', html[dialog_start:dialog_end])

    def test_parent_goal_summary_prioritises_reached_goals_waiting_for_approval(self):
        current = self.make_goal(target=100)
        select_goal_mode(goal=current, child=self.child, mode=GoalMode.AVAILABLE)
        saved = self.make_goal(target=10)
        select_goal_mode(goal=saved, child=self.child, mode=GoalMode.SAVED)
        self.fund_child(10)
        add_saved_points(goal=saved, child=self.child, amount=10)
        request_goal_completion(goal=saved, child=self.child)
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        child = response.context["children"][0]
        self.assertEqual(child.goal_summary.pk, saved.pk)

    def test_parent_goal_actions_use_official_archive_icon(self):
        self.make_goal()
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'href="#icon-box-archive"', html=False)
        self.assertContains(response, 'id="icon-box-archive"', html=False)
        self.assertContains(response, 'viewBox="0 0 512 512"', html=False)
        self.assertContains(response, 'fill="currentColor"', html=False)
        self.assertNotContains(response, 'fill-rule="evenodd"', html=False)
        self.assertContains(response, 'history-decision-informational', html=False)

    def test_parent_goal_editor_uses_official_delete_icon_and_confirmation(self):
        goal = self.make_goal()
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'href="#icon-pen-to-square"', html=False)
        self.assertNotContains(response, "icon-button--edit", html=False)
        self.assertContains(response, 'href="#icon-trash"', html=False)
        self.assertContains(response, 'data-open-dialog="delete-goal-', html=False)
        self.assertContains(response, "Delete goal?", html=False)
        self.assertContains(
            response,
            "This goal will be removed. This action cannot be undone.",
            html=False,
        )
        html = response.content.decode()
        form_start = html.index(f'id="edit-goal-{goal.pk}"')
        form_end = html.index("</form>", form_start)
        editor_html = html[form_start:form_end]
        self.assertIn('aria-label="Delete"', editor_html)
        self.assertIn('title="Delete"', editor_html)
        self.assertIn('href="#icon-trash"', editor_html)
        self.assertNotIn("icon-trash-can", editor_html)

    def test_parent_goal_info_button_sits_in_the_heading_not_the_status_row(self):
        self.fund_child(200)
        available = self.make_goal(target=250)
        select_goal_mode(goal=available, child=self.child, mode=GoalMode.AVAILABLE)
        saved = self.make_goal(target=200)
        saved.title = "Art supplies"
        saved.save(update_fields=["title"])
        select_goal_mode(goal=saved, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=saved, child=self.child, amount=185, actor=self.parent)
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))
        html = response.content.decode()

        def section(start_marker, end_marker, blob):
            start = blob.index(start_marker)
            end = blob.index(end_marker, start)
            return blob[start:end]

        saved_row = section(f'id="goal-item-{saved.pk}"', f'id="goal-parent-info-{saved.pk}"', html)
        heading = section('class="goal-manage-heading"', 'class="goal-manage-progress"', saved_row)
        status = section('class="goal-manage-status"', 'class="goal-manage-actions"', saved_row)
        self.assertIn("goal-parent-info-", heading)
        self.assertIn("info-button", heading)
        self.assertNotIn("info-button", status)
        self.assertIn("icon-circle-plus", saved_row)
        self.assertIn("icon-right-left", saved_row)
        stylesheet = (Path(__file__).resolve().parents[2] / "static" / "css" / "app.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("minmax(194px, max-content)", stylesheet)

    def test_parent_saved_goal_delete_confirmation_includes_amount_and_child(self):
        self.fund_child(100)
        goal = self.make_goal(target=80)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=50)
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Delete goal and return saved points?", html=False)
        self.assertContains(
            response,
            "50 saved points will be returned to Goal child’s available balance before this goal is removed.",
            html=False,
        )
        self.assertContains(response, "Return points and delete", html=False)

    def test_parent_can_delete_goal_through_the_explicit_post_endpoint(self):
        self.fund_child(100)
        goal = self.make_goal(target=50)
        select_goal_mode(goal=goal, child=self.child, mode=GoalMode.SAVED)
        add_saved_points(goal=goal, child=self.child, amount=50)
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_delete_goal", args=[goal.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Goal deleted and 50 points returned.")
        goal.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(goal.status, GoalStatus.CANCELLED)
        self.assertEqual(self.child.balance, 100)
