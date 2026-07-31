import json
import random
from collections import Counter
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from economy.lottery import (
    _draw_board,
    _draw_prize,
    lottery_state,
    lottery_week_start,
    purchase_lottery_ticket,
    reveal_lottery_ticket,
    send_due_lottery_reminders,
)
from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    ChildProfile,
    FamilySettings,
    LedgerKind,
    LotteryReminder,
    LotteryTicket,
    LotteryTicketStatus,
    PushSubscription,
    Theme,
)
from economy.templatetags.economy_tags import theme_text


class JackpotRng:
    def randint(self, lower, upper):
        return upper


class OutcomeRng:
    def __init__(self, rolls):
        self.rolls = iter(rolls)

    def randrange(self, _limit):
        return next(self.rolls)

    def randint(self, lower, _upper):
        return lower


class LotteryServiceTests(TestCase):
    def setUp(self):
        self.family = FamilySettings.load()
        self.child = ChildProfile.objects.create(
            name="Child",
            balance=100,
            min_balance=-100,
            theme_selected=True,
        )

    def test_board_has_exactly_one_three_number_match(self):
        values = _draw_board(42, random.Random(17))
        counts = Counter(values)

        self.assertEqual(len(values), 9)
        self.assertEqual(counts[42], 3)
        self.assertFalse(any(count >= 3 for value, count in counts.items() if value != 42))

    def test_standard_outcome_boundaries_are_50_30_20(self):
        positive = _draw_prize(self.child, OutcomeRng([49, 0]))
        negative = _draw_prize(self.child, OutcomeRng([50, 0]))
        no_prize = _draw_prize(self.child, OutcomeRng([80]))

        self.assertEqual(positive, 1)
        self.assertEqual(negative, -1)
        self.assertEqual(no_prize, 0)

    def test_no_prize_board_has_no_three_number_match(self):
        values = _draw_board(0, random.Random(9))

        self.assertFalse(any(count >= 3 for count in Counter(values).values()))
        self.assertNotIn(0, values)

    def test_purchase_costs_earned_points_and_creates_open_ticket(self):
        ticket = purchase_lottery_ticket(
            child=self.child,
            rng=random.Random(5),
        )

        self.child.refresh_from_db()
        self.assertEqual(
            self.child.balance,
            100 - self.family.lottery_ticket_cost,
        )
        self.assertEqual(ticket.status, LotteryTicketStatus.OPEN)
        self.assertEqual(
            ticket.purchase_ledger_entry.delta,
            -self.family.lottery_ticket_cost,
        )
        self.assertEqual(ticket.purchase_ledger_entry.kind, LedgerKind.LOTTERY)
        self.assertEqual(Counter(ticket.values)[ticket.prize_amount], 3)

    def test_ticket_cannot_be_bought_from_credit(self):
        self.child.balance = 14
        self.child.save(update_fields=["balance"])

        with self.assertRaisesMessage(
            ValidationError,
            "A lottery ticket can be bought only with 15 points you have earned.",
        ):
            purchase_lottery_ticket(child=self.child)

        self.assertFalse(LotteryTicket.objects.exists())

    def test_open_ticket_must_be_finished_before_another_purchase(self):
        purchase_lottery_ticket(child=self.child, rng=random.Random(3))

        with self.assertRaisesMessage(
            ValidationError,
            "Finish your open lottery ticket before buying another.",
        ):
            purchase_lottery_ticket(child=self.child)

    def test_assigned_reward_block_also_blocks_lottery(self):
        parent = get_user_model().objects.create_user("parent")
        batch = AssignedTaskBatch.objects.create(
            child=self.child,
            assigned_by=parent,
            blocks_rewards=True,
        )
        AssignedTask.objects.create(
            batch=batch,
            title_snapshot="Task",
            reward_snapshot=10,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Complete the assigned tasks before buying a lottery ticket.",
        ):
            purchase_lottery_ticket(child=self.child)

    def test_only_three_tickets_can_be_bought_in_a_calendar_week(self):
        for seed in range(3):
            ticket = purchase_lottery_ticket(
                child=self.child,
                rng=random.Random(seed),
            )
            reveal_lottery_ticket(ticket=ticket, child=self.child)
            self.child.refresh_from_db()
            if self.child.balance < self.family.lottery_ticket_cost:
                self.child.balance = 100
                self.child.save(update_fields=["balance"])

        state = lottery_state(self.child)
        self.assertEqual(state["tickets_used"], 3)
        self.assertEqual(state["tickets_remaining"], 0)
        with self.assertRaisesMessage(
            ValidationError,
            "You have already used all 3 lottery tickets this week.",
        ):
            purchase_lottery_ticket(child=self.child)

    def test_configured_cost_and_weekly_limit_are_enforced(self):
        self.family.lottery_ticket_cost = 25
        self.family.lottery_weekly_limit = 1
        self.family.save(
            update_fields=["lottery_ticket_cost", "lottery_weekly_limit"]
        )

        ticket = purchase_lottery_ticket(child=self.child, rng=random.Random(1))
        revealed = reveal_lottery_ticket(ticket=ticket, child=self.child)
        self.child.refresh_from_db()

        state = lottery_state(self.child)
        self.assertEqual(ticket.purchase_ledger_entry.delta, -25)
        self.assertEqual(self.child.balance, 75 + revealed.applied_delta)
        self.assertEqual(state["ticket_cost"], 25)
        self.assertEqual(state["weekly_limit"], 1)
        self.assertEqual(state["tickets_remaining"], 0)
        with self.assertRaisesMessage(
            ValidationError,
            "You have already used all 1 lottery tickets this week.",
        ):
            purchase_lottery_ticket(child=self.child)

    def test_family_switch_has_priority_over_child_switch(self):
        self.family.lottery_enabled = False
        self.family.save(update_fields=["lottery_enabled"])

        state = lottery_state(self.child)

        self.assertFalse(state["feature_enabled"])
        self.assertFalse(state["is_visible"])
        with self.assertRaisesMessage(ValidationError, "Lottery tickets are disabled."):
            purchase_lottery_ticket(child=self.child)

    def test_child_switch_disables_only_that_child(self):
        self.child.lottery_enabled = False
        self.child.save(update_fields=["lottery_enabled"])
        other = ChildProfile.objects.create(name="Other", balance=100)

        self.assertFalse(lottery_state(self.child)["feature_enabled"])
        self.assertTrue(lottery_state(other)["feature_enabled"])

    def test_open_ticket_remains_visible_and_can_be_revealed_after_disabling(self):
        ticket = purchase_lottery_ticket(child=self.child, rng=random.Random(4))
        self.family.lottery_enabled = False
        self.family.save(update_fields=["lottery_enabled"])

        state = lottery_state(self.child)
        revealed = reveal_lottery_ticket(ticket=ticket, child=self.child)

        self.assertTrue(state["is_visible"])
        self.assertEqual(state["open_ticket"], ticket)
        self.assertEqual(revealed.status, LotteryTicketStatus.REVEALED)

    def test_weekly_limit_resets_on_monday(self):
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        previous_week = monday - timedelta(days=7)
        LotteryTicket.objects.create(
            child=self.child,
            week_start=previous_week,
            values=_draw_board(10, random.Random(1)),
            prize_amount=10,
            status=LotteryTicketStatus.REVEALED,
        )

        self.assertTrue(lottery_state(self.child, monday)["can_purchase"])

    def test_positive_result_is_applied_once(self):
        with patch("economy.lottery._draw_prize", return_value=75):
            ticket = purchase_lottery_ticket(child=self.child, rng=random.Random(2))

        first = reveal_lottery_ticket(ticket=ticket, child=self.child)
        second = reveal_lottery_ticket(ticket=ticket, child=self.child)
        self.child.refresh_from_db()

        self.assertEqual(first.applied_delta, 75)
        self.assertEqual(second.result_ledger_entry_id, first.result_ledger_entry_id)
        self.assertEqual(self.child.balance, 160)
        self.assertEqual(
            self.child.ledger_entries.filter(
                description="Lottery result"
            ).count(),
            1,
        )

    def test_negative_result_stops_at_credit_limit(self):
        self.child.min_balance = -20
        self.child.save(update_fields=["min_balance"])
        with patch("economy.lottery._draw_prize", return_value=-50):
            ticket = purchase_lottery_ticket(child=self.child, rng=random.Random(4))
        self.child.balance = -10
        self.child.save(update_fields=["balance"])

        revealed = reveal_lottery_ticket(ticket=ticket, child=self.child)
        self.child.refresh_from_db()

        self.assertEqual(revealed.prize_amount, -50)
        self.assertEqual(revealed.applied_delta, -10)
        self.assertEqual(self.child.balance, -20)

    def test_negative_result_never_adds_points_when_balance_is_below_floor(self):
        self.child.min_balance = -20
        self.child.save(update_fields=["min_balance"])
        with patch("economy.lottery._draw_prize", return_value=-50):
            ticket = purchase_lottery_ticket(child=self.child, rng=random.Random(4))
        self.child.balance = -25
        self.child.save(update_fields=["balance"])

        revealed = reveal_lottery_ticket(ticket=ticket, child=self.child)
        self.child.refresh_from_db()

        self.assertEqual(revealed.applied_delta, 0)
        self.assertEqual(self.child.balance, -25)

    def test_twelfth_ticket_is_a_guaranteed_jackpot_after_eleven_without_one(self):
        for index in range(11):
            LotteryTicket.objects.create(
                child=self.child,
                week_start=lottery_week_start(),
                values=_draw_board(index + 1, random.Random(index)),
                prize_amount=index + 1,
                status=LotteryTicketStatus.REVEALED,
            )

        self.assertEqual(_draw_prize(self.child, JackpotRng()), 150)


@override_settings(
    VAPID_PRIVATE_KEY="test-private-key",
    VAPID_SUBJECT="mailto:test@example.com",
)
class LotteryReminderTests(TestCase):
    def setUp(self):
        self.family = FamilySettings.load()
        self.child = ChildProfile.objects.create(
            name="Child",
            balance=50,
            theme=Theme.PANDA_PET,
            theme_selected=True,
        )
        PushSubscription.objects.create(
            child=self.child,
            endpoint="https://push.example/lottery",
            p256dh="key",
            auth="auth",
        )
        self.now = datetime(
            2026,
            7,
            30,
            18,
            0,
            tzinfo=timezone.get_current_timezone(),
        )
        self.reminder = LotteryReminder.objects.create(
            child=self.child,
            week_start=lottery_week_start(self.now.date()),
            scheduled_for=self.now - timedelta(minutes=1),
        )

    @patch("economy.push.notify_lottery_reminder")
    def test_due_eligible_reminder_is_sent_only_once(self, notify):
        first = send_due_lottery_reminders(current_time=self.now)
        second = send_due_lottery_reminders(
            current_time=self.now + timedelta(minutes=30)
        )

        self.reminder.refresh_from_db()
        self.assertEqual(first, [self.child])
        self.assertEqual(second, [])
        self.assertTrue(self.reminder.sent)
        notify.assert_called_once_with(self.child)

    @patch("economy.push.notify_lottery_reminder")
    def test_reminder_is_skipped_after_any_ticket_purchase(self, notify):
        LotteryTicket.objects.create(
            child=self.child,
            week_start=self.reminder.week_start,
            values=_draw_board(5, random.Random(1)),
            prize_amount=5,
            status=LotteryTicketStatus.REVEALED,
        )

        sent = send_due_lottery_reminders(current_time=self.now)

        self.reminder.refresh_from_db()
        self.assertEqual(sent, [])
        self.assertFalse(self.reminder.sent)
        self.assertIsNotNone(self.reminder.handled_at)
        notify.assert_not_called()

    @patch("economy.push.notify_lottery_reminder")
    def test_reminder_respects_switches_and_configured_cost(self, notify):
        self.family.lottery_ticket_cost = 60
        self.family.save(update_fields=["lottery_ticket_cost"])

        sent = send_due_lottery_reminders(current_time=self.now)

        self.assertEqual(sent, [])
        notify.assert_not_called()

    @patch("economy.push.webpush")
    def test_reminder_push_uses_theme_title_and_risk_copy(self, webpush):
        from economy.push import notify_lottery_reminder

        with override("lt"):
            notify_lottery_reminder(self.child)

        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Bambukų staigmena")
        self.assertIn("gali laimėti", payload["body"])
        self.assertIn("prarasti taškų", payload["body"])
        self.assertEqual(payload["url"], "/vaikas/mano/#prizai")


class LotteryViewTests(TestCase):
    def setUp(self):
        self.family = FamilySettings.load()
        self.child = ChildProfile.objects.create(
            name="Child",
            balance=80,
            min_balance=-100,
            theme=Theme.MAGIC_ACADEMY,
            theme_selected=True,
        )
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def test_child_dashboard_shows_themed_system_reward_and_risk(self):
        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, "Enchanted Prophecy")
        self.assertContains(response, "System reward")
        self.assertContains(response, "Buy for 15 galleons")
        self.assertContains(response, "lose up to 50 points")

    def test_dashboard_uses_configured_cost_and_limit(self):
        self.family.lottery_ticket_cost = 22
        self.family.lottery_weekly_limit = 5
        self.family.save(
            update_fields=["lottery_ticket_cost", "lottery_weekly_limit"]
        )

        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, "Buy for 22 galleons")
        self.assertContains(response, "Tickets left this week: 5 of 5.")
        self.assertContains(response, "It costs 22 earned galleons.")

    def test_disabled_lottery_is_hidden_without_an_open_ticket(self):
        self.family.lottery_enabled = False
        self.family.save(update_fields=["lottery_enabled"])

        response = self.client.get(reverse("child_dashboard"))

        self.assertNotContains(response, "Enchanted Prophecy")
        self.assertNotContains(response, 'data-lottery-card')

    def test_parent_sees_all_weekly_tickets_available_before_purchase(self):
        parent = get_user_model().objects.create_user(
            "parent-with-unused-tickets",
            password="test-password",
        )
        self.client.force_login(parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Credit limit: -100")
        self.assertContains(response, "Lottery tickets this week: 3 of 3")

    def test_all_seven_themes_have_distinct_lottery_titles(self):
        with override("en"):
            titles = {
                str(theme_text(theme, "lottery_title"))
                for theme in Theme.values
            }

        self.assertEqual(len(titles), 7)

    @patch("economy.lottery._draw_prize", return_value=33)
    def test_child_can_purchase_and_reveal_ticket(self, _draw_prize_mock):
        purchase_response = self.client.post(
            reverse("child_purchase_lottery_ticket")
        )
        ticket = LotteryTicket.objects.get(child=self.child)

        self.assertRedirects(
            purchase_response,
            f"{reverse('child_dashboard')}#prizai",
            fetch_redirect_response=False,
        )
        dashboard = self.client.get(reverse("child_dashboard"))
        self.assertContains(dashboard, "Continue scratching")
        self.assertContains(dashboard, 'data-lottery-value="33"', count=3)

        reveal_response = self.client.post(
            reverse("child_reveal_lottery_ticket", args=[ticket.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(reveal_response.status_code, 200)
        self.assertEqual(reveal_response.json()["delta"], 33)
        self.child.refresh_from_db()
        self.assertEqual(self.child.balance, 98)

    def test_parent_sees_read_only_weekly_status_and_ledger_result(self):
        parent = get_user_model().objects.create_user(
            "parent",
            password="test-password",
        )
        self.client.force_login(parent)
        with patch("economy.lottery._draw_prize", return_value=20):
            ticket = purchase_lottery_ticket(
                child=self.child,
                rng=random.Random(2),
            )
        reveal_lottery_ticket(ticket=ticket, child=self.child)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Lottery tickets this week: 2 of 3")
        self.assertContains(response, "Lottery ticket")
        self.assertContains(response, "Lottery result")
        self.assertNotContains(response, "data-lottery-value")
