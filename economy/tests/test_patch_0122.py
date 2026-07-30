from datetime import date

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
class Patch0122ParentResponseTests(TestCase):
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

    def test_theme_and_avatar_forms_share_one_appearance_panel(self):
        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        content = response.content.decode()

        self.assertEqual(content.count("data-profile-appearance-panel"), 1)
        self.assertEqual(content.count('class="profile-setting-part"'), 2)
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

        self.assertRedirects(response, reverse("child_dashboard"))
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
