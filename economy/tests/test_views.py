import re
import tempfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from economy.forms import PenaltyForm, RewardForm, TaskForm
from economy.models import (
    ChildProfile,
    FamilySettings,
    LedgerKind,
    PenaltyTemplate,
    Proposal,
    ProposalType,
    PushSubscription,
    RequestStatus,
    Reward,
    RewardRequest,
    Task,
)
from economy.services import post_ledger_entry


class LanguageSelectionTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("language-parent", password="Safe-language-pass-123!")

    def test_english_is_the_default_language(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "A shared family space")
        self.assertContains(response, '<html lang="en">', html=False)
        self.assertContains(response, "Documentation")
        self.assertContains(response, 'href="https://docs.kinkudos.app/"', html=False)
        self.assertNotContains(response, "https://docs.kinkudos.app/index.lt/")

    def test_browser_lithuanian_is_used_without_saved_preference(self):
        response = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="lt-LT,lt;q=0.9")
        self.assertContains(response, "Bendra šeimos erdvė")
        self.assertContains(response, '<html lang="lt">', html=False)
        self.assertContains(response, "Dokumentacija")
        self.assertContains(
            response,
            'href="https://docs.kinkudos.app/index.lt/"',
            html=False,
        )
        self.assertContains(response, ">🇱🇹</span>", html=False)
        self.assertNotContains(response, "🇱🇹 LT</span>", html=False)
        self.assertContains(response, 'class="language-switcher-option"', count=2, html=False)
        self.assertNotContains(response, "🇱🇹 LT", html=False)
        self.assertNotContains(response, "🇬🇧 EN", html=False)

    def test_saved_language_overrides_browser_and_persists(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("home")},
            HTTP_ACCEPT_LANGUAGE="lt",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")
        response = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="lt")
        self.assertContains(response, "A shared family space")

    def test_family_name_is_combined_with_localized_family_label(self):
        family = FamilySettings.load()
        family.family_name = "Aurora"
        family.save(update_fields=["family_name"])

        response = self.client.get(reverse("home"))
        self.assertContains(response, "Aurora family")

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "lt"
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Aurora šeima")

    def test_language_menu_is_centred_under_its_button(self):
        stylesheet = Path(settings.BASE_DIR, "static/css/app.css").read_text(
            encoding="utf-8"
        )

        rule = re.search(r"\.language-switcher-menu \{([^}]+)\}", stylesheet)

        self.assertIsNotNone(rule)
        self.assertIn("left: 50%", rule.group(1))
        self.assertIn("transform: translateX(-50%)", rule.group(1))
        self.assertNotIn("right: 0", rule.group(1))

        switcher_rule = re.search(r"\.language-switcher \{([^}]+)\}", stylesheet)

        self.assertIsNotNone(switcher_rule)
        self.assertIn("margin-top: 0", switcher_rule.group(1))

    def test_history_child_filter_listens_to_the_child_select(self):
        script = Path(settings.BASE_DIR, "static/js/app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'document.querySelector("[data-history-child-filter] select[name=history_child]")?.addEventListener("change"',
            script,
        )
        self.assertNotIn(
            'document.querySelector("[data-history-child-filter]")?.addEventListener("change"',
            script,
        )


class AccessAndWorkflowTests(TestCase):
    def setUp(self):
        # Existing workflow assertions intentionally verify the Lithuanian UI.
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "lt"
        family = FamilySettings.load()
        family.family_name = "Aurora"
        family.currency_name = "Tokenai"
        family.save(update_fields=["family_name", "currency_name"])
        self.parent_password = "Very-safe-pass-123!"
        self.parent = get_user_model().objects.create_user(
            "tevai",
            email="tevai@example.com",
            password=self.parent_password,
        )
        self.child_one = ChildProfile(name="Child One", min_balance=-100, theme_selected=True)
        self.child_one.set_pin("1234")
        self.child_one.save()
        self.child_two = ChildProfile(name="Child Two", min_balance=-100, theme_selected=True)
        self.child_two.set_pin("5678")
        self.child_two.save()
        self.task = Task.objects.create(title="Testas", reward=50)
        self.reward = Reward.objects.create(title="Ekranas", cost=100)
        post_ledger_entry(
            child=self.child_two,
            delta=999,
            kind=LedgerKind.ADJUSTMENT,
            description="Sibling private entry",
            actor=self.parent,
        )

    def login_child(self, child, pin):
        return self.client.post(
            reverse("child_select"),
            {"child_id": child.pk, "pin": pin},
            follow=True,
        )

    def test_child_pin_dialog_uses_explicit_login_label_in_both_languages(self):
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, ">Prisijungti</button>", html=False)
        self.assertNotContains(response, ">Neužbaigtas</button>", html=False)
        self.assertContains(response, ">PIN:</label>", html=False)
        self.assertNotContains(response, "4 skaitmenys", html=False)

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, ">Login</button>", html=False)
        self.assertContains(response, ">PIN:</label>", html=False)
        self.assertNotContains(response, "4 digits", html=False)

    def test_child_dashboard_does_not_expose_sibling_data(self):
        response = self.login_child(self.child_one, "1234")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Child One")
        self.assertNotContains(response, "Sibling private entry")
        self.assertNotContains(response, ">999<", html=True)

    def test_parent_manage_sections_expose_nested_hash_links(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))

        for section in ("tasks", "penalties", "rewards", "goals"):
            with self.subTest(section=section):
                self.assertContains(response, f'href="#manage-{section}"', html=False)

    def test_child_request_workflows_use_state_colored_icon_actions(self):
        response = self.login_child(self.child_one, "1234")

        self.assertContains(
            response,
            'class="decision-icon-button decision-approve workflow-card-button"',
            html=False,
        )
        self.assertContains(response, 'class="workflow-card-action"', html=False)
        self.assertContains(response, 'href="#icon-circle-check"', html=False)
        self.assertNotContains(response, ">Pateikti</button>", html=False)

    def test_parent_proposal_decisions_use_one_icon_row_and_dialogs(self):
        proposal = Proposal.objects.create(
            child=self.child_one,
            proposal_type=ProposalType.GOAL,
            title="Dviratis",
            suggested_cost=500,
        )
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(
            response,
            f'data-open-dialog="approve-proposal-{proposal.pk}"',
            html=False,
        )
        self.assertContains(
            response,
            f'data-open-dialog="reject-proposal-{proposal.pk}"',
            html=False,
        )
        self.assertContains(
            response,
            f'id="proposal-final-cost-{proposal.pk}"',
            html=False,
        )
        self.assertContains(
            response,
            'class="pending-request-row',
            html=False,
        )
        self.assertContains(response, "Dviratis")
        self.assertContains(response, "Siūlo: 500 taškų")
        self.assertNotContains(response, ">Patvirtinti</button>", html=False)
        self.assertNotContains(response, ">Atmesti</button>", html=False)

    @patch("economy.views.parent_actions.notify_proposal_decision")
    def test_proposal_decision_is_one_time_and_notifies_only_after_success(self, notify):
        proposal = Proposal.objects.create(
            child=self.child_one,
            proposal_type=ProposalType.REWARD,
            title="Cinema",
            suggested_cost=50,
        )
        self.client.force_login(self.parent)

        self.client.post(
            reverse("parent_decide_proposal", args=[proposal.pk, "approve"]),
            {"final_cost": 50},
        )
        self.client.post(
            reverse("parent_decide_proposal", args=[proposal.pk, "reject"]),
            {"reason": "Too late"},
        )

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, RequestStatus.APPROVED)
        self.assertEqual(notify.call_count, 1)
        self.assertEqual(Reward.objects.filter(title="Cinema").count(), 1)

    def test_child_dashboard_shows_only_five_latest_history_entries(self):
        for index in range(7):
            post_ledger_entry(
                child=self.child_one,
                delta=1,
                kind=LedgerKind.ADJUSTMENT,
                description=f"First child action {index}",
                actor=self.parent,
            )

        response = self.login_child(self.child_one, "1234")

        self.assertEqual(len(response.context["ledger"]), 5)
        self.assertContains(response, "First child action 6")
        self.assertNotContains(response, "First child action 0")

    def test_child_must_choose_a_world_on_first_sign_in(self):
        self.child_one.theme = "neutral"
        self.child_one.theme_selected = False
        self.child_one.save(update_fields=["theme", "theme_selected"])

        response = self.login_child(self.child_one, "1234")
        self.assertEqual(response.resolver_match.url_name, "child_theme_onboarding")
        self.assertContains(response, "Pasirink savo pasaulį")
        self.assertNotContains(response, "Neutrali")

        response = self.client.post(
            reverse("child_theme_onboarding"),
            {"theme": "magic_academy"},
            follow=True,
        )
        self.assertEqual(response.resolver_match.url_name, "child_dashboard")
        self.child_one.refresh_from_db()
        self.assertTrue(self.child_one.theme_selected)
        self.assertEqual(self.child_one.theme, "magic_academy")

    def test_unselected_child_cannot_skip_world_onboarding(self):
        self.child_one.theme_selected = False
        self.child_one.save(update_fields=["theme_selected"])
        self.login_child(self.child_one, "1234")

        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]))
        self.assertRedirects(
            response,
            reverse("child_theme_onboarding"),
            fetch_redirect_response=False,
        )
        self.assertFalse(self.child_one.task_claims.exists())

    def test_child_cannot_open_parent_dashboard(self):
        self.login_child(self.child_one, "1234")
        response = self.client.get(reverse("parent_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("parent_login"), response.url)

    def test_child_can_submit_task_but_not_duplicate(self):
        self.login_child(self.child_one, "1234")
        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]), follow=True)
        self.assertContains(response, "perduotas tėvams")
        self.assertEqual(self.child_one.task_claims.filter(status=RequestStatus.PENDING).count(), 1)
        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]), follow=True)
        self.assertContains(response, "jau laukia")
        self.assertEqual(self.child_one.task_claims.filter(status=RequestStatus.PENDING).count(), 1)

    @override_settings(VAPID_PRIVATE_KEY="configured")
    @patch("economy.push.webpush", side_effect=ValueError("push error"))
    @patch("economy.push.transaction.on_commit", side_effect=lambda func: func())
    @patch("economy.push._start_push_thread", side_effect=lambda target, args: target(*args))
    def test_saved_task_is_not_reported_as_500_when_push_fails(
        self, _start_thread, _on_commit, webpush_mock
    ):
        PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example.test/subscription",
            p256dh="test-p256dh",
            auth="test-auth",
        )
        self.login_child(self.child_one, "1234")
        response = self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "perduotas tėvams")
        self.assertEqual(self.child_one.task_claims.count(), 1)
        webpush_mock.assert_called_once()

    def test_child_cannot_cancel_sibling_reward_request(self):
        sibling_request = self.child_two.reward_requests.create(
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.login_child(self.child_one, "1234")
        response = self.client.post(
            reverse("child_cancel_reward", args=[sibling_request.pk])
        )
        self.assertEqual(response.status_code, 404)
        sibling_request.refresh_from_db()
        self.assertEqual(sibling_request.status, RequestStatus.PENDING)

    def test_child_only_sees_request_action_for_affordable_rewards(self):
        post_ledger_entry(
            child=self.child_one,
            delta=50,
            kind=LedgerKind.ADJUSTMENT,
            description="Prizų biudžetas",
            actor=self.parent,
        )
        affordable = Reward.objects.create(title="Prizas už 150", cost=150)
        too_expensive = Reward.objects.create(title="Prizas už 151", cost=151)
        response = self.login_child(self.child_one, "1234")

        rewards = {reward.pk: reward for reward in response.context["rewards"]}
        self.assertTrue(rewards[affordable.pk].is_affordable)
        self.assertFalse(rewards[too_expensive.pk].is_affordable)
        self.assertContains(
            response,
            reverse("child_request_reward", args=[affordable.pk]),
        )
        self.assertNotContains(
            response,
            reverse("child_request_reward", args=[too_expensive.pk]),
        )
        self.assertContains(response, 'title="Nepakanka taškų"', html=False)

    def test_child_cannot_post_unaffordable_reward_request(self):
        post_ledger_entry(
            child=self.child_one,
            delta=50,
            kind=LedgerKind.ADJUSTMENT,
            description="Prizų biudžetas",
            actor=self.parent,
        )
        too_expensive = Reward.objects.create(title="Per brangus", cost=151)
        self.login_child(self.child_one, "1234")

        response = self.client.post(
            reverse("child_request_reward", args=[too_expensive.pk]),
            follow=True,
        )

        self.assertContains(response, "Šiam prizui nepakanka taškų.")
        self.assertFalse(
            self.child_one.reward_requests.filter(reward=too_expensive).exists()
        )

    def test_enhanced_reward_request_returns_server_confirmed_effect(self):
        self.login_child(self.child_one, "1234")

        response = self.client.post(
            reverse("child_request_reward", args=[self.reward.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "redirect_url": reverse("child_dashboard"),
                "effect": "reward",
            },
        )
        self.assertTrue(
            self.child_one.reward_requests.filter(
                reward=self.reward,
                status=RequestStatus.PENDING,
            ).exists()
        )

    @patch("economy.views.child.notify_reward_request")
    def test_reward_request_notifies_parents(self, notify):
        self.login_child(self.child_one, "1234")

        self.client.post(reverse("child_request_reward", args=[self.reward.pk]))

        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.child_one)

    def test_parent_login_and_task_approval(self):
        response = self.client.post(
            reverse("parent_login"),
            {"username": "tevai", "password": self.parent_password},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tėvų erdvė")
        claim = self.child_one.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(reverse("parent_decide_task", args=[claim.pk, "approve"]))
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 50)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Istorija")
        self.assertNotContains(response, "Veiksmų istorija")
        self.assertContains(response, "Child One · Testas")

    @patch("economy.views.parent_actions.notify_task_decision")
    def test_task_approval_and_rejection_notify_the_affected_child(self, notify):
        self.client.login(username="tevai", password=self.parent_password)
        approved = self.child_one.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(reverse("parent_decide_task", args=[approved.pk, "approve"]))
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.child_one)
        self.assertTrue(notify.call_args.kwargs["approved"])

        notify.reset_mock()
        rejected = self.child_one.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(
            reverse("parent_decide_task", args=[rejected.pk, "reject"]),
            {"reason": "Pabandyk dar kartą."},
        )
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.child_one)
        self.assertFalse(notify.call_args.kwargs["approved"])

    @patch("economy.views.parent_actions.notify_reward_decision")
    def test_reward_approval_and_rejection_notify_the_affected_child(self, notify):
        post_ledger_entry(
            child=self.child_one,
            delta=300,
            kind=LedgerKind.ADJUSTMENT,
            description="Pradinis balansas",
            actor=self.parent,
        )
        self.client.login(username="tevai", password=self.parent_password)
        approved = RewardRequest.objects.create(
            child=self.child_one,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.client.post(reverse("parent_decide_reward", args=[approved.pk, "approve"]))
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.child_one)
        self.assertTrue(notify.call_args.kwargs["approved"])

        notify.reset_mock()
        rejected = RewardRequest.objects.create(
            child=self.child_one,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.client.post(
            reverse("parent_decide_reward", args=[rejected.pk, "reject"]),
            {"reason": "Pirmiausia atlik darbus."},
        )
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.child_one)
        self.assertFalse(notify.call_args.kwargs["approved"])

    def test_task_decision_dialog_is_fully_lithuanian(self):
        self.child_one.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Galite pridėti komentarą, kurį matys vaikas.")
        self.assertContains(response, "Komentaras (neprivalomas)")
        self.assertNotContains(response, "You may add a comment")
        self.assertNotContains(response, "Comment (optional)")

    @override_settings(
        EMAIL_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="KinKudos <app@example.com>",
        PASSWORD_RESET_TIMEOUT=3600,
    )
    def test_parent_can_reset_password_by_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "tevai@example.com"},
            follow=True,
        )
        self.assertContains(response, "Patikrinkite el. paštą")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["tevai@example.com"])
        self.assertIn("Aurora Šeima", mail.outbox[0].subject)
        self.assertIn("Aurora Šeima", mail.outbox[0].body)
        self.assertIn("galioja vieną valandą", mail.outbox[0].body)

        match = re.search(r"http://testserver(\S+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        response = self.client.get(match.group(1))
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            response.url,
            {
                "new_password1": "Visai-naujas-saugus-456!",
                "new_password2": "Visai-naujas-saugus-456!",
            },
            follow=True,
        )
        self.assertContains(response, "Slaptažodis pakeistas")
        self.parent.refresh_from_db()
        self.assertTrue(check_password("Visai-naujas-saugus-456!", self.parent.password))

    @override_settings(
        EMAIL_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_password_reset_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "nezinomas@example.com"},
            follow=True,
        )
        self.assertContains(response, "Patikrinkite el. paštą")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_ENABLED=False)
    def test_password_reset_is_hidden_when_email_is_disabled(self):
        self.assertEqual(self.client.get(reverse("password_reset")).status_code, 404)

    def test_parent_can_unlock_child_profile(self):
        self.child_one.locked_until = timezone.now() + timedelta(minutes=5)
        self.child_one.failed_pin_attempts = 3
        self.child_one.save(update_fields=["locked_until", "failed_pin_attempts"])
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_unlock_child", args=[self.child_one.pk]),
            follow=True,
        )
        self.assertContains(response, "atrakinta")
        self.child_one.refresh_from_db()
        self.assertIsNone(self.child_one.locked_until)
        self.assertEqual(self.child_one.failed_pin_attempts, 0)

    def test_parent_can_hide_catalog_item_from_child(self):
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(reverse("parent_toggle_catalog", args=["task", self.task.pk]))
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_active)
        self.client.logout()
        response = self.login_child(self.child_one, "1234")
        self.assertNotContains(response, "Testas")
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, 'href="#icon-eye-slash"', html=False)

    def test_parent_can_edit_catalog_item_and_choose_emoji(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_edit_catalog", args=["task", self.task.pk]),
            {"title": "Naujas darbas", "reward": 75, "icon": "🧹"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "atnaujinta")
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Naujas darbas")
        self.assertEqual(self.task.reward, 75)
        self.assertEqual(self.task.icon, "🧹")

    def test_catalog_edit_forms_use_localized_icon_label(self):
        PenaltyTemplate.objects.create(title="Vėlavimas", amount=-5)
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "<label>Ikona", count=3, html=False)
        self.assertNotContains(response, "<label>Emoji", html=False)

    def test_new_catalog_forms_have_no_default_icon(self):
        for form_class in (TaskForm, PenaltyForm, RewardForm):
            with self.subTest(form=form_class.__name__):
                form = form_class()
                self.assertEqual(form["icon"].value(), "")
                self.assertNotIn('value="⭐"', str(form["icon"]))

    def test_penalty_form_accepts_positive_amount_and_stores_negative(self):
        form = PenaltyForm(
            {"title": "Vėlavimas", "amount": 15, "icon": "⏰"}
        )
        self.assertTrue(form.is_valid(), form.errors)
        penalty = form.save()
        self.assertEqual(penalty.amount, -15)

    def test_catalog_forms_reject_zero_and_negative_amounts(self):
        cases = (
            (TaskForm, {"title": "Darbas", "reward": 0, "icon": "🧹"}),
            (PenaltyForm, {"title": "Nuobauda", "amount": 0, "icon": "⏰"}),
            (PenaltyForm, {"title": "Nuobauda", "amount": -5, "icon": "⏰"}),
            (RewardForm, {"title": "Prizas", "cost": 0, "icon": "🎁"}),
        )
        for form_class, data in cases:
            with self.subTest(form=form_class.__name__, data=data):
                self.assertFalse(form_class(data).is_valid())

    def test_parent_can_delete_catalog_items_without_losing_history(self):
        penalty = PenaltyTemplate.objects.create(
            title="Istorinė nuobauda",
            amount=-20,
            icon="📵",
        )
        claim = self.child_one.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        reward_request = self.child_one.reward_requests.create(
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        penalty_entry = post_ledger_entry(
            child=self.child_one,
            delta=penalty.amount,
            kind=LedgerKind.PENALTY,
            description=penalty.title,
            actor=self.parent,
            source_id=penalty.pk,
        )
        self.client.login(username="tevai", password=self.parent_password)

        for kind, item in (
            ("task", self.task),
            ("penalty", penalty),
            ("reward", self.reward),
        ):
            with self.subTest(kind=kind):
                response = self.client.post(
                    reverse("parent_delete_catalog", args=[kind, item.pk]),
                    follow=True,
                )
                self.assertContains(response, "ištrinta")
                item.refresh_from_db()
                self.assertTrue(item.is_deleted)
                self.assertFalse(item.is_active)

        self.assertTrue(type(claim).objects.filter(pk=claim.pk, task=self.task).exists())
        self.assertTrue(
            type(reward_request).objects.filter(
                pk=reward_request.pk,
                reward=self.reward,
            ).exists()
        )
        self.assertTrue(
            type(penalty_entry).objects.filter(
                pk=penalty_entry.pk,
                source_id=penalty.pk,
            ).exists()
        )

    def test_child_dashboard_uses_lithuanian_vocative(self):
        self.child_two.vocative_name = "Second child"
        self.child_two.save(update_fields=["vocative_name"])
        response = self.login_child(self.child_two, "5678")
        self.assertContains(response, "Labas, Second child!")
        self.assertContains(response, "Šiandienos darbai laukia!")
        self.assertNotContains(response, "It's great to see you")

    def test_child_dashboard_uses_personalized_english_greeting(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.login_child(self.child_one, "1234")
        self.assertContains(response, "Hello, Child One!")
        self.assertContains(response, "Ready for today's tasks?")
        self.assertNotContains(response, '<p class="eyebrow">Hello, Child One', html=False)
        self.assertNotContains(response, "It's great to see you")

    def test_child_dashboard_falls_back_when_child_name_is_unavailable(self):
        self.child_one.name = ""
        self.child_one.save(update_fields=["name"])

        for language, expected in (("en", "Hello!"), ("lt", "Labas!")):
            with self.subTest(language=language):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
                response = self.login_child(self.child_one, "1234")
                self.assertContains(response, expected)
                self.assertNotContains(response, "undefined")
                self.assertNotContains(response, "null")
                self.assertNotContains(response, "Hello, !")
                self.assertNotContains(response, "Labas, !")

    def test_child_dashboard_escapes_diacritics_and_long_names(self):
        long_name = "Ąžuolė Žvaigždžių Tyrinėtoja su Lietuviškais Diakritiniais Ženklais"
        self.child_one.name = long_name
        self.child_one.save(update_fields=["name"])
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = self.login_child(self.child_one, "1234")

        self.assertContains(response, f"Hello, {long_name}!")
        self.assertContains(response, 'class="child-greeting-supporting"', html=False)

        self.child_one.name = "<img src=x>"
        self.child_one.save(update_fields=["name"])
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "Hello, &lt;img src=x&gt;!")
        self.assertNotContains(response, "Hello, <img src=x>!")

    def test_child_dashboard_uses_one_greeting_across_all_themes(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        themes = (
            "neutral",
            "magic_academy",
            "block_world",
            "hero_hq",
            "art_studio",
            "panda_pet",
            "blockville",
        )

        for theme in themes:
            with self.subTest(theme=theme):
                self.child_one.theme = theme
                self.child_one.save(update_fields=["theme"])
                response = self.login_child(self.child_one, "1234")
                self.assertContains(response, "Hello, Child One!")
                self.assertContains(response, "Ready for today's tasks?")
                self.assertNotContains(response, "It's great to see you")

    def test_child_dashboard_greeting_layout_wraps_without_collisions(self):
        stylesheet = Path(settings.BASE_DIR, "static/css/app.css").read_text(
            encoding="utf-8"
        )

        identity_rule = re.search(r"\.child-identity \{([^}]+)\}", stylesheet)
        greeting_rule = re.search(r"\.child-greeting \{([^}]+)\}", stylesheet)
        greeting_heading_rule = re.search(
            r"\.child-greeting h1 \{([^}]+)\}", stylesheet
        )
        supporting_rule = re.search(
            r"\.child-greeting-supporting \{([^}]+)\}", stylesheet
        )
        hero_rule = re.search(r"\.child-hero \{([^}]+)\}", stylesheet)

        self.assertIsNotNone(identity_rule)
        self.assertIsNotNone(greeting_rule)
        self.assertIsNotNone(greeting_heading_rule)
        self.assertIsNotNone(supporting_rule)
        self.assertIsNotNone(hero_rule)
        self.assertIn("min-width: 0", identity_rule.group(1))
        self.assertIn("min-width: 0", greeting_rule.group(1))
        self.assertIn("overflow-wrap: anywhere", greeting_heading_rule.group(1))
        self.assertIn(
            "font-size: clamp(1.05rem, 2.2vw, 1.9rem)",
            supporting_rule.group(1),
        )
        self.assertIn("overflow-wrap: anywhere", supporting_rule.group(1))
        self.assertIn("flex-wrap: wrap", hero_rule.group(1))

    def test_magic_theme_uses_correct_owl_accusative(self):
        self.child_one.theme = "magic_academy"
        self.child_one.save(update_fields=["theme"])
        response = self.login_child(self.child_one, "1234")
        self.assertContains(response, "Siųsti pelėdą")
        self.assertNotContains(response, "Siųsti pelėda")
        self.assertContains(response, 'id="sound-toggle"', html=False)
        self.assertContains(response, 'href="#icon-volume-high"', html=False)
        self.assertContains(response, 'aria-label="Išjungti garsus"', html=False)
        self.assertNotContains(response, ">♪</button>", html=False)

    def test_child_selector_is_neutral_and_hides_themes(self):
        self.child_one.theme = "magic_academy"
        self.child_one.save(update_fields=["theme"])
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, "Prisijungti", count=3)
        self.assertContains(response, "profile-select-heading")
        self.assertNotContains(response, "Tai aš")
        self.assertNotContains(response, "Magijos akademija")
        self.assertNotContains(response, "Blokų pasaulis")
        self.assertNotContains(response, "theme-magic_academy")
        self.assertNotContains(response, "theme-block_world")

    def test_parent_dashboard_has_v060_labels_and_collapsed_catalogs(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "v26.6.7")
        self.assertContains(response, f'href="{reverse("changelog")}"', html=False)
        self.assertContains(response, "taškai")
        self.assertContains(response, "Kreditas -100")
        self.assertContains(response, 'class="push-icon"', html=False)
        self.assertContains(response, "Kaip įjungti pranešimus?")
        self.assertNotContains(response, '<details class="panel" open>', html=False)
        self.assertNotContains(response, '<details class="settings-section" open>', html=False)
        self.assertNotContains(
            response,
            "settings-section-standalone",
            html=False,
        )
        self.assertContains(response, 'class="language-switcher-option"', count=2, html=False)
        self.assertContains(response, "🇱🇹", html=False)
        self.assertContains(response, "🇬🇧", html=False)
        self.assertNotContains(response, "🇱🇹 LT", html=False)
        self.assertNotContains(response, "🇬🇧 EN", html=False)
        self.assertContains(response, "<title>Tėvų erdvė – KinKudos</title>", html=False)
        self.assertNotContains(response, "Aurora šeima")
        self.assertContains(
            response,
            'class="catalog-token catalog-token-negative">−100 taškų',
            html=False,
        )
        self.assertNotContains(
            response,
            'class="catalog-token catalog-token-positive">−100 taškų',
            html=False,
        )
        self.assertContains(response, ">Darbai<", html=False)
        self.assertContains(response, ">Nuobaudos<", html=False)
        self.assertContains(response, ">Prizai<", html=False)
        self.assertContains(response, ">Tikslai<", html=False)
        self.assertContains(response, ">Nustatymai<", html=False)
        self.assertNotContains(response, "Šeimos nustatymai")
        self.assertNotContains(response, ">Bendrieji<", html=False)
        self.assertNotContains(response, "Vaikai ir prieiga")
        self.assertContains(response, "Vaikų įrenginiai")
        self.assertContains(response, "Taškai ir darbai")
        self.assertContains(response, "Duomenys ir saugojimas")
        self.assertContains(response, "Tinklas ir saugumas")
        self.assertContains(response, "Kortelių limitas per savaitę")
        self.assertContains(
            response,
            "Limitas atnaujinamas kiekvieną pirmadienį, kiekvienam vaikui. "
            "Numatytoji reikšmė – 3.",
        )
        self.assertNotContains(response, "El. pašto nustatymai")
        self.assertContains(response, "El. paštas ir pranešimai")
        self.assertContains(response, ">Atsarginės kopijos<", html=False)
        self.assertContains(response, ">Paskyros<", html=False)
        self.assertNotContains(response, "Dabartinis jūsų tėvų paskyros slaptažodis")
        self.assertNotContains(response, '<label for="history-child">', html=False)
        self.assertContains(response, ">Išsaugoti</button>", html=False)
        self.assertNotContains(response, "Išsaugoti nustatymus")
        self.assertNotContains(response, "Išsaugoti paskyrą")
        self.assertNotContains(response, "Išsaugoti profilį")
        self.assertNotContains(response, "Tasks, penalties and rewards")
        self.assertNotContains(response, "Family accounts and application settings")
        self.assertNotContains(response, "Task photo settings")
        self.assertNotContains(response, "Save settings")
        self.assertNotContains(response, ">Reikia sprendimo<", html=False)
        self.assertNotContains(response, ">Valdymas<", html=False)
        self.assertNotContains(response, ">Prisijungimai<", html=False)
        self.assertNotContains(response, ">Žurnalas<", html=False)

        stylesheet = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")
        self.assertNotIn(".catalog-grid > details > summary::after", stylesheet)
        self.assertIn("#parent-settings details > summary::after", stylesheet)
        self.assertIn(".manage-tabs a.is-active", stylesheet)
        self.assertContains(response, "data-manage-section", html=False)

    def test_home_title_contains_family_nickname_and_project_name(self):
        response = self.client.get(reverse("home"))
        self.assertContains(
            response,
            "<title>Sveiki, Aurora – KinKudos</title>",
            html=False,
        )
        self.assertContains(response, "Atlik darbus, rink taškus ir išsirink prizą.")
        self.assertNotContains(response, "Complete tasks, earn points")
        self.assertContains(response, 'class="topbar landing-topbar"', html=False)
        self.assertContains(response, 'class="site-footer"', html=False)
        self.assertContains(response, 'class="footer-product">KinKudos · ', html=False)
        self.assertContains(response, "v26.6.7")
        self.assertContains(response, "Dokumentacija")
        self.assertContains(response, "https://docs.kinkudos.app/index.lt/")
        self.assertContains(response, "https://github.com/VooZ2/kinkudos")
        self.assertContains(response, 'href="#icon-github"', html=False)
        self.assertNotContains(response, 'class="app-version"', html=False)

    def test_public_pages_share_the_product_header(self):
        for url_name in ("parent_login", "child_select", "changelog"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(
                    response,
                    'class="topbar landing-topbar"',
                    html=False,
                )
                self.assertContains(response, 'class="brand-mark brand-logo"', html=False)
                self.assertContains(response, 'class="brand-name">KinKudos', html=False)
                self.assertContains(response, "system-page", html=False)
                self.assertNotContains(response, "Aurora šeima")
                self.assertNotContains(response, 'class="app-version"', html=False)

    @override_settings(EMAIL_ENABLED=True)
    def test_password_reset_pages_share_the_product_header(self):
        for url_name in (
            "password_reset",
            "password_reset_done",
            "password_reset_complete",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(
                    response,
                    'class="topbar landing-topbar"',
                    html=False,
                )
                self.assertContains(response, 'class="brand-mark brand-logo"', html=False)
                self.assertNotContains(response, "Aurora šeima")
                self.assertNotContains(response, 'class="app-version"', html=False)

    @override_settings(EMAIL_ENABLED=True)
    def test_auth_pages_use_the_shared_auth_design_shell(self):
        for url_name in ("parent_login", "password_reset", "password_reset_done"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(
                    response,
                    '<body class="system-page auth-page session-sensitive-page theme-neutral">',
                    html=False,
                )

    def test_session_sensitive_pages_are_not_cacheable(self):
        for url_name in ("parent_login", "child_select"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                cache_control = response["Cache-Control"]
                for directive in ("no-store", "no-cache", "must-revalidate", "private"):
                    self.assertIn(directive, cache_control)

    def test_parent_can_login_and_logout_thirty_times(self):
        csrf_client = Client(enforce_csrf_checks=True)
        for _attempt in range(30):
            csrf_client.get(reverse("parent_login"))
            csrf_token = csrf_client.cookies["csrftoken"].value
            response = csrf_client.post(
                reverse("parent_login"),
                {
                    "username": "tevai",
                    "password": self.parent_password,
                    "csrfmiddlewaretoken": csrf_token,
                },
            )
            self.assertRedirects(
                response,
                reverse("parent_dashboard"),
                fetch_redirect_response=False,
            )
            csrf_client.post(
                reverse("logout"),
                {"csrfmiddlewaretoken": csrf_client.cookies["csrftoken"].value},
            )

    def test_two_open_login_forms_work_until_authentication_rotates_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get(reverse("parent_login"))
        first_token = csrf_client.cookies["csrftoken"].value
        csrf_client.get(reverse("parent_login"))
        second_token = csrf_client.cookies["csrftoken"].value

        invalid = csrf_client.post(
            reverse("parent_login"),
            {
                "username": "tevai",
                "password": "not-the-password",
                "csrfmiddlewaretoken": first_token,
            },
        )
        self.assertEqual(invalid.status_code, 200)
        valid = csrf_client.post(
            reverse("parent_login"),
            {
                "username": "tevai",
                "password": self.parent_password,
                "csrfmiddlewaretoken": second_token,
            },
        )
        self.assertRedirects(
            valid,
            reverse("parent_dashboard"),
            fetch_redirect_response=False,
        )

    def test_login_and_theme_onboarding_include_stale_form_guards(self):
        login_response = self.client.get(reverse("parent_login"))
        self.assertContains(login_response, "data-single-submit", html=False)
        self.assertContains(login_response, "session-sensitive-page", html=False)

        self.child_one.theme_selected = False
        self.child_one.save(update_fields=["theme_selected"])
        response = self.login_child(self.child_one, "1234")
        self.assertContains(response, 'class="theme-choice-grid"', html=False)
        self.assertNotContains(response, "theme-choice-motif", html=False)
        for theme in (
            "magic_academy",
            "block_world",
            "hero_hq",
            "art_studio",
            "panda_pet",
            "blockville",
        ):
            self.assertContains(response, f"theme-choice theme-{theme}", html=False)
        self.assertNotContains(response, "<strong>🛡️", html=False)
        self.assertNotContains(response, "<strong>🎨", html=False)
        self.assertNotContains(response, "<strong>🐼", html=False)

    def test_signed_in_areas_do_not_use_the_system_page_shell(self):
        self.client.login(username="tevai", password=self.parent_password)
        parent_response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(parent_response, '<body class="parent-area">', html=False)
        self.assertContains(
            parent_response,
            'class="topbar app-topbar"',
            html=False,
        )
        self.assertContains(parent_response, 'class="brand-name">KinKudos', html=False)
        self.assertNotContains(parent_response, "system-page", html=False)

        self.client.logout()
        child_response = self.login_child(self.child_one, "1234")
        self.assertContains(child_response, "child-area", html=False)
        self.assertContains(
            child_response,
            'class="topbar app-topbar"',
            html=False,
        )
        self.assertContains(child_response, 'class="brand-name">KinKudos', html=False)
        self.assertNotContains(child_response, "system-page", html=False)

    def test_parent_information_dialogs_use_the_close_control_only(self):
        self.client.login(username="tevai", password=self.parent_password)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "How does the credit limit work?")
        self.assertContains(response, "Saved points")
        self.assertNotContains(response, "Got it")

    def test_parent_history_is_paginated_and_filterable_without_a_collapse_header(self):
        for index in range(12):
            post_ledger_entry(
                child=self.child_one,
                delta=index + 1,
                kind=LedgerKind.ADJUSTMENT,
                description=f"First child history {index}",
                actor=self.parent,
            )
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))
        self.assertEqual(len(response.context["ledger_page"]), 10)
        self.assertEqual(response.context["ledger_page"].paginator.num_pages, 2)
        self.assertContains(response, 'class="history-panel"', html=False)
        self.assertNotContains(response, 'class="history-count"', html=False)
        self.assertContains(response, 'data-history-child-filter', html=False)
        self.assertNotContains(response, 'history-meta-icon', html=False)
        self.assertContains(response, '<h1>Istorija</h1>', html=False)
        self.assertNotContains(response, "Veiklos istorija")
        self.assertNotContains(response, '<details class="history-panel"', html=False)
        self.assertContains(response, "First child history 11")
        self.assertNotContains(response, "First child history 0")

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.child_one.pk, "history_page": 2},
        )
        self.assertTrue(response.context["history_filters_active"])
        self.assertEqual(len(response.context["ledger_page"]), 2)
        self.assertContains(response, "First child history 0")
        self.assertNotContains(response, "Sibling private entry")

        response = self.client.get(
            reverse("parent_dashboard"),
            {
                "history_child": self.child_two.pk,
                "history_activity": "adjustments",
                "history_date": "any",
            },
        )
        self.assertEqual(response.context["ledger_page"].paginator.count, 1)
        self.assertContains(response, "Sibling private entry")
        self.assertNotContains(response, "First child history")
        self.assertEqual(response.context["history_activity"], "adjustments")
        self.assertEqual(response.context["history_date"], "any")

    def test_parent_history_paginates_beyond_fifty_entries_for_any_time(self):
        for index in range(52):
            post_ledger_entry(
                child=self.child_one,
                delta=index + 1,
                kind=LedgerKind.ADJUSTMENT,
                description=f"Recent history {index}",
                actor=self.parent,
            )
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.child_one.pk, "history_date": "any"},
        )

        # 52 child-one entries, no silent 50-cap; pagination keeps pages of 10.
        self.assertEqual(response.context["ledger_page"].paginator.count, 52)
        self.assertEqual(response.context["ledger_page"].paginator.num_pages, 6)
        self.assertContains(response, "Recent history 51")
        self.assertNotContains(response, "Recent history 0")

        last_page = self.client.get(
            reverse("parent_dashboard"),
            {
                "history_child": self.child_one.pk,
                "history_date": "any",
                "history_page": 6,
            },
        )
        self.assertContains(last_page, "Recent history 0")
        self.assertContains(last_page, "Recent history 1")
        self.assertNotContains(last_page, "Sibling private entry")

    def test_parent_quick_actions_use_clear_icons_and_requested_order(self):
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))
        html = response.content.decode()
        action_markers = [
            f'data-open-dialog="task-{self.child_one.pk}"',
            f'data-open-dialog="assign-tasks-{self.child_one.pk}"',
            f'data-open-dialog="child-more-{self.child_one.pk}"',
            f'data-open-dialog="custom-{self.child_one.pk}"',
            f'data-open-dialog="child-penalty-{self.child_one.pk}"',
            f'data-open-dialog="credit-{self.child_one.pk}"',
        ]

        positions = [html.index(marker) for marker in action_markers]
        self.assertEqual(positions, sorted(positions))
        quick_action_html = html[html.index('<div class="child-quick-actions"'):]
        quick_action_html = quick_action_html[:quick_action_html.index('</div>')]
        self.assertEqual(
            re.findall(r'<button class="quick-action[^"]*".*?<use href="#(icon-[^"]+)"', quick_action_html, re.S),
            [
                "icon-clipboard-check",
                "icon-calendar-plus",
                "icon-ellipsis-vertical",
            ],
        )
        self.assertIn(">Pridėti<", quick_action_html)
        self.assertIn(">Paskirti<", quick_action_html)
        self.assertIn('class="sr-only">Daugiau</span>', quick_action_html)
        more_dialog = html[html.index(f'id="child-more-{self.child_one.pk}"') :]
        more_dialog = more_dialog[: more_dialog.index("</dialog>") + len("</dialog>")]
        self.assertIn("Daugiau veiksmų", more_dialog)
        self.assertIn(f'data-open-dialog="custom-{self.child_one.pk}"', more_dialog)
        self.assertIn(f'data-open-dialog="child-penalty-{self.child_one.pk}"', more_dialog)
        self.assertIn(f'data-open-dialog="credit-{self.child_one.pk}"', more_dialog)
        self.assertIn("icon-coins", more_dialog)
        self.assertIn("icon-circle-minus", more_dialog)
        self.assertIn("icon-credit-card", more_dialog)
        self.assertIn("Koreguoti taškus", more_dialog)
        self.assertIn("Skirti nuobaudą", more_dialog)
        self.assertIn("Nustatyti kreditą", more_dialog)
        meta_row = html[html.index('<div class="child-metadata-row">') :]
        meta_row = meta_row[: meta_row.index("</div>")]
        self.assertIn("Kreditas -100", meta_row)
        self.assertLess(meta_row.index("Kreditas"), meta_row.index("Kortelės"))
        self.assertNotIn("child-meta-sep", meta_row)
        nav_html = html[html.index('<nav class="parent-navigation"'):]
        nav_html = nav_html[:nav_html.index('</nav>')]
        self.assertEqual(
            re.findall(r'<use href="#(icon-[^"]+)"', nav_html),
            ["icon-house", "icon-table-list", "icon-clock-rotate-left", "icon-gear"],
        )
        manage_html = html[html.index('<nav class="manage-tabs"'):]
        manage_html = manage_html[:manage_html.index('</nav>')]
        self.assertEqual(
            re.findall(r'<use href="#(icon-[^"]+)"', manage_html),
            ["icon-list-check", "icon-circle-minus", "icon-gift", "icon-bullseye"],
        )
        self.assertContains(response, 'id="icon-house"', html=False)
        self.assertContains(response, 'id="icon-list-check"', html=False)
        self.assertContains(response, 'fill="currentColor"', html=False)
        self.assertNotContains(response, 'icon-square-check-plus', html=False)
        self.assertNotContains(response, 'icon-coins-adjust', html=False)
        for title in (
            "Pridėti atliktą darbą",
            "Skirti nuobaudą",
            "Paskirti darbus šiandienai",
            "Koreguoti taškus",
            "Nustatyti kreditą",
        ):
            self.assertContains(response, f"<h2>{title}</h2>", html=False)

    def test_parent_history_shows_approved_and_rejected_reward_requests(self):
        approved_request = RewardRequest.objects.create(
            child=self.child_one,
            reward=self.reward,
            reward_title="Patvirtintas prizas",
            cost_snapshot=100,
        )
        rejected_request = RewardRequest.objects.create(
            child=self.child_two,
            reward=self.reward,
            reward_title="Atmestas prizas",
            cost_snapshot=100,
        )
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(
            reverse(
                "parent_decide_reward",
                args=[approved_request.pk, "approve"],
            )
        )
        self.client.post(
            reverse(
                "parent_decide_reward",
                args=[rejected_request.pk, "reject"],
            ),
            {"reason": "Pirmiausia užbaik sutartus darbus."},
        )

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.child_two.pk},
        )
        self.assertContains(response, "Atmestas prizas")
        self.assertContains(response, "Pirmiausia užbaik sutartus darbus.")
        self.assertContains(response, 'href="#icon-circle-xmark"', html=False)
        self.assertContains(response, "Atmesta")
        self.assertNotContains(response, "Patvirtintas prizas")

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.child_one.pk},
        )
        self.assertContains(response, "Patvirtintas prizas")
        self.assertContains(response, 'href="#icon-circle-check"', html=False)
        self.assertContains(response, "Patvirtinta")
        self.assertNotContains(response, "Atmestas prizas")

    def test_parent_history_shows_rejected_task_without_changing_balance(self):
        claim = self.child_two.task_claims.create(
            task=self.task,
            task_title="Atmestas darbas",
            reward_snapshot=75,
        )
        self.child_two.refresh_from_db()
        balance_before = self.child_two.balance
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "reject"]),
            {"reason": "Dar liko nesutvarkyta."},
        )

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.child_two.pk},
        )

        self.child_two.refresh_from_db()
        self.assertEqual(self.child_two.balance, balance_before)
        self.assertContains(response, "Atmestas darbas")
        self.assertContains(response, "Dar liko nesutvarkyta.")
        self.assertContains(response, 'href="#icon-circle-xmark"', html=False)
        self.assertContains(response, "Atmesta")
        self.assertEqual(response.context["ledger_page"].paginator.count, 2)

    def test_changelog_is_public_and_paginates_release_history(self):
        response = self.client.get(reverse("changelog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kas naujo?")
        self.assertContains(response, "Kas pataisyta?")
        self.assertContains(response, "v26.6.7")
        self.assertContains(response, "Dabartinė versija")
        current_release = response.context["releases"][0]
        self.assertEqual(current_release["version"], "26.6.7")
        self.assertEqual(len(response.context["releases"]), 5)
        self.assertEqual(response.context["release_page"].paginator.per_page, 5)
        current_copy = " ".join(current_release["new"] + current_release["fixed"]).lower()
        self.assertNotIn("loterij", current_copy)
        self.assertNotIn("demo", current_copy)
        next_page = self.client.get(reverse("changelog"), {"page": 2})
        self.assertEqual(next_page.status_code, 200)
        self.assertNotContains(next_page, "<h2>v26.6.7</h2>", html=False)
        self.assertContains(next_page, "Pakeitimų istorijos puslapiai")

    def test_parent_can_create_another_parent_account(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_create_parent_account"),
            {
                "username": "mama",
                "email": "mama@example.com",
                "password1": "Another-safe-pass-456!",
                "password2": "Another-safe-pass-456!",
            },
            follow=True,
        )
        self.assertContains(response, "paskyra „mama“ sukurta")
        self.assertTrue(
            get_user_model().objects.get(username="mama").check_password(
                "Another-safe-pass-456!"
            )
        )

    def test_parent_can_create_child_profile(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_create_child_account"),
            {
                "name": "Marius",
                "vocative_name": "",
                "pin": "1357",
                "confirm_pin": "1357",
                "theme": "neutral",
                "min_balance": "-50",
            },
            follow=True,
        )
        self.assertContains(response, "Vaiko profilis „Marius“ sukurtas")
        child = ChildProfile.objects.get(name="Marius")
        self.assertEqual(child.address_name, "Mariau")
        self.assertEqual(child.min_balance, -50)
        self.assertFalse(child.theme_selected)
        self.assertEqual(child.theme, "neutral")
        self.assertTrue(child.verify_pin("1357"))

    def test_parent_can_edit_parent_account_and_password(self):
        account = get_user_model().objects.create_user(
            "mama",
            email="mama@example.com",
            password="Another-safe-pass-456!",
        )
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_edit_parent_account", args=[account.pk]),
            {
                "username": "mama-nauja",
                "email": "mama-nauja@example.com",
                "new_password": "Updated-safe-pass-789!",
                "confirm_password": "Updated-safe-pass-789!",
            },
            follow=True,
        )
        self.assertContains(response, "atnaujinta")
        account.refresh_from_db()
        self.assertEqual(account.username, "mama-nauja")
        self.assertEqual(account.email, "mama-nauja@example.com")
        self.assertTrue(account.check_password("Updated-safe-pass-789!"))

    def test_parent_cannot_remove_current_account(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_remove_parent_account", args=[self.parent.pk]),
            follow=True,
        )
        self.assertContains(response, "Negalima pašalinti paskyros")
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.is_active)

    def test_parent_can_deactivate_other_parent_without_deleting_history(self):
        other = get_user_model().objects.create_user(
            "mama",
            password="Another-safe-pass-456!",
        )
        post_ledger_entry(
            child=self.child_one,
            delta=5,
            kind=LedgerKind.ADJUSTMENT,
            description="Mamos įrašas",
            actor=other,
        )
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(reverse("parent_remove_parent_account", args=[other.pk]))
        other.refresh_from_db()
        self.assertFalse(other.is_active)
        self.assertTrue(self.child_one.ledger_entries.filter(actor=other).exists())

    def test_parent_can_edit_and_deactivate_child_without_losing_history(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_edit_child_account", args=[self.child_one.pk]),
            {
                "name": "Updated Child",
                "vocative_name": "Updated Child",
                "theme": "magic_academy",
                "min_balance": "-80",
                "lottery_enabled": "on",
                "new_pin": "2468",
                "confirm_pin": "2468",
            },
            follow=True,
        )
        self.assertContains(response, "atnaujintas")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.name, "Updated Child")
        self.assertEqual(self.child_one.address_name, "Updated Child")
        self.assertEqual(self.child_one.min_balance, -80)
        self.assertTrue(self.child_one.lottery_enabled)
        self.assertTrue(self.child_one.verify_pin("2468"))
        post_ledger_entry(
            child=self.child_one,
            delta=10,
            kind=LedgerKind.ADJUSTMENT,
            description="Istorinis įrašas",
            actor=self.parent,
        )
        self.client.post(reverse("parent_remove_child_account", args=[self.child_one.pk]))
        self.child_one.refresh_from_db()
        self.assertFalse(self.child_one.is_active)
        self.assertTrue(self.child_one.ledger_entries.filter(description="Istorinis įrašas").exists())

    def test_parent_mutations_reject_deactivated_children(self):
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(reverse("parent_remove_child_account", args=[self.child_one.pk]))
        self.child_one.refresh_from_db()
        self.assertFalse(self.child_one.is_active)
        penalty = PenaltyTemplate.objects.create(
            title="Inactive child penalty",
            amount=-5,
            icon="📵",
        )
        endpoints = (
            (
                reverse("parent_adjust_balance", args=[self.child_one.pk]),
                {"amount": "1", "description": "Nope"},
            ),
            (
                reverse("parent_apply_penalty", args=[self.child_one.pk]),
                {"penalty_id": str(penalty.pk), "reason": "Nope"},
            ),
            (
                reverse("parent_set_min_balance", args=[self.child_one.pk]),
                {"min_balance": "-10"},
            ),
            (
                reverse("parent_unlock_child", args=[self.child_one.pk]),
                {},
            ),
        )
        for url, payload in endpoints:
            with self.subTest(url=url):
                response = self.client.post(url, payload)
                self.assertEqual(response.status_code, 404)

    def test_parent_can_disable_lottery_for_one_child(self):
        self.client.login(username="tevai", password=self.parent_password)

        self.client.post(
            reverse("parent_edit_child_account", args=[self.child_one.pk]),
            {
                "name": self.child_one.name,
                "vocative_name": self.child_one.vocative_name,
                "min_balance": self.child_one.min_balance,
                "new_pin": "",
                "confirm_pin": "",
            },
        )

        self.child_one.refresh_from_db()
        self.assertFalse(self.child_one.lottery_enabled)

    def test_parent_can_assign_penalty_from_catalog(self):
        penalty = PenaltyTemplate.objects.create(
            title="Ekrano nuoboda",
            amount=-20,
            icon="📵",
        )
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_penalty", args=[penalty.pk]),
            {"child_id": self.child_one.pk, "reason": "Nesilaikė susitarimo"},
            follow=True,
        )
        self.assertContains(response, "Nuobauda „Ekrano nuoboda“ skirta")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, -20)
        self.assertEqual(self.child_one.ledger_entries.first().kind, LedgerKind.PENALTY)

    def test_parent_can_award_catalog_task_from_child_card(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.child_one.pk]),
            {"task_ids": [self.task.pk]},
            follow=True,
        )
        self.assertContains(response, "darbų: 1 (iš viso +50)")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 50)

    def test_parent_can_award_multiple_tasks_from_child_card(self):
        second_task = Task.objects.create(title="Antras darbas", reward=25)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.child_one.pk]),
            {"task_ids": [self.task.pk, second_task.pk]},
            follow=True,
        )
        self.assertContains(response, "darbų: 2 (iš viso +75)")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 75)
        self.assertEqual(
            self.child_one.ledger_entries.filter(kind=LedgerKind.TASK).count(),
            2,
        )

    def test_multiple_task_awards_are_atomic(self):
        second_task = Task.objects.create(title="Antras darbas", reward=25)
        self.client.login(username="tevai", password=self.parent_password)
        call_count = 0

        def fail_on_second_entry(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("testinė antro įrašo klaida")
            return post_ledger_entry(**kwargs)

        with patch(
            "economy.views.parent_actions.post_ledger_entry",
            side_effect=fail_on_second_entry,
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("parent_award_task", args=[self.child_one.pk]),
                    {"task_ids": [self.task.pk, second_task.pk]},
                )

        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 0)
        self.assertFalse(self.child_one.ledger_entries.exists())

    def test_parent_can_assign_penalty_from_child_card(self):
        penalty = PenaltyTemplate.objects.create(title="Nuoboda", amount=-15)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_child_penalty", args=[self.child_one.pk]),
            {"penalty_ids": [penalty.pk], "reason": "Susitarimas"},
            follow=True,
        )
        self.assertContains(response, "nuobaudų: 1 (iš viso -15)")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, -15)

    def test_parent_can_assign_multiple_penalties_from_child_card(self):
        first = PenaltyTemplate.objects.create(title="Pirma", amount=-15)
        second = PenaltyTemplate.objects.create(title="Antra", amount=-10)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_child_penalty", args=[self.child_one.pk]),
            {
                "penalty_ids": [first.pk, second.pk],
                "reason": "Susitarimas",
            },
            follow=True,
        )
        self.assertContains(response, "nuobaudų: 2 (iš viso -25)")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, -25)
        entries = self.child_one.ledger_entries.filter(kind=LedgerKind.PENALTY)
        self.assertEqual(entries.count(), 2)
        self.assertTrue(
            all(entry.description.endswith(": Susitarimas") for entry in entries)
        )

    def test_parent_must_select_at_least_one_quick_action_item(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.child_one.pk]),
            {},
            follow=True,
        )
        self.assertContains(response, "Pasirink bent vieną aktyvų darbą")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 0)

    def test_parent_can_add_custom_evaluation_from_child_card(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_adjust_balance", args=[self.child_one.pk]),
            {"amount": 17, "description": "Papildoma pagalba"},
            follow=True,
        )
        self.assertContains(response, "Balansas pakoreguotas")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 17)

    def test_parent_child_card_places_saved_points_with_balance(self):
        template = Path(settings.BASE_DIR, "templates/economy/parent_dashboard.html").read_text(
            encoding="utf-8"
        )
        balance_start = template.index('<div class="child-balance-row">')
        balance_end = template.index("</div>", balance_start)
        balance_row = template[balance_start:balance_end]
        metadata_start = template.index('<div class="child-metadata-row">')

        self.assertLess(
            balance_row.index('class="stat-value'),
            balance_row.index('class="saved-total"'),
        )
        self.assertLess(balance_start, metadata_start)
        self.assertIn("credit-caption", template[metadata_start:])
        self.assertLess(
            template.index("credit-caption", metadata_start),
            template.index("child-quick-actions", metadata_start),
        )
        stylesheet = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".child-balance-row { display: flex; align-items: baseline; justify-content: flex-start;", stylesheet)
        self.assertIn(".child-metadata-row {", stylesheet)

    def test_pending_requests_are_one_shared_chronological_list(self):
        older = self.child_one.task_claims.create(
            task=self.task,
            task_title="Pirmas prašymas",
            reward_snapshot=10,
        )
        second_task = Task.objects.create(title="Antras", reward=20)
        newer = self.child_one.task_claims.create(
            task=second_task,
            task_title="Antras prašymas",
            reward_snapshot=20,
        )
        older.submitted_at = timezone.now() - timedelta(hours=1)
        older.save(update_fields=["submitted_at"])
        newer.submitted_at = timezone.now()
        newer.save(update_fields=["submitted_at"])
        RewardRequest.objects.create(
            child=self.child_two,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
            status=RequestStatus.PENDING,
        )
        self.client.login(username="tevai", password=self.parent_password)
        content = self.client.get(reverse("parent_dashboard")).content.decode()
        self.assertLess(content.index("Pirmas prašymas"), content.index("Antras prašymas"))
        self.assertIn("Laukiantys prašymai", content)
        self.assertIn('class="pending-count-badge"', content)
        self.assertRegex(content, r'class="pending-count-badge"[^>]*>\s*3\s*<')
        self.assertEqual(content.count('class="pending-requests-panel"'), 1)
        self.assertEqual(content.count('class="pending-panel-heading"'), 1)
        self.assertEqual(content.count('class="pending-request-row'), 3)
        self.assertEqual(content.count('class="pending-request-avatar"'), 3)
        self.assertNotIn("pending-child-group", content)
        self.assertEqual(content.count('class="pending-request-meta"'), 3)
        self.assertEqual(content.count('data-open-dialog="revise-task-'), 2)
        self.assertEqual(content.count('data-open-dialog="reject-reward-'), 1)
        self.assertNotIn('class="pending-request-row"><span class="item-icon"', content)
        self.assertIn("Vaikai", content)

    def test_pending_requests_panel_uses_attention_border(self):
        stylesheet = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")

        self.assertIn(
            "border: 2px solid color-mix(in srgb, var(--accent) 62%, var(--line));",
            stylesheet,
        )
        self.assertIn(
            "background: color-mix(in srgb, var(--accent) 8%, var(--surface));",
            stylesheet,
        )
        self.assertIn(".pending-panel-heading", stylesheet)
        self.assertIn(
            ".pending-request-actions { grid-column: 2; justify-content: flex-start;",
            stylesheet,
        )

    def test_pending_requests_render_english_children_heading_and_fragment(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        self.child_one.task_claims.create(
            task=self.task,
            task_title="Clean your room",
            reward_snapshot=self.task.reward,
        )
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Children")
        self.assertNotContains(response, "Kids")
        self.assertNotContains(response, "Kids info")
        self.assertContains(response, 'data-pending-requests-fragment', html=False)
        self.assertContains(response, reverse("parent_pending_state"), html=False)

        state = self.client.get(reverse("parent_pending_state"))
        self.assertEqual(state.status_code, 200)
        fragment = state.json()["html"]
        self.assertIn("data-pending-requests-fragment", fragment)
        self.assertIn('class="pending-request-row', fragment)
        self.assertNotIn("<html", fragment)

    def test_parent_dashboard_colors_positive_and_negative_balances(self):
        post_ledger_entry(
            child=self.child_one,
            delta=-10,
            kind=LedgerKind.ADJUSTMENT,
            description="Testinis minusas",
            actor=self.parent,
        )
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, 'class="stat-value balance-positive"', html=False)
        self.assertContains(response, 'class="stat-value balance-negative"', html=False)

    def test_parent_can_unsubscribe_current_push_endpoint(self):
        subscription = PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example.test/current",
            p256dh="p256dh",
            auth="auth",
        )
        other_parent = get_user_model().objects.create_user(
            "kitas",
            password="Another-safe-pass-456!",
        )
        other_subscription = PushSubscription.objects.create(
            user=other_parent,
            endpoint="https://push.example.test/other",
            p256dh="other-p256dh",
            auth="other-auth",
        )
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("push_unsubscribe"),
            data='{"endpoint":"https://push.example.test/current"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PushSubscription.objects.filter(pk=subscription.pk).exists())
        self.assertTrue(PushSubscription.objects.filter(pk=other_subscription.pk).exists())

    def test_parent_page_has_push_state_and_disable_endpoint(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Tikrinami pranešimai")
        self.assertContains(response, reverse("push_unsubscribe"))

    def test_child_can_change_own_pin(self):
        self.login_child(self.child_one, "1234")
        response = self.client.post(
            reverse("child_change_pin"),
            {
                "current_pin": "1234",
                "new_pin": "2468",
                "confirm_pin": "2468",
            },
            follow=True,
        )
        self.assertContains(response, "PIN pakeistas")
        self.child_one.refresh_from_db()
        self.assertTrue(self.child_one.verify_pin("2468"))
        self.assertFalse(self.child_one.verify_pin("1234"))

    def test_child_cannot_change_pin_without_current_pin(self):
        self.login_child(self.child_one, "1234")
        response = self.client.post(
            reverse("child_change_pin"),
            {
                "current_pin": "9999",
                "new_pin": "2468",
                "confirm_pin": "2468",
            },
            follow=True,
        )
        self.assertContains(response, "Dabartinis PIN neteisingas")
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.failed_pin_attempts, 1)
        self.assertTrue(self.child_one.verify_pin("1234"))

    def test_child_change_pin_lockout_blocks_further_attempts(self):
        self.login_child(self.child_one, "1234")
        for _ in range(5):
            response = self.client.post(
                reverse("child_change_pin"),
                {
                    "current_pin": "9999",
                    "new_pin": "2468",
                    "confirm_pin": "2468",
                },
                follow=True,
            )
            self.assertContains(response, "Dabartinis PIN neteisingas")

        self.child_one.refresh_from_db()
        self.assertTrue(self.child_one.is_locked)

        response = self.client.post(
            reverse("child_change_pin"),
            {
                "current_pin": "1234",
                "new_pin": "2468",
                "confirm_pin": "2468",
            },
            follow=True,
        )
        self.assertContains(response, "Profilis trumpam užrakintas")
        self.child_one.refresh_from_db()
        self.assertTrue(self.child_one.is_locked)
        self.assertTrue(check_password("1234", self.child_one.pin_hash))
        self.assertFalse(check_password("2468", self.child_one.pin_hash))

    def test_last_child_badge_follows_ui_language(self):
        self.client.cookies["kinkudos_last_child"] = str(self.child_one.pk)
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, "profile-card-last-badge")
        self.assertContains(response, ">Paskutinis</span>", html=False)
        self.assertNotContains(response, 'content: "Paskutinis"')

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, ">Last</span>", html=False)
        self.assertNotContains(response, ">Paskutinis</span>", html=False)

    def test_child_avatar_is_cropped_and_served_as_webp(self):
        image_bytes = BytesIO()
        Image.new("RGB", (900, 450), "#7c3aed").save(image_bytes, format="PNG")
        upload = SimpleUploadedFile(
            "avatar.png",
            image_bytes.getvalue(),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.login_child(self.child_one, "1234")
                response = self.client.post(
                    reverse("child_set_avatar"),
                    {"avatar": upload},
                    follow=True,
                )
                self.assertContains(response, "Avataras pakeistas")
                self.child_one.refresh_from_db()
                self.assertTrue(self.child_one.avatar.name.endswith(".webp"))
                with self.child_one.avatar.open("rb") as stored_avatar:
                    with Image.open(stored_avatar) as processed:
                        self.assertEqual(processed.format, "WEBP")
                        self.assertEqual(processed.size, (512, 512))
                avatar_response = self.client.get(
                    reverse("child_avatar", args=[self.child_one.pk])
                )
                self.assertEqual(avatar_response.status_code, 200)
                self.assertEqual(avatar_response["Content-Type"], "image/webp")

    def test_child_can_upload_iphone_heic_avatar(self):
        image_bytes = BytesIO()
        Image.new("RGB", (640, 960), "#be123c").save(image_bytes, format="HEIF")
        upload = SimpleUploadedFile(
            "iphone.heic",
            image_bytes.getvalue(),
            content_type="image/heic",
        )
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.login_child(self.child_one, "1234")
                response = self.client.post(
                    reverse("child_set_avatar"),
                    {"avatar": upload},
                    follow=True,
                )
                self.assertContains(response, "Avataras pakeistas")
                self.child_one.refresh_from_db()
                with self.child_one.avatar.open("rb") as stored_avatar:
                    with Image.open(stored_avatar) as processed:
                        self.assertEqual(processed.format, "WEBP")
                        self.assertEqual(processed.size, (512, 512))

    def test_child_session_uses_configured_expiry(self):
        response = self.login_child(self.child_one, "1234")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get_expiry_age(), 172800)

    def test_parent_session_uses_configured_expiry(self):
        self.client.post(
            reverse("parent_login"),
            {"username": "tevai", "password": self.parent_password},
        )
        self.assertEqual(self.client.session.get_expiry_age(), 86400)

    def test_csrf_protects_balance_changes(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.parent)
        response = csrf_client.post(
            reverse("parent_adjust_balance", args=[self.child_one.pk]),
            {"amount": 10, "description": "Be CSRF"},
        )
        self.assertEqual(response.status_code, 403)
        self.child_one.refresh_from_db()
        self.assertEqual(self.child_one.balance, 0)

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_production_session_cookie_is_secure(self):
        response = self.client.post(
            reverse("parent_login"),
            {"username": "tevai", "password": self.parent_password},
        )
        self.assertTrue(response.cookies["kinkudos_session"]["secure"])

    def test_mutating_endpoints_reject_get(self):
        self.login_child(self.child_one, "1234")
        response = self.client.get(reverse("child_submit_task", args=[self.task.pk]))
        self.assertEqual(response.status_code, 405)

    def test_manifest_and_service_worker_are_available(self):
        home = self.client.get(reverse("home"))
        self.assertContains(
            home,
            '/static/icons/favicon-32.png?v=26.6.7',
        )
        self.assertContains(home, "/static/css/app.css?v=26.6.7")
        self.assertContains(home, "/static/js/app.js?v=26.6.7")
        manifest = self.client.get(reverse("manifest"))
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()["display"], "standalone")
        self.assertEqual(manifest.json()["background_color"], "#F9FAFB")
        self.assertEqual(manifest.json()["theme_color"], "#4C1D95")
        self.assertEqual(
            manifest.json()["icons"][0]["src"],
            "/static/icons/icon-192.png?v=26.6.7",
        )
        worker = self.client.get(reverse("service_worker"))
        self.assertEqual(worker.status_code, 200)
        self.assertContains(worker, "/static/icons/icon-192.png?v=26.6.7")
        self.assertContains(worker, 'self.addEventListener("push"', html=False)
        self.assertContains(worker, 'self.addEventListener("notificationclick"', html=False)
        self.assertNotContains(worker, 'self.addEventListener("fetch"', html=False)
        self.assertNotContains(worker, "respondWith", html=False)
        self.assertEqual(worker["Service-Worker-Allowed"], "/")
        self.assertEqual(
            worker["Cache-Control"],
            "no-store, no-cache, must-revalidate",
        )
