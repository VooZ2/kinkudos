from io import BytesIO
import re
import tempfile
from datetime import timedelta
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from django.test import override_settings
from django.utils import timezone

from economy.forms import PenaltyForm, RewardForm, TaskForm
from economy.models import (
    ChildProfile,
    FamilySettings,
    LedgerKind,
    PenaltyTemplate,
    PushSubscription,
    RequestStatus,
    Reward,
    RewardRequest,
    Task,
)
from economy.services import post_ledger_entry


class LanguageSelectionTests(TestCase):
    def test_english_is_the_default_language(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "A shared family space")
        self.assertContains(response, '<html lang="en">', html=False)

    def test_browser_lithuanian_is_used_without_saved_preference(self):
        response = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="lt-LT,lt;q=0.9")
        self.assertContains(response, "Bendra šeimos erdvė")
        self.assertContains(response, '<html lang="lt">', html=False)

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
        self.gabija = ChildProfile(name="Gabija", min_balance=-100, theme_selected=True)
        self.gabija.set_pin("1234")
        self.gabija.save()
        self.augustas = ChildProfile(name="Augustas", min_balance=-100, theme_selected=True)
        self.augustas.set_pin("5678")
        self.augustas.save()
        self.task = Task.objects.create(title="Testas", reward=50)
        self.reward = Reward.objects.create(title="Ekranas", cost=100)
        post_ledger_entry(
            child=self.augustas,
            delta=999,
            kind=LedgerKind.ADJUSTMENT,
            description="Tik Augusto paslaptis",
            actor=self.parent,
        )

    def login_child(self, child, pin):
        return self.client.post(
            reverse("child_select"),
            {"child_id": child.pk, "pin": pin},
            follow=True,
        )

    def test_child_dashboard_does_not_expose_sibling_data(self):
        response = self.login_child(self.gabija, "1234")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gabija")
        self.assertNotContains(response, "Tik Augusto paslaptis")
        self.assertNotContains(response, ">999<", html=True)

    def test_child_must_choose_a_world_on_first_sign_in(self):
        self.gabija.theme = "neutral"
        self.gabija.theme_selected = False
        self.gabija.save(update_fields=["theme", "theme_selected"])

        response = self.login_child(self.gabija, "1234")
        self.assertEqual(response.resolver_match.url_name, "child_theme_onboarding")
        self.assertContains(response, "Pasirink savo pasaulį")
        self.assertNotContains(response, "Neutrali")

        response = self.client.post(
            reverse("child_theme_onboarding"),
            {"theme": "magic_academy"},
            follow=True,
        )
        self.assertEqual(response.resolver_match.url_name, "child_dashboard")
        self.gabija.refresh_from_db()
        self.assertTrue(self.gabija.theme_selected)
        self.assertEqual(self.gabija.theme, "magic_academy")

    def test_unselected_child_cannot_skip_world_onboarding(self):
        self.gabija.theme_selected = False
        self.gabija.save(update_fields=["theme_selected"])
        self.login_child(self.gabija, "1234")

        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]))
        self.assertRedirects(
            response,
            reverse("child_theme_onboarding"),
            fetch_redirect_response=False,
        )
        self.assertFalse(self.gabija.task_claims.exists())

    def test_child_cannot_open_parent_dashboard(self):
        self.login_child(self.gabija, "1234")
        response = self.client.get(reverse("parent_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("parent_login"), response.url)

    def test_child_can_submit_task_but_not_duplicate(self):
        self.login_child(self.gabija, "1234")
        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]), follow=True)
        self.assertContains(response, "perduotas tėvams")
        self.assertEqual(self.gabija.task_claims.filter(status=RequestStatus.PENDING).count(), 1)
        response = self.client.post(reverse("child_submit_task", args=[self.task.pk]), follow=True)
        self.assertContains(response, "jau laukia")
        self.assertEqual(self.gabija.task_claims.filter(status=RequestStatus.PENDING).count(), 1)

    @override_settings(VAPID_PRIVATE_KEY="configured")
    @patch("economy.push.webpush", side_effect=ValueError("push error"))
    def test_saved_task_is_not_reported_as_500_when_push_fails(self, webpush_mock):
        PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example.test/subscription",
            p256dh="test-p256dh",
            auth="test-auth",
        )
        self.login_child(self.gabija, "1234")
        response = self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "perduotas tėvams")
        self.assertEqual(self.gabija.task_claims.count(), 1)
        webpush_mock.assert_called_once()

    def test_child_cannot_cancel_sibling_reward_request(self):
        sibling_request = self.augustas.reward_requests.create(
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.login_child(self.gabija, "1234")
        response = self.client.post(
            reverse("child_cancel_reward", args=[sibling_request.pk])
        )
        self.assertEqual(response.status_code, 404)
        sibling_request.refresh_from_db()
        self.assertEqual(sibling_request.status, RequestStatus.PENDING)

    def test_child_only_sees_request_action_for_affordable_rewards(self):
        post_ledger_entry(
            child=self.gabija,
            delta=50,
            kind=LedgerKind.ADJUSTMENT,
            description="Prizų biudžetas",
            actor=self.parent,
        )
        affordable = Reward.objects.create(title="Prizas už 150", cost=150)
        too_expensive = Reward.objects.create(title="Prizas už 151", cost=151)
        response = self.login_child(self.gabija, "1234")

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
            child=self.gabija,
            delta=50,
            kind=LedgerKind.ADJUSTMENT,
            description="Prizų biudžetas",
            actor=self.parent,
        )
        too_expensive = Reward.objects.create(title="Per brangus", cost=151)
        self.login_child(self.gabija, "1234")

        response = self.client.post(
            reverse("child_request_reward", args=[too_expensive.pk]),
            follow=True,
        )

        self.assertContains(response, "Šiam prizui nepakanka taškų.")
        self.assertFalse(
            self.gabija.reward_requests.filter(reward=too_expensive).exists()
        )

    def test_enhanced_reward_request_returns_server_confirmed_effect(self):
        self.login_child(self.gabija, "1234")

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
            self.gabija.reward_requests.filter(
                reward=self.reward,
                status=RequestStatus.PENDING,
            ).exists()
        )

    def test_parent_login_and_task_approval(self):
        response = self.client.post(
            reverse("parent_login"),
            {"username": "tevai", "password": self.parent_password},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tėvų erdvė")
        claim = self.gabija.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(reverse("parent_decide_task", args=[claim.pk, "approve"]))
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 50)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Veiksmų istorija")
        self.assertContains(response, "Gabija · Testas")

    @patch("economy.views.notify_task_decision")
    def test_task_approval_and_rejection_notify_the_affected_child(self, notify):
        self.client.login(username="tevai", password=self.parent_password)
        approved = self.gabija.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(reverse("parent_decide_task", args=[approved.pk, "approve"]))
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.gabija)
        self.assertTrue(notify.call_args.kwargs["approved"])

        notify.reset_mock()
        rejected = self.gabija.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        self.client.post(
            reverse("parent_decide_task", args=[rejected.pk, "reject"]),
            {"reason": "Pabandyk dar kartą."},
        )
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.gabija)
        self.assertFalse(notify.call_args.kwargs["approved"])

    @patch("economy.views.notify_reward_decision")
    def test_reward_approval_and_rejection_notify_the_affected_child(self, notify):
        post_ledger_entry(
            child=self.gabija,
            delta=300,
            kind=LedgerKind.ADJUSTMENT,
            description="Pradinis balansas",
            actor=self.parent,
        )
        self.client.login(username="tevai", password=self.parent_password)
        approved = RewardRequest.objects.create(
            child=self.gabija,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.client.post(reverse("parent_decide_reward", args=[approved.pk, "approve"]))
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.gabija)
        self.assertTrue(notify.call_args.kwargs["approved"])

        notify.reset_mock()
        rejected = RewardRequest.objects.create(
            child=self.gabija,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.client.post(
            reverse("parent_decide_reward", args=[rejected.pk, "reject"]),
            {"reason": "Pirmiausia atlik darbus."},
        )
        notify.assert_called_once()
        self.assertEqual(notify.call_args.args[0].child, self.gabija)
        self.assertFalse(notify.call_args.kwargs["approved"])

    def test_task_decision_dialog_is_fully_lithuanian(self):
        self.gabija.task_claims.create(
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
        self.gabija.locked_until = timezone.now() + timedelta(minutes=5)
        self.gabija.failed_pin_attempts = 3
        self.gabija.save(update_fields=["locked_until", "failed_pin_attempts"])
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_unlock_child", args=[self.gabija.pk]),
            follow=True,
        )
        self.assertContains(response, "atrakinta")
        self.gabija.refresh_from_db()
        self.assertIsNone(self.gabija.locked_until)
        self.assertEqual(self.gabija.failed_pin_attempts, 0)

    def test_parent_can_hide_catalog_item_from_child(self):
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(reverse("parent_toggle_catalog", args=["task", self.task.pk]))
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_active)
        self.client.logout()
        response = self.login_child(self.gabija, "1234")
        self.assertNotContains(response, "Testas")

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
        claim = self.gabija.task_claims.create(
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
        )
        reward_request = self.gabija.reward_requests.create(
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        penalty_entry = post_ledger_entry(
            child=self.gabija,
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
        response = self.login_child(self.augustas, "5678")
        self.assertContains(response, "Labas, Augustai")

    def test_magic_theme_uses_correct_owl_accusative(self):
        self.gabija.theme = "magic_academy"
        self.gabija.save(update_fields=["theme"])
        response = self.login_child(self.gabija, "1234")
        self.assertContains(response, "Siųsti pelėdą")
        self.assertNotContains(response, "Siųsti pelėda")
        self.assertContains(response, 'id="sound-toggle"', html=False)
        self.assertContains(response, 'href="#icon-sound-on"', html=False)
        self.assertContains(response, 'aria-label="Išjungti garsus"', html=False)
        self.assertNotContains(response, ">♪</button>", html=False)

    def test_child_selector_is_neutral_and_hides_themes(self):
        self.gabija.theme = "magic_academy"
        self.gabija.save(update_fields=["theme"])
        response = self.client.get(reverse("child_select"))
        self.assertContains(response, "Prisijungti", count=2)
        self.assertContains(response, "profile-select-heading")
        self.assertNotContains(response, "Tai aš")
        self.assertNotContains(response, "Magijos akademija")
        self.assertNotContains(response, "Blokų pasaulis")
        self.assertNotContains(response, "theme-magic_academy")
        self.assertNotContains(response, "theme-block_world")

    def test_parent_dashboard_has_v060_labels_and_collapsed_catalogs(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "v0.12.2 BETA")
        self.assertContains(response, 'href="/pakeitimai/"', html=False)
        self.assertContains(response, "TAŠKAI")
        self.assertContains(response, "Kredito limitas -100")
        self.assertContains(response, 'class="push-icon"', html=False)
        self.assertContains(response, "Kaip įjungti pranešimus?")
        self.assertNotContains(response, '<details class="panel" open>', html=False)
        self.assertContains(response, "🇱🇹 LT")
        self.assertContains(response, "🇬🇧 EN")
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
        self.assertContains(response, "Darbai, nuobaudos ir prizai")
        self.assertContains(response, ">Nustatymai<", html=False)
        self.assertContains(response, "Projekto nustatymai")
        self.assertContains(response, "Išsaugoti nustatymus")
        self.assertNotContains(response, "Tasks, penalties and rewards")
        self.assertNotContains(response, "Family accounts and application settings")
        self.assertNotContains(response, "Task photo settings")
        self.assertNotContains(response, "Save settings")
        self.assertNotContains(response, ">Reikia sprendimo<", html=False)
        self.assertNotContains(response, ">Valdymas<", html=False)
        self.assertNotContains(response, ">Prisijungimai<", html=False)
        self.assertNotContains(response, ">Žurnalas<", html=False)

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
        self.assertContains(response, "KinKudos · v0.12.2 BETA")
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

    def test_parent_history_is_collapsed_paginated_and_filterable(self):
        for index in range(12):
            post_ledger_entry(
                child=self.gabija,
                delta=index + 1,
                kind=LedgerKind.ADJUSTMENT,
                description=f"Gabijos istorija {index}",
                actor=self.parent,
            )
        self.client.login(username="tevai", password=self.parent_password)

        response = self.client.get(reverse("parent_dashboard"))
        self.assertEqual(len(response.context["ledger_page"]), 10)
        self.assertEqual(response.context["ledger_page"].paginator.num_pages, 2)
        self.assertContains(response, 'class="history-panel"', html=False)
        self.assertNotContains(response, 'class="history-panel" open', html=False)
        self.assertContains(response, "Gabijos istorija 11")
        self.assertNotContains(response, "Gabijos istorija 0")

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.gabija.pk, "history_page": 2},
        )
        self.assertTrue(response.context["history_is_open"])
        self.assertEqual(len(response.context["ledger_page"]), 2)
        self.assertContains(response, "Gabijos istorija 0")
        self.assertNotContains(response, "Tik Augusto paslaptis")

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.augustas.pk},
        )
        self.assertEqual(response.context["ledger_page"].paginator.count, 1)
        self.assertContains(response, "Tik Augusto paslaptis")
        self.assertNotContains(response, "Gabijos istorija")

    def test_parent_history_shows_approved_and_rejected_reward_requests(self):
        approved_request = RewardRequest.objects.create(
            child=self.gabija,
            reward=self.reward,
            reward_title="Patvirtintas prizas",
            cost_snapshot=100,
        )
        rejected_request = RewardRequest.objects.create(
            child=self.augustas,
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
            {"history_child": self.augustas.pk},
        )
        self.assertContains(response, "Atmestas prizas")
        self.assertContains(response, "Pirmiausia užbaik sutartus darbus.")
        self.assertContains(response, 'href="#icon-stop"', html=False)
        self.assertContains(response, "Atmesta")
        self.assertNotContains(response, "Patvirtintas prizas")

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.gabija.pk},
        )
        self.assertContains(response, "Patvirtintas prizas")
        self.assertContains(response, 'href="#icon-check-circle"', html=False)
        self.assertContains(response, "Patvirtinta")
        self.assertNotContains(response, "Atmestas prizas")

    def test_parent_history_shows_rejected_task_without_changing_balance(self):
        claim = self.augustas.task_claims.create(
            task=self.task,
            task_title="Atmestas darbas",
            reward_snapshot=75,
        )
        self.augustas.refresh_from_db()
        balance_before = self.augustas.balance
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "reject"]),
            {"reason": "Dar liko nesutvarkyta."},
        )

        response = self.client.get(
            reverse("parent_dashboard"),
            {"history_child": self.augustas.pk},
        )

        self.augustas.refresh_from_db()
        self.assertEqual(self.augustas.balance, balance_before)
        self.assertContains(response, "Atmestas darbas")
        self.assertContains(response, "Dar liko nesutvarkyta.")
        self.assertContains(response, 'href="#icon-stop"', html=False)
        self.assertContains(response, "Atmesta")
        self.assertEqual(response.context["ledger_page"].paginator.count, 2)

    def test_changelog_is_public_and_contains_full_release_history(self):
        response = self.client.get(reverse("changelog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kas naujo?")
        self.assertContains(response, "Kas pataisyta?")
        self.assertContains(response, "v0.12.2 BETA")
        self.assertContains(response, "v0.10.4 BETA")
        self.assertContains(response, "v0.10.1 BETA")
        self.assertContains(response, "v0.10.0 BETA")
        self.assertContains(response, "v0.1.0")
        self.assertContains(response, "Dabartinė versija")
        self.assertContains(
            response,
            "„Safari“ perjungiant tėvų erdvės skyrius puslapis lieka viršuje",
        )
        self.assertContains(
            response,
            "Tėvų nustatymų puslapyje naudojama trumpa antraštė",
        )

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
            child=self.gabija,
            delta=5,
            kind=LedgerKind.ADJUSTMENT,
            description="Mamos įrašas",
            actor=other,
        )
        self.client.login(username="tevai", password=self.parent_password)
        self.client.post(reverse("parent_remove_parent_account", args=[other.pk]))
        other.refresh_from_db()
        self.assertFalse(other.is_active)
        self.assertTrue(self.gabija.ledger_entries.filter(actor=other).exists())

    def test_parent_can_edit_and_deactivate_child_without_losing_history(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_edit_child_account", args=[self.gabija.pk]),
            {
                "name": "Gabrielė",
                "vocative_name": "Gabriele",
                "theme": "magic_academy",
                "min_balance": "-80",
                "new_pin": "2468",
                "confirm_pin": "2468",
            },
            follow=True,
        )
        self.assertContains(response, "atnaujintas")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.name, "Gabrielė")
        self.assertEqual(self.gabija.address_name, "Gabriele")
        self.assertEqual(self.gabija.min_balance, -80)
        self.assertTrue(self.gabija.verify_pin("2468"))
        post_ledger_entry(
            child=self.gabija,
            delta=10,
            kind=LedgerKind.ADJUSTMENT,
            description="Istorinis įrašas",
            actor=self.parent,
        )
        self.client.post(reverse("parent_remove_child_account", args=[self.gabija.pk]))
        self.gabija.refresh_from_db()
        self.assertFalse(self.gabija.is_active)
        self.assertTrue(self.gabija.ledger_entries.filter(description="Istorinis įrašas").exists())

    def test_parent_can_assign_penalty_from_catalog(self):
        penalty = PenaltyTemplate.objects.create(
            title="Ekrano nuoboda",
            amount=-20,
            icon="📵",
        )
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_penalty", args=[penalty.pk]),
            {"child_id": self.gabija.pk, "reason": "Nesilaikė susitarimo"},
            follow=True,
        )
        self.assertContains(response, "Nuobauda „Ekrano nuoboda“ skirta")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, -20)
        self.assertEqual(self.gabija.ledger_entries.first().kind, LedgerKind.PENALTY)

    def test_parent_can_award_catalog_task_from_child_card(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.gabija.pk]),
            {"task_ids": [self.task.pk]},
            follow=True,
        )
        self.assertContains(response, "darbų: 1 (iš viso +50)")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 50)

    def test_parent_can_award_multiple_tasks_from_child_card(self):
        second_task = Task.objects.create(title="Antras darbas", reward=25)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.gabija.pk]),
            {"task_ids": [self.task.pk, second_task.pk]},
            follow=True,
        )
        self.assertContains(response, "darbų: 2 (iš viso +75)")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 75)
        self.assertEqual(
            self.gabija.ledger_entries.filter(kind=LedgerKind.TASK).count(),
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
            "economy.views.post_ledger_entry",
            side_effect=fail_on_second_entry,
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("parent_award_task", args=[self.gabija.pk]),
                    {"task_ids": [self.task.pk, second_task.pk]},
                )

        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 0)
        self.assertFalse(self.gabija.ledger_entries.exists())

    def test_parent_can_assign_penalty_from_child_card(self):
        penalty = PenaltyTemplate.objects.create(title="Nuoboda", amount=-15)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_child_penalty", args=[self.gabija.pk]),
            {"penalty_ids": [penalty.pk], "reason": "Susitarimas"},
            follow=True,
        )
        self.assertContains(response, "nuobaudų: 1 (iš viso -15)")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, -15)

    def test_parent_can_assign_multiple_penalties_from_child_card(self):
        first = PenaltyTemplate.objects.create(title="Pirma", amount=-15)
        second = PenaltyTemplate.objects.create(title="Antra", amount=-10)
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_assign_child_penalty", args=[self.gabija.pk]),
            {
                "penalty_ids": [first.pk, second.pk],
                "reason": "Susitarimas",
            },
            follow=True,
        )
        self.assertContains(response, "nuobaudų: 2 (iš viso -25)")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, -25)
        entries = self.gabija.ledger_entries.filter(kind=LedgerKind.PENALTY)
        self.assertEqual(entries.count(), 2)
        self.assertTrue(
            all(entry.description.endswith(": Susitarimas") for entry in entries)
        )

    def test_parent_must_select_at_least_one_quick_action_item(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_award_task", args=[self.gabija.pk]),
            {},
            follow=True,
        )
        self.assertContains(response, "Pasirink bent vieną aktyvų darbą")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 0)

    def test_parent_can_add_custom_evaluation_from_child_card(self):
        self.client.login(username="tevai", password=self.parent_password)
        response = self.client.post(
            reverse("parent_adjust_balance", args=[self.gabija.pk]),
            {"amount": 17, "description": "Papildoma pagalba"},
            follow=True,
        )
        self.assertContains(response, "Balansas pakoreguotas")
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 17)

    def test_pending_requests_are_grouped_and_oldest_first(self):
        older = self.gabija.task_claims.create(
            task=self.task,
            task_title="Pirmas prašymas",
            reward_snapshot=10,
        )
        second_task = Task.objects.create(title="Antras", reward=20)
        newer = self.gabija.task_claims.create(
            task=second_task,
            task_title="Antras prašymas",
            reward_snapshot=20,
        )
        older.submitted_at = timezone.now() - timedelta(hours=1)
        older.save(update_fields=["submitted_at"])
        newer.submitted_at = timezone.now()
        newer.save(update_fields=["submitted_at"])
        self.client.login(username="tevai", password=self.parent_password)
        content = self.client.get(reverse("parent_dashboard")).content.decode()
        self.assertLess(content.index("Pirmas prašymas"), content.index("Antras prašymas"))
        self.assertIn("Laukiantys prašymai (2)", content)

    def test_parent_dashboard_colors_positive_and_negative_balances(self):
        post_ledger_entry(
            child=self.gabija,
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
        self.login_child(self.gabija, "1234")
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
        self.gabija.refresh_from_db()
        self.assertTrue(self.gabija.verify_pin("2468"))
        self.assertFalse(self.gabija.verify_pin("1234"))

    def test_child_cannot_change_pin_without_current_pin(self):
        self.login_child(self.gabija, "1234")
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
        self.gabija.refresh_from_db()
        self.assertTrue(self.gabija.verify_pin("1234"))

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
                self.login_child(self.gabija, "1234")
                response = self.client.post(
                    reverse("child_set_avatar"),
                    {"avatar": upload},
                    follow=True,
                )
                self.assertContains(response, "Avataras pakeistas")
                self.gabija.refresh_from_db()
                self.assertTrue(self.gabija.avatar.name.endswith(".webp"))
                with self.gabija.avatar.open("rb") as stored_avatar:
                    with Image.open(stored_avatar) as processed:
                        self.assertEqual(processed.format, "WEBP")
                        self.assertEqual(processed.size, (512, 512))
                avatar_response = self.client.get(
                    reverse("child_avatar", args=[self.gabija.pk])
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
                self.login_child(self.gabija, "1234")
                response = self.client.post(
                    reverse("child_set_avatar"),
                    {"avatar": upload},
                    follow=True,
                )
                self.assertContains(response, "Avataras pakeistas")
                self.gabija.refresh_from_db()
                with self.gabija.avatar.open("rb") as stored_avatar:
                    with Image.open(stored_avatar) as processed:
                        self.assertEqual(processed.format, "WEBP")
                        self.assertEqual(processed.size, (512, 512))

    def test_child_session_uses_configured_expiry(self):
        response = self.login_child(self.gabija, "1234")
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
            reverse("parent_adjust_balance", args=[self.gabija.pk]),
            {"amount": 10, "description": "Be CSRF"},
        )
        self.assertEqual(response.status_code, 403)
        self.gabija.refresh_from_db()
        self.assertEqual(self.gabija.balance, 0)

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_production_session_cookie_is_secure(self):
        response = self.client.post(
            reverse("parent_login"),
            {"username": "tevai", "password": self.parent_password},
        )
        self.assertTrue(response.cookies["kinkudos_session"]["secure"])

    def test_mutating_endpoints_reject_get(self):
        self.login_child(self.gabija, "1234")
        response = self.client.get(reverse("child_submit_task", args=[self.task.pk]))
        self.assertEqual(response.status_code, 405)

    def test_manifest_and_service_worker_are_available(self):
        home = self.client.get(reverse("home"))
        self.assertContains(
            home,
            '/static/icons/favicon-32.png?v=0.12.2',
        )
        self.assertContains(home, "/static/css/app.css?v=0.12.2")
        self.assertContains(home, "/static/js/app.js?v=0.12.2")
        manifest = self.client.get(reverse("manifest"))
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()["display"], "standalone")
        self.assertEqual(manifest.json()["background_color"], "#FAF8F5")
        self.assertEqual(manifest.json()["theme_color"], "#5B3E96")
        self.assertEqual(
            manifest.json()["icons"][0]["src"],
            "/static/icons/icon-192.png?v=0.12.2",
        )
        worker = self.client.get(reverse("service_worker"))
        self.assertEqual(worker.status_code, 200)
        self.assertContains(worker, "/static/icons/icon-192.png?v=0.12.2")
        self.assertContains(worker, 'kinkudos-app-shell-0.12.2')
        self.assertEqual(worker["Service-Worker-Allowed"], "/")
