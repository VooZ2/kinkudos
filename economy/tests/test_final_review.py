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
    Task,
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
        content = response.content.decode()
        self.assertContains(response, "parent-accordion", count=11)
        self.assertContains(response, 'class="settings-section parent-accordion"', count=11, html=False)
        self.assertNotContains(
            response,
            "settings-section-standalone",
            html=False,
        )
        self.assertContains(response, 'id="settings-everyday-heading"', html=False)
        self.assertContains(response, 'id="settings-people-heading"', html=False)
        self.assertContains(response, 'id="settings-server-heading"', html=False)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".parent-accordion:not([open]) > summary", css)
        self.assertIn("min-height: 68px", css)
        self.assertIn("min-height: 60px", css)
        self.assertIn(".settings-block-heading", css)
        self.assertNotIn("position: sticky; bottom: 0", css.split(".settings-save-actions")[1].split("}")[0])
        self.assertIn("Manage the family name and default language.", content)
        self.assertIn("Protect the family database and uploaded photos.", content)
        self.assertIn("settings-add-divider", content)
        people = content[content.index('id="settings-people-heading"') : content.index('id="settings-server-heading"')]
        self.assertNotIn("settings-description", people)

    def test_manage_uses_tabbed_sections_with_edit_and_hidden_states(self):
        Task.objects.create(title="Review chore", reward=10, icon="🧹", is_active=False)
        response = self.parent_response()
        content = response.content.decode()
        manage = content[content.index('id="parent-catalogs"') :]
        manage = manage[: manage.index('id="parent-settings"')]
        self.assertIn('class="manage-tabs"', manage)
        self.assertIn("data-manage-section", manage)
        self.assertNotIn("parent-accordion", manage)
        self.assertIn("catalog-edit-actions", manage)
        self.assertIn("data-cancel-edit", manage)
        self.assertIn("catalog-delete-action", manage)
        self.assertIn("catalog-row is-inactive", manage)
        self.assertIn("Hidden", manage)
        self.assertIn("manage-empty", manage)
        self.assertNotIn(
            "Children can propose goals from their area. Approved goals appear here.",
            manage,
        )
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".manage-tabs a.is-active", css)
        self.assertIn(".catalog-row.is-inactive", css)
        self.assertIn(".manage-empty", css)
        self.assertIn("text-align: left", css.split(".manage-empty {")[1].split("}")[0])
        self.assertIn("min-height: 44px", css.split(".manage-tabs a {")[1].split("}")[0])
        self.assertIn(".catalog-edit-actions", css)
        js = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
        self.assertIn("[data-manage-section]", js)
        self.assertIn("data-cancel-edit", js)
        self.assertIn("closeCatalogEdit", js)

    def test_empty_states_share_the_left_aligned_spacing_and_copy(self):
        child_template = (ROOT / "templates/economy/child_dashboard.html").read_text(
            encoding="utf-8"
        )
        select_template = (ROOT / "templates/economy/child_select.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('class="empty-state">{% translate "The rewards catalog is empty." %}', child_template)
        self.assertIn('class="empty-state">{% translate "No child profiles have been created yet." %}', select_template)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        empty_start = css.index("\n.empty-state {") + 1
        empty_css = css[empty_start : css.index("}", empty_start)]
        self.assertIn("padding: 18px", empty_css)
        self.assertIn("line-height: 1.4", empty_css)
        self.assertIn("text-align: left", empty_css)

    def test_mobile_feedback_summary_is_compact_and_left_aligned(self):
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        mobile_feedback = css[css.index(".feedback-summary {", css.index("@media (max-width: 720px)")) :]
        mobile_feedback = mobile_feedback[: mobile_feedback.index(".feedback-actions {", mobile_feedback.index(".feedback-summary {"))]
        self.assertIn("display: grid", mobile_feedback)
        self.assertIn("padding: 14px 16px", mobile_feedback)
        self.assertIn("text-align: left", mobile_feedback)

    def test_notice_blocks_tabs_and_requested_action_icons_share_patterns(self):
        response = self.parent_response()
        content = response.content.decode()
        template = (ROOT / "templates/economy/parent_dashboard.html").read_text(encoding="utf-8")
        child_template = (ROOT / "templates/economy/child_dashboard.html").read_text(encoding="utf-8")
        setup_template = (ROOT / "templates/economy/setup_complete.html").read_text(encoding="utf-8")
        self.assertIn("notice-block notice-danger", template)
        self.assertIn("notice-block notice-warning", template)
        self.assertIn("notice-block notice-warning", child_template)
        self.assertIn("notice-block notice-info", child_template)
        self.assertIn('href="#icon-copy"', template)
        self.assertIn('href="#icon-trash"', template)
        self.assertIn('href="#icon-filter"', template)
        self.assertNotIn('button-with-icon', template)
        self.assertNotIn('href="#icon-user-plus"', template)
        self.assertIn('>{% translate "Create invite" %}</button>', template)
        self.assertIn('>{% translate "Create invite link" %}</button>', template)
        self.assertIn("notice-block", content)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".notice-block.notice-info", css)
        self.assertIn(".notice-block.notice-warning", css)
        self.assertIn(".notice-block.notice-danger", css)
        pending_css = css[css.index(".pending-empty-state") : css.index(".empty-panel")]
        self.assertIn("color: var(--success)", pending_css)
        self.assertIn(".pending-empty-state .action-icon", pending_css)
        self.assertIn(".required-marker-star", css)
        self.assertIn(".required-marker-colon", css)
        self.assertIn(".stack-form p > label.required-label-decorated::after", css)
        self.assertIn(".settings-summary-description", css)
        self.assertIn(".settings-add-divider", css)
        self.assertIn(".tabbar.is-scrollable:not(.is-at-start)", css)
        self.assertIn(".recovery-code-row", css)
        self.assertIn(".account-create-form { grid-template-columns: repeat(2, minmax(0, 1fr));", css)
        self.assertIn(".child-hero.has-avatar .balance-orb", css)
        self.assertNotIn("--viewport-bottom-offset", css)
        self.assertIn('data-copy-from="recovery-code-value"', setup_template)
        self.assertIn("setup-open-parent", setup_template)
        js = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
        self.assertIn("syncHorizontalTabbar", js)
        self.assertIn("revealActiveTab", js)
        self.assertIn("scrollIntoView", js)
        self.assertIn("decorateRequiredLabels", js)
        self.assertIn("data-copy-from", setup_template)

    def test_child_card_metadata_keeps_credit_and_ticket_controls_together(self):
        response = self.parent_response()
        content = response.content.decode()
        row = content[content.index('<div class="child-metadata-row">') :]
        row = row[: row.index("</div>")]
        self.assertIn('href="#icon-credit-card"', row)
        self.assertIn("Credit -100", row)
        self.assertIn('aria-label="About credit"', row)
        self.assertIn('href="#icon-ticket-simple"', row)
        self.assertIn("Cards", row)
        self.assertIn('aria-label="About surprise cards"', row)
        self.assertIn("meta-info-button", row)
        self.assertNotIn("child-meta-sep", row)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".meta-info-button", css)

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

    def test_history_mobile_polish_styles_align_actions_and_touch_targets(self):
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".history-filter-chips button { min-height: 44px;", css)
        self.assertIn(".history-row-actions > .amount { margin-left: auto; }", css)
        self.assertIn(
            ".history-decision-informational .history-decision-label { position: absolute;",
            css,
        )
        self.assertIn("border-radius: 24px 24px 0 0;", css)
        self.assertIn("inset: auto 0 0;", css)
        self.assertIn(".history-filter-dialog .dialog-actions", css)
        self.assertIn("position: sticky;", css)
        self.assertIn(".history-photo-button", css)
        template = (ROOT / "templates/economy/parent_dashboard.html").read_text(encoding="utf-8")
        self.assertIn('class="history-decision-label"', template)
        self.assertIn('aria-label="{% translate \'Informational\' %}"', template)

    def test_choice_fieldset_radios_use_inline_option_cards(self):
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn('.stack-form input[type="radio"]', css)
        self.assertIn(".choice-fieldset > label {", css)
        self.assertIn("display: flex;", css)
        self.assertIn(".choice-fieldset > label:has(input:checked)", css)

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

    def test_safari_mobile_first_tap_reaches_settings_and_dialogs(self):
        response = self.parent_response()
        self.assertContains(
            response,
            'name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content"',
            html=False,
        )
        self.assertContains(response, "r=responsive-controls", html=False)

        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn("--safe-area-bottom: env(safe-area-inset-bottom, 0px);", css)
        self.assertNotIn("--viewport-bottom-offset", css)
        self.assertNotIn(
            "@media (display-mode: browser) and (hover: none) and (pointer: coarse)",
            css,
        )
        self.assertNotIn(
            "--browser-bottom-gap",
            css,
        )
        self.assertIn("@media (hover: none)", css)
        self.assertIn("touch-action: manipulation", css)
        self.assertIn("inset: auto 0 0;", css)
        self.assertIn(
            "padding: 7px 0 calc(7px + var(--safe-area-bottom))",
            css,
        )
        self.assertIn(
            "padding: 22px 18px calc(16px + var(--safe-area-bottom))",
            css,
        )
        self.assertIn(
            "--fab-inset-block: calc(88px + var(--safe-area-bottom));",
            css,
        )

        js = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
        self.assertNotIn("function bindPrimaryTap(", js)
        self.assertIn('document.addEventListener("click", event => {', js)
        self.assertIn(
            'const closeButton = event.target.closest?.("[data-close-dialog]");',
            js,
        )
        self.assertIn(
            'links.forEach(link => link.addEventListener("click", event => {',
            js,
        )

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
        self.assertContains(response, "v26.8.1")
        self.assertContains(response, 'class="footer-docs-short">Docs', html=False)
        css = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".footer-product, .footer-docs-long { display: none; }", css)
        self.assertIn(".child-area .app-topbar .brand-name { display: none; }", css)
