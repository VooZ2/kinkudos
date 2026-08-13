from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import get_resolver, reverse
from django.utils import timezone
from django.utils.translation import override

from economy.models import FamilySettings

CANONICAL_EXAMPLES = {
    "changelog": "/changes/",
    "submit_feedback": "/feedback/",
    "parent_login": "/login/",
    "password_reset": "/password/reset/",
    "password_reset_done": "/password/reset/sent/",
    "password_reset_confirm": "/password/new/123/abc/",
    "password_reset_complete": "/password/changed/",
    "logout": "/logout/",
    "pair_device_via_link": "/pair-device/",
    "child_select": "/child/",
    "child_dashboard": "/child/home/",
    "child_state": "/child/state/",
    "child_theme_onboarding": "/child/first-login/",
    "child_submit_task": "/child/tasks/7/submit/",
    "task_evidence": "/child/task-evidence/7/full/",
    "child_request_reward": "/child/rewards/8/request/",
    "child_purchase_lottery_ticket": "/child/lottery/purchase/",
    "child_reveal_lottery_ticket": "/child/lottery/9/reveal/",
    "child_cancel_reward": "/child/reward-requests/10/cancel/",
    "child_create_proposal": "/child/proposals/create/",
    "child_set_goal_mode": "/child/goals/11/mode/",
    "child_add_goal_points": "/child/goals/11/add-points/",
    "child_request_goal_completion": "/child/goals/11/request-completion/",
    "child_set_theme": "/child/theme/",
    "child_give_points": "/child/gifts/points/",
    "child_set_birth_date": "/child/birthday/",
    "child_change_pin": "/child/pin/",
    "child_set_avatar": "/child/avatar/",
    "parent_dashboard": "/parents/",
    "parent_pending_state": "/parents/pending-requests/state/",
    "parent_add_goal_points": "/parents/goals/11/add-points/",
    "parent_return_goal_points": "/parents/goals/11/return-points/",
    "parent_edit_goal": "/parents/goals/11/edit/",
    "parent_close_goal": "/parents/goals/11/close/",
    "parent_delete_goal": "/parents/goals/11/delete/",
    "parent_decide_goal_completion": "/parents/goal-requests/12/approve/",
    "parent_create_parent_account": "/parents/accounts/parents/new/",
    "parent_create_child_account": "/parents/accounts/children/new/",
    "parent_edit_parent_account": "/parents/accounts/parents/13/edit/",
    "parent_remove_parent_account": "/parents/accounts/parents/13/remove/",
    "parent_edit_child_account": "/parents/accounts/children/14/edit/",
    "parent_remove_child_account": "/parents/accounts/children/14/remove/",
    "parent_create_catalog": "/parents/catalog/task/",
    "parent_toggle_catalog": "/parents/catalog/task/15/toggle/",
    "parent_edit_catalog": "/parents/catalog/task/15/edit/",
    "parent_delete_catalog": "/parents/catalog/task/15/delete/",
    "parent_decide_task": "/parents/tasks/16/approve/",
    "parent_decide_reward": "/parents/rewards/17/approve/",
    "parent_decide_proposal": "/parents/proposals/18/approve/",
    "parent_decide_birth_date": "/parents/birthday-requests/19/approve/",
    "parent_adjust_balance": "/parents/children/20/balance/",
    "parent_apply_penalty": "/parents/children/20/penalty/",
    "parent_award_task": "/parents/children/20/award-task/",
    "parent_assign_tasks": "/parents/children/20/assign-tasks/",
    "parent_save_assignment_preset": "/parents/children/20/assignment-presets/save/",
    "parent_apply_assignment_preset": "/parents/assignment-presets/26/apply/",
    "parent_toggle_assignment_preset": "/parents/assignment-presets/26/toggle/",
    "parent_delete_assignment_preset": "/parents/assignment-presets/26/delete/",
    "parent_cancel_assigned_task": "/parents/assigned-tasks/21/cancel/",
    "parent_cancel_assigned_task_batch": "/parents/assigned-task-batches/22/cancel/",
    "parent_assign_child_penalty": "/parents/children/20/assign-penalty/",
    "parent_assign_penalty": "/parents/penalties/23/assign/",
    "parent_set_min_balance": "/parents/children/20/minimum-balance/",
    "parent_unlock_child": "/parents/children/20/unlock/",
    "parent_update_family_preferences": "/parents/settings/family/",
    "parent_update_network_access": "/parents/settings/network/",
    "parent_pair_device": "/parents/devices/pair/",
    "parent_generate_pairing_link": "/parents/devices/pairing-link/",
    "parent_revoke_device": "/parents/devices/24/revoke/",
    "parent_rename_device": "/parents/devices/24/rename/",
    "parent_revoke_all_devices": "/parents/devices/revoke-all/",
    "parent_configure_backup": "/parents/settings/backup/",
    "parent_backup_status": "/parents/settings/backup/status/",
    "parent_configure_smtp": "/parents/settings/email/",
    "parent_run_backup": "/parents/settings/backup/run/",
    "parent_update_feedback_status": "/parents/feedback/25/status/",
    "push_subscribe": "/push/subscribe/",
    "push_unsubscribe": "/push/unsubscribe/",
    "child_push_subscribe": "/child/push/subscribe/",
    "child_push_unsubscribe": "/child/push/unsubscribe/",
}


class CanonicalUrlTests(TestCase):
    def setUp(self):
        family = FamilySettings.load()
        family.setup_completed_at = timezone.now()
        family.save(update_fields=["setup_completed_at"])

    def test_named_urls_generate_english_canonical_paths(self):
        for name, expected in CANONICAL_EXAMPLES.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=_args_for(name)), expected)

    def test_all_named_application_routes_have_no_lithuanian_segments(self):
        old_segments = (
            "pakeitimai",
            "atsiliepimas",
            "prisijungti",
            "slaptazodis",
            "atsijungti",
            "susieti-irengini",
            "vaikas",
            "tevai",
            "darbo-irodymas",
        )
        for pattern in _iter_url_patterns(get_resolver().url_patterns):
            if pattern.name is None:
                continue
            route = str(pattern.pattern)
            with self.subTest(name=pattern.name):
                self.assertFalse(
                    any(segment in route for segment in old_segments),
                    route,
                )

    def test_english_paths_are_identical_for_both_ui_languages(self):
        for name in CANONICAL_EXAMPLES:
            with self.subTest(name=name):
                with override("en"):
                    english = reverse(name, args=_args_for(name))
                with override("lt"):
                    lithuanian = reverse(name, args=_args_for(name))
                self.assertEqual(english, lithuanian)


class LegacyUrlCompatibilityTests(TestCase):
    def setUp(self):
        family = FamilySettings.load()
        family.setup_completed_at = timezone.now()
        family.save(update_fields=["setup_completed_at"])
        get_user_model().objects.create_user(
            "legacy-login",
            password="Safe-legacy-password-123!",
        )

    def test_public_legacy_gets_permanently_redirect_to_canonical_paths(self):
        legacy_paths = {
            "/pakeitimai/": "changelog",
            "/atsiliepimas/": "submit_feedback",
            "/prisijungti/": "parent_login",
            "/slaptazodis/atkurti/": "password_reset",
            "/slaptazodis/issiusta/": "password_reset_done",
            "/slaptazodis/pakeistas/": "password_reset_complete",
            "/atsijungti/": "logout",
            "/susieti-irengini/": "pair_device_via_link",
            "/vaikas/": "child_select",
            "/vaikas/mano/": "child_dashboard",
            "/vaikas/busena/": "child_state",
            "/tevai/": "parent_dashboard",
        }
        for old_path, name in legacy_paths.items():
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], reverse(name))

    def test_legacy_get_redirect_preserves_query_string(self):
        response = self.client.get("/pakeitimai/?page=2")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/changes/?page=2")

    def test_legacy_redirect_drops_unknown_and_unsafe_query_values(self):
        cases = (
            ("/pakeitimai/?page=https://evil.example", "/changes/"),
            ("/pakeitimai/?page=//evil.example", "/changes/"),
            ("/pakeitimai/?page=%2F%2Fevil.example", "/changes/"),
            ("/pakeitimai/?page=2&next=https://evil.example", "/changes/?page=2"),
            ("/prisijungti/?next=https://evil.example", "/login/"),
            ("/prisijungti/?next=//evil.example", "/login/"),
            ("/prisijungti/?next=%2F%2Fevil.example", "/login/"),
            ("/prisijungti/?next=https%3A%2F%2Fevil.example", "/login/"),
            ("/prisijungti/?next=%2F%5C%5Cevil.example", "/login/"),
            ("/prisijungti/?next=%2F%2F%5Bevil", "/login/"),
        )
        for old_path, expected_path in cases:
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], expected_path)

    def test_legacy_login_redirect_preserves_one_safe_internal_next(self):
        response = self.client.get("/prisijungti/?next=%2Fchild%2F")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/login/?next=%2Fchild%2F")

    def test_legacy_dynamic_gets_redirect_to_dynamic_canonical_paths(self):
        cases = (
            (
                "/slaptazodis/naujas/123/abc/",
                "/password/new/123/abc/",
            ),
            (
                "/atsiliepimas/7/nuotrauka/",
                "/feedback/7/screenshot/",
            ),
        )
        for old_path, expected_path in cases:
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], expected_path)

    def test_legacy_post_keeps_method_and_body_for_login_and_logout(self):
        response = self.client.post(
            "/prisijungti/",
            {"username": "legacy-login", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 301)

        response = self.client.post("/atsijungti/", {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("home"))


def _args_for(name):
    args = {
        "password_reset_confirm": ["123", "abc"],
        "feedback_screenshot": [1],
        "child_avatar": [1],
        "child_submit_task": [7],
        "child_complete_assigned_task": [1],
        "child_resubmit_task": [1],
        "child_acknowledge_task_response": [1],
        "task_evidence": [7, "full"],
        "child_request_reward": [8],
        "child_reveal_lottery_ticket": [9],
        "child_cancel_reward": [10],
        "child_set_goal_mode": [11],
        "child_add_goal_points": [11],
        "child_request_goal_completion": [11],
        "parent_add_goal_points": [11],
        "parent_return_goal_points": [11],
        "parent_edit_goal": [11],
        "parent_close_goal": [11],
        "parent_delete_goal": [11],
        "parent_decide_goal_completion": [12, "approve"],
        "parent_edit_parent_account": [13],
        "parent_remove_parent_account": [13],
        "parent_edit_child_account": [14],
        "parent_remove_child_account": [14],
        "parent_create_catalog": ["task"],
        "parent_toggle_catalog": ["task", 15],
        "parent_edit_catalog": ["task", 15],
        "parent_delete_catalog": ["task", 15],
        "parent_decide_task": [16, "approve"],
        "parent_decide_reward": [17, "approve"],
        "parent_decide_proposal": [18, "approve"],
        "parent_decide_birth_date": [19, "approve"],
        "parent_adjust_balance": [20],
        "parent_apply_penalty": [20],
        "parent_award_task": [20],
        "parent_assign_tasks": [20],
        "parent_save_assignment_preset": [20],
        "parent_apply_assignment_preset": [26],
        "parent_toggle_assignment_preset": [26],
        "parent_delete_assignment_preset": [26],
        "parent_cancel_assigned_task": [21],
        "parent_cancel_assigned_task_batch": [22],
        "parent_assign_child_penalty": [20],
        "parent_assign_penalty": [23],
        "parent_set_min_balance": [20],
        "parent_unlock_child": [20],
        "parent_revoke_device": [24],
        "parent_rename_device": [24],
        "parent_update_feedback_status": [25],
    }
    return args.get(name, [])


def _iter_url_patterns(patterns):
    for pattern in patterns:
        if hasattr(pattern, "url_patterns"):
            yield from _iter_url_patterns(pattern.url_patterns)
        else:
            yield pattern
