from datetime import date
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    ChildProfile,
    RequestStatus,
    Reward,
    RewardRequest,
    Task,
    TaskClaim,
    Theme,
)
from economy.services import randomize_daily_themes


@override_settings(LANGUAGE_CODE="en")
class ChildExperienceTests(TestCase):
    def setUp(self):
        self.child = ChildProfile.objects.create(
            name="Child Two",
            theme_selected=True,
        )
        self.other_child = ChildProfile.objects.create(
            name="Other child",
            theme_selected=True,
        )
        self.task = Task.objects.create(
            title="Gautas geras įvertinimas arba pagyrimas",
            reward=10,
            icon="📚",
        )
        self.claim = TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
            status=RequestStatus.REJECTED,
            rejection_reason="testas",
            decided_at=timezone.now(),
        )

    def sign_in_child(self, child=None):
        session = self.client.session
        session["child_id"] = (child or self.child).pk
        session.save()

    def test_rejected_task_has_clear_lithuanian_response(self):
        self.sign_in_child()
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "lt"
        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, "Tėvų atsakymas")
        self.assertContains(response, "Darbas atmestas")
        self.assertContains(response, self.task.title)
        self.assertContains(response, "Komentaras")
        self.assertContains(response, "testas")
        self.assertContains(response, "Supratau")

    def test_child_can_acknowledge_response_without_deleting_history(self):
        self.sign_in_child()
        response = self.client.post(
            reverse("child_acknowledge_task_response", args=[self.claim.pk])
        )
        self.assertRedirects(response, reverse("child_dashboard"))

        self.claim.refresh_from_db()
        self.assertIsNotNone(self.claim.child_acknowledged_at)
        self.assertEqual(self.claim.status, RequestStatus.REJECTED)
        self.assertTrue(TaskClaim.objects.filter(pk=self.claim.pk).exists())

        response = self.client.get(reverse("child_dashboard"))
        self.assertNotContains(response, 'class="task-response-card', html=False)

    def test_child_cannot_acknowledge_another_child_response(self):
        self.sign_in_child(self.other_child)
        response = self.client.post(
            reverse("child_acknowledge_task_response", args=[self.claim.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.claim.refresh_from_db()
        self.assertIsNone(self.claim.child_acknowledged_at)

    def test_rejected_task_and_reward_history_use_catalog_icons(self):
        reward = Reward.objects.create(title="Filmas", cost=20, icon="🎬")
        RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
            status=RequestStatus.REJECTED,
            decided_at=timezone.now(),
        )
        self.sign_in_child()

        response = self.client.get(reverse("child_dashboard"))
        content = response.content.decode()

        self.assertRegex(content, r'class="ledger-icon">\s*📚\s*</span>')
        self.assertRegex(content, r'class="ledger-icon">\s*🎬\s*</span>')
        self.assertNotRegex(content, r'class="ledger-icon">\s*[TR]\s*</span>')

    def test_theme_and_avatar_forms_share_settings_accordion(self):
        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        content = response.content.decode()

        self.assertEqual(content.count("data-child-settings-accordion"), 1)
        self.assertEqual(content.count("data-settings-panel="), 4)
        self.assertContains(response, 'id="nustatymai"')
        self.assertContains(response, 'id="gimtadienis"')
        self.assertContains(response, 'id="pinas"')
        self.assertContains(response, "theme-daily")
        self.assertContains(response, 'data-pin-pad')
        self.assertContains(response, 'class="pin-pad-back"', html=False)
        self.assertRegex(content, r'data-pin-key="back"[^>]*>\s*<svg class="action-icon"[^>]*>\s*<use href="#icon-circle-xmark">')
        self.assertNotContains(response, "⌫")
        self.assertContains(response, reverse("child_set_theme"))
        self.assertContains(response, reverse("child_set_avatar"))

    def test_child_can_enable_daily_random_theme(self):
        self.sign_in_child()
        response = self.client.post(
            reverse("child_set_theme"),
            {
                "theme": Theme.MAGIC_ACADEMY,
                "randomize_theme_daily": "on",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('child_dashboard')}#nustatymai",
            fetch_redirect_response=False,
        )
        self.child.refresh_from_db()
        self.assertEqual(self.child.theme, Theme.MAGIC_ACADEMY)
        self.assertTrue(self.child.randomize_theme_daily)

    def test_daily_random_theme_changes_once_and_never_repeats_current_theme(self):
        self.child.theme = Theme.MAGIC_ACADEMY
        self.child.randomize_theme_daily = True
        self.child.save(update_fields=["theme", "randomize_theme_daily"])
        current_date = date(2026, 7, 29)

        changed = randomize_daily_themes(
            current_date=current_date,
            chooser=lambda choices: choices[0],
        )
        first_theme = changed[0].theme
        changed_again = randomize_daily_themes(
            current_date=current_date,
            chooser=lambda choices: choices[0],
        )

        self.child.refresh_from_db()
        self.assertNotEqual(first_theme, Theme.MAGIC_ACADEMY)
        self.assertEqual(self.child.theme, first_theme)
        self.assertEqual(self.child.theme_randomized_on, current_date)
        self.assertEqual(changed_again, [])

    def test_daily_random_theme_ignores_children_who_did_not_enable_it(self):
        original_theme = self.child.theme

        changed = randomize_daily_themes(
            current_date=date(2026, 7, 29),
            chooser=lambda choices: choices[0],
        )

        self.child.refresh_from_db()
        self.assertEqual(changed, [])
        self.assertEqual(self.child.theme, original_theme)
        self.assertIsNone(self.child.theme_randomized_on)

    def test_waiting_for_parents_strip_hidden_when_empty(self):
        self.claim.child_acknowledged_at = timezone.now()
        self.claim.save(update_fields=["child_acknowledged_at"])
        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertNotContains(response, "waiting-parents-strip", html=False)

    def test_waiting_for_parents_strip_shows_chips_with_targets(self):
        self.claim.child_acknowledged_at = timezone.now()
        self.claim.save(update_fields=["child_acknowledged_at"])
        pending_task = Task.objects.create(title="Wash dishes", reward=8, icon="🍽️")
        TaskClaim.objects.create(
            child=self.child,
            task=pending_task,
            task_title=pending_task.title,
            reward_snapshot=pending_task.reward,
            status=RequestStatus.PENDING,
        )
        reward = Reward.objects.create(title="Ice cream", cost=15, icon="🍦")
        RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
            status=RequestStatus.PENDING,
        )
        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "waiting-parents-strip", html=False)
        self.assertContains(response, "Waiting for parents")
        self.assertContains(response, f'href="#task-card-{pending_task.pk}"', html=False)
        self.assertContains(response, f'href="#reward-card-{reward.pk}"', html=False)
        self.assertContains(response, "Wash dishes")
        self.assertContains(response, "Ice cream")

    def test_waiting_for_parents_strip_skips_inactive_catalog_targets(self):
        self.claim.child_acknowledged_at = timezone.now()
        self.claim.save(update_fields=["child_acknowledged_at"])
        pending_task = Task.objects.create(title="Wash dishes", reward=8, icon="🍽️")
        TaskClaim.objects.create(
            child=self.child,
            task=pending_task,
            task_title=pending_task.title,
            reward_snapshot=pending_task.reward,
            status=RequestStatus.PENDING,
        )
        reward = Reward.objects.create(title="Ice cream", cost=15, icon="🍦")
        RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
            status=RequestStatus.PENDING,
        )
        pending_task.is_active = False
        pending_task.save(update_fields=["is_active"])
        reward.is_deleted = True
        reward.save(update_fields=["is_deleted"])

        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertNotContains(response, "waiting-parents-strip", html=False)
        self.assertNotContains(
            response,
            f'href="#task-card-{pending_task.pk}"',
            html=False,
        )
        self.assertNotContains(
            response,
            f'href="#reward-card-{reward.pk}"',
            html=False,
        )

    def test_dashboard_tabbar_sticks_to_viewport_top(self):
        stylesheet = Path(__file__).resolve().parents[2] / "static" / "css" / "app.css"
        css = stylesheet.read_text(encoding="utf-8")
        self.assertIn(
            ".tabbar { display: flex; gap: 6px; overflow-x: auto; position: sticky; top: calc(10px + env(safe-area-inset-top, 0px));",
            css,
        )
        self.assertNotIn("position: sticky; top: 82px;", css)
        self.assertIn(".item-card .amount { flex: 0 0 auto; white-space: nowrap; }", css)

    def test_dashboard_assigned_task_stacks_title_above_points(self):
        stylesheet = Path(__file__).resolve().parents[2] / "static" / "css" / "app.css"
        css = stylesheet.read_text(encoding="utf-8")
        self.assertIn(
            ".assigned-task-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: start;",
            css,
        )
        self.assertIn(".assigned-task-row > div { display: grid; gap: 2px; min-width: 0; }", css)
        self.assertIn(".assigned-task-row h3 { min-width: 0; overflow-wrap: break-word; }", css)
        self.assertIn(".assigned-task-row .amount { white-space: nowrap; }", css)
        self.assertNotIn(
            ".assigned-task-row .amount { grid-column: 2; grid-row: 1; white-space: nowrap; }",
            css,
        )
        self.assertNotIn(".assigned-task-row h3 { grid-column: 1; grid-row: 1; min-width: 0; overflow-wrap: anywhere; }", css)

    def test_dashboard_item_card_keeps_readable_title_beside_points(self):
        stylesheet = Path(__file__).resolve().parents[2] / "static" / "css" / "app.css"
        css = stylesheet.read_text(encoding="utf-8")
        self.assertIn(
            ".item-grid { grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); }",
            css,
        )
        self.assertIn(
            ".item-card h3 { margin: 0; flex: 1 1 8ch; min-width: 8ch; overflow-wrap: break-word; }",
            css,
        )
        self.assertNotIn(".item-card h3 { margin: 0; overflow-wrap: anywhere; }", css)
        self.assertIn(
            ".item-card > div { display: flex; flex-wrap: wrap; align-items: baseline;",
            css,
        )
        self.assertIn(
            ".item-card > button,\n.item-card > form.workflow-card-action { grid-column: 1 / -1; justify-self: end; }",
            css,
        )
