from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from economy.forms import AdjustmentForm, ProposalForm, TaskForm
from economy.models import (
    ChildProfile,
    FamilySettings,
    GoalMode,
    LedgerKind,
    Proposal,
    ProposalType,
    SavingsGoal,
)
from economy.services import approve_proposal, post_ledger_entry

ROOT = Path(__file__).resolve().parents[2]


@override_settings(LANGUAGE_CODE="en")
class FinalReviewTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "review-parent",
            password="Safe-review-pass-123!",
        )
        self.child = ChildProfile.objects.create(
            name="Review Child",
            min_balance=-100,
            theme_selected=True,
            lottery_enabled=True,
        )
        family = FamilySettings.load()
        family.lottery_enabled = True
        family.save(update_fields=["lottery_enabled"])

    def parent_response(self, params=None):
        self.client.force_login(self.parent)
        return self.client.get(reverse("parent_dashboard"), params or {})

    def sign_in_child(self):
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def test_navigation_and_history_heading_follow_final_hierarchy(self):
        response = self.parent_response()
        content = response.content.decode()
        nav = content[content.index('<nav class="parent-navigation"') :]
        positions = [
            nav.index(f'data-parent-nav="{name}"')
            for name in ("home", "catalogs", "history", "settings")
        ]
        self.assertEqual(positions, sorted(positions))
        history = content[content.index('<section id="parent-history"') :]
        history = history[: history.index('<footer class="parent-version-footer"')]
        self.assertEqual(history.count("<h1>History</h1>"), 1)
        self.assertNotIn("Activity history", history)
        self.assertNotIn('<details class="history-panel"', history)

    def test_parent_accordions_and_settings_use_shared_compact_surface(self):
        response = self.parent_response()
        self.assertContains(response, "parent-accordion", count=14)
        self.assertContains(
            response,
            'class="settings-section settings-section-standalone parent-accordion"',
            count=6,
            html=False,
        )
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".parent-accordion:not([open]) > summary", css)
        self.assertIn("min-height: 68px", css)
        self.assertIn("min-height: 60px", css)

    def test_child_card_metadata_keeps_credit_and_ticket_controls_together(self):
        response = self.parent_response()
        content = response.content.decode()
        row = content[content.index('<div class="child-metadata-row">') :]
        row = row[: row.index("</div>")]
        self.assertIn('href="#icon-credit-card"', row)
        self.assertIn("Credit -100", row)
        self.assertIn('aria-label="About credit"', row)
        self.assertIn('href="#icon-ticket-simple"', row)
        self.assertIn("Tickets", row)
        self.assertIn('aria-label="About scratch tickets"', row)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn("justify-content: center", css)

        family = FamilySettings.load()
        family.lottery_enabled = False
        family.save(update_fields=["lottery_enabled"])
        response = self.parent_response()
        self.assertContains(response, "Credit -100")
        self.assertNotContains(response, 'class="lottery-parent-status"', html=False)

    def test_history_defaults_are_not_active_and_filtered_empty_state_can_clear(self):
        response = self.parent_response()
        self.assertEqual(response.context["history_date"], "any")
        self.assertEqual(response.context["history_filter_count"], 0)
        self.assertFalse(response.context["history_filters_active"])
        self.assertContains(response, "The activity history is empty.")
        self.assertNotContains(response, "data-clear-history-filters", html=False)

        response = self.parent_response({"history_child": self.child.pk})
        self.assertTrue(response.context["history_filters_active"])
        self.assertEqual(response.context["history_filter_count"], 1)
        self.assertContains(response, "No activity matches these filters.")
        self.assertContains(response, "data-clear-history-filters", count=1, html=False)
        self.assertContains(response, 'href="#icon-filter-circle-xmark"', html=False)

    def test_history_custom_dates_normalize_and_validate(self):
        response = self.parent_response(
            {
                "history_date": "week",
                "history_start": "2026-08-03",
                "history_end": "2026-08-04",
            }
        )
        self.assertEqual(response.context["history_date"], "custom")
        self.assertEqual(response.context["history_custom_start"], "2026-08-03")
        self.assertContains(response, 'data-history-custom-range', html=False)
        self.assertNotContains(response, 'name="history_start" value="2026-08-03" disabled', html=False)

        default_response = self.parent_response()
        self.assertContains(default_response, 'data-history-custom-range hidden', html=False)

        response = self.parent_response(
            {
                "history_date": "custom",
                "history_start": "2026-08-05",
                "history_end": "2026-08-04",
            }
        )
        self.assertContains(response, "From date must not be later than To date.")

    def test_history_actor_and_category_icons_use_event_sources(self):
        post_ledger_entry(
            child=self.child,
            delta=25,
            kind=LedgerKind.ADJUSTMENT,
            description="Manual correction",
            actor=self.parent,
        )
        response = self.parent_response()
        self.assertContains(response, "Adjusted by: review-parent")
        icon_template = (ROOT / "templates/economy/includes/history_kind_icon.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('entry.kind == "task" or entry.kind == "assigned_task"', icon_template)
        self.assertIn('href="#icon-list-check"', icon_template)
        self.assertIn('entry.kind == "reward"', icon_template)
        self.assertIn('href="#icon-hand-holding-heart"', icon_template)

    def test_goal_proposal_requires_and_preserves_saving_method(self):
        form = ProposalForm(
            {
                "proposal_type": ProposalType.GOAL,
                "title": "New bicycle",
                "suggested_cost": 500,
                "icon": "🚲",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("goal_mode", form.errors)

        form = ProposalForm(
            {
                "proposal_type": ProposalType.REWARD,
                "title": "Cinema",
                "suggested_cost": 50,
                "icon": "🎬",
            }
        )
        self.assertTrue(form.is_valid())

        proposal = Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.GOAL,
            goal_mode=GoalMode.SAVED,
            title="New bicycle",
            suggested_cost=500,
        )
        goal = approve_proposal(proposal=proposal, actor=self.parent, final_cost=550)
        self.assertIsInstance(goal, SavingsGoal)
        self.assertEqual(goal.mode, GoalMode.SAVED)

    def test_frontend_source_covers_date_goal_language_and_balance_behaviour(self):
        response = self.parent_response()
        self.assertContains(response, 'name="language" value="en" type="submit"', html=False)
        self.assertContains(response, 'name="language" value="lt" type="submit"', html=False)
        script = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
        self.assertIn("data-clear-history-filters", script)
        self.assertIn('dateSelect.value = "any"', script)
        self.assertIn('dateSelect.value = "custom"', script)
        self.assertIn("available - Math.min(amount, max)", script)
        self.assertIn('document.querySelectorAll(".language-switcher-menu")', script)
        self.assertNotIn("languageNavigationPending", script)
        self.assertNotIn("requestSubmit", script)
        self.assertNotIn('button.setAttribute("aria-disabled", "true")', script)

    def test_numeric_point_fields_have_a_five_digit_guard_and_backend_limit(self):
        response = self.parent_response()
        self.assertContains(response, 'name="custom_points" type="number" min="1" max="99999"', html=False)
        self.assertContains(response, 'name="amount" type="number" min="-99999" max="99999"', html=False)
        self.assertFalse(
            TaskForm({"title": "Long task", "reward": 100000, "icon": "🧹"}).is_valid()
        )
        self.assertFalse(
            AdjustmentForm({"amount": 100000, "description": "Too large"}).is_valid()
        )

    def test_device_actions_use_short_labels_and_dark_controls_have_contrast(self):
        response = self.parent_response()
        self.assertContains(response, "Allow on this device")
        self.assertContains(response, "Send a link")
        self.assertNotContains(response, "Allow children on this device")
        self.assertNotContains(response, "Create private pairing link")
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn("color: #d8c9ff", css)

    def test_mobile_footer_has_compact_labels_and_dynamic_version(self):
        response = self.parent_response()
        self.assertContains(response, 'class="footer-release"', html=False)
        self.assertContains(response, "v26.6.3")
        self.assertContains(response, 'class="footer-docs-short">Docs', html=False)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".footer-product, .footer-docs-long { display: none; }", css)
        self.assertIn(".child-area .app-topbar .brand-name { display: none; }", css)
