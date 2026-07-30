from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from economy.models import (
    ChildProfile,
    LedgerEntry,
    LedgerKind,
    PenaltyTemplate,
    Proposal,
    ProposalType,
    RequestStatus,
    Reward,
    SavingsGoal,
    Task,
)
from economy.services import (
    approve_proposal,
    approve_reward_request,
    approve_task_claim,
    post_ledger_entry,
    reject_task_claim,
    submit_reward_request,
    submit_task,
)


class EconomyServiceTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("tevai", password="Very-safe-pass-123!")
        self.child = ChildProfile(name="Child One", min_balance=-100)
        self.child.set_pin("1234")
        self.child.save()
        self.task = Task.objects.create(title="Testas", reward=50)
        self.reward = Reward.objects.create(title="Ekrano laikas", cost=100)

    def test_pin_lockout_after_five_failures(self):
        for _ in range(4):
            self.assertFalse(self.child.verify_pin("9999"))
            self.child.refresh_from_db()
            self.assertFalse(self.child.is_locked)
        self.assertFalse(self.child.verify_pin("9999"))
        self.child.refresh_from_db()
        self.assertTrue(self.child.is_locked)
        self.assertFalse(self.child.verify_pin("1234"))

    def test_task_approval_posts_immutable_ledger_entry(self):
        claim = submit_task(child=self.child, task=self.task)
        entry = approve_task_claim(claim=claim, actor=self.parent)
        self.child.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual(self.child.balance, 50)
        self.assertEqual(entry.balance_after, 50)
        self.assertEqual(claim.status, RequestStatus.APPROVED)
        entry.description = "Pakeista"
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()

    def test_duplicate_pending_task_is_rejected(self):
        submit_task(child=self.child, task=self.task)
        with self.assertRaises(ValidationError):
            submit_task(child=self.child, task=self.task)

    def test_rejected_task_allows_optional_comment_and_does_not_change_balance(self):
        claim = submit_task(child=self.child, task=self.task)
        reject_task_claim(claim=claim, actor=self.parent, reason=" ")
        self.child.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual(self.child.balance, 0)
        self.assertEqual(claim.status, RequestStatus.REJECTED)
        self.assertEqual(claim.rejection_reason, "")

    def test_reward_requests_pause_after_half_credit_is_used(self):
        request = submit_reward_request(child=self.child, reward=self.reward)
        approve_reward_request(request=request, actor=self.parent)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, -100)

        second_reward = Reward.objects.create(title="Per brangu", cost=1)
        with self.assertRaises(ValidationError):
            submit_reward_request(child=self.child, reward=second_reward)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, -100)

    def test_reward_request_boundary_is_exactly_half_of_credit(self):
        post_ledger_entry(
            child=self.child,
            delta=-49,
            kind=LedgerKind.ADJUSTMENT,
            description="Credit boundary setup",
            actor=self.parent,
        )
        first_reward = Reward.objects.create(title="Allowed below half", cost=1)
        submit_reward_request(child=self.child, reward=first_reward)

        post_ledger_entry(
            child=self.child,
            delta=-1,
            kind=LedgerKind.ADJUSTMENT,
            description="Reach half credit",
            actor=self.parent,
        )
        self.child.refresh_from_db()
        blocked_reward = Reward.objects.create(title="Blocked at half", cost=1)
        with self.assertRaises(ValidationError):
            submit_reward_request(child=self.child, reward=blocked_reward)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, -50)

    def test_reward_request_respects_balance_and_credit_limit(self):
        post_ledger_entry(
            child=self.child,
            delta=50,
            kind=LedgerKind.ADJUSTMENT,
            description="Available reward balance",
            actor=self.parent,
        )
        self.child.refresh_from_db()

        exact_limit_reward = Reward.objects.create(title="Exactly affordable", cost=150)
        request = submit_reward_request(child=self.child, reward=exact_limit_reward)
        self.assertEqual(request.cost_snapshot, 150)

        too_expensive_reward = Reward.objects.create(title="Too expensive", cost=151)
        with self.assertRaisesMessage(
            ValidationError,
            "You do not have enough points for this reward.",
        ):
            submit_reward_request(child=self.child, reward=too_expensive_reward)
        self.assertFalse(
            self.child.reward_requests.filter(reward=too_expensive_reward).exists()
        )

    def test_penalty_can_cross_spending_limit(self):
        penalty = PenaltyTemplate.objects.create(title="Bausmė", amount=-150)
        post_ledger_entry(
            child=self.child,
            delta=penalty.amount,
            kind=LedgerKind.PENALTY,
            description="Bausmė: paaiškinimas",
            actor=self.parent,
            source_id=penalty.pk,
        )
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, -150)

    def test_reward_and_goal_proposals_create_expected_objects(self):
        reward_proposal = Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.REWARD,
            title="Išvyka",
            suggested_cost=300,
        )
        created_reward = approve_proposal(
            proposal=reward_proposal,
            actor=self.parent,
            final_cost=350,
        )
        self.assertIsInstance(created_reward, Reward)
        self.assertEqual(created_reward.cost, 350)

        goal_proposal = Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.GOAL,
            title="Dviratis",
            suggested_cost=500,
        )
        created_goal = approve_proposal(
            proposal=goal_proposal,
            actor=self.parent,
            final_cost=550,
        )
        self.assertIsInstance(created_goal, SavingsGoal)
        self.assertEqual(created_goal.child, self.child)

    def test_balance_equals_ledger_sum(self):
        post_ledger_entry(
            child=self.child,
            delta=25,
            kind=LedgerKind.ADJUSTMENT,
            description="Pradžia",
            actor=self.parent,
        )
        post_ledger_entry(
            child=self.child,
            delta=-10,
            kind=LedgerKind.ADJUSTMENT,
            description="Korekcija",
            actor=self.parent,
        )
        self.child.refresh_from_db()
        ledger_sum = sum(LedgerEntry.objects.filter(child=self.child).values_list("delta", flat=True))
        self.assertEqual(self.child.balance, ledger_sum)
