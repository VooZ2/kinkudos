from functools import wraps

from django.http import HttpResponsePermanentRedirect
from django.urls import path, reverse

from .views import (
    ParentLoginView,
    ParentPasswordResetCompleteView,
    ParentPasswordResetConfirmView,
    ParentPasswordResetDoneView,
    ParentPasswordResetView,
    changelog,
    child_acknowledge_task_response,
    child_add_goal_points,
    child_avatar,
    child_cancel_reward,
    child_change_pin,
    child_complete_assigned_task,
    child_create_proposal,
    child_dashboard,
    child_give_points,
    child_purchase_lottery_ticket,
    child_push_subscribe,
    child_push_unsubscribe,
    child_request_goal_completion,
    child_request_reward,
    child_resubmit_task,
    child_reveal_lottery_ticket,
    child_select,
    child_set_avatar,
    child_set_birth_date,
    child_set_goal_mode,
    child_set_theme,
    child_state,
    child_submit_task,
    child_theme_onboarding,
    feedback_screenshot,
    health,
    home,
    manifest,
    pair_device_via_link,
    parent_add_goal_points,
    parent_adjust_balance,
    parent_apply_penalty,
    parent_assign_child_penalty,
    parent_assign_penalty,
    parent_assign_tasks,
    parent_award_task,
    parent_cancel_assigned_task,
    parent_cancel_assigned_task_batch,
    parent_close_goal,
    parent_configure_backup,
    parent_configure_smtp,
    parent_create_catalog,
    parent_create_child_account,
    parent_create_parent_account,
    parent_dashboard,
    parent_decide_birth_date,
    parent_decide_goal_completion,
    parent_decide_proposal,
    parent_decide_reward,
    parent_decide_task,
    parent_delete_catalog,
    parent_delete_goal,
    parent_edit_catalog,
    parent_edit_child_account,
    parent_edit_goal,
    parent_edit_parent_account,
    parent_generate_pairing_link,
    parent_pair_device,
    parent_pending_state,
    parent_remove_child_account,
    parent_remove_parent_account,
    parent_rename_device,
    parent_return_goal_points,
    parent_revoke_all_devices,
    parent_revoke_device,
    parent_run_backup,
    parent_set_min_balance,
    parent_toggle_catalog,
    parent_unlock_child,
    parent_update_family_preferences,
    parent_update_feedback_status,
    parent_update_network_access,
    push_subscribe,
    push_unsubscribe,
    service_worker,
    session_logout,
    setup,
    submit_feedback,
    task_evidence,
)


def _legacy_route(view, url_name):
    """Redirect legacy GETs while preserving mutating request semantics."""

    @wraps(view)
    def route(request, *args, **kwargs):
        if request.method in {"GET", "HEAD"}:
            destination = reverse(url_name, args=args, kwargs=kwargs)
            query_string = request.META.get("QUERY_STRING")
            if query_string:
                destination = f"{destination}?{query_string}"
            return HttpResponsePermanentRedirect(destination)
        return view(request, *args, **kwargs)

    return route

urlpatterns = [
    path("", home, name="home"),
    path("setup/", setup, name="setup"),
    path("changes/", changelog, name="changelog"),
    path("health/", health, name="health"),
    path("manifest.webmanifest", manifest, name="manifest"),
    path("service-worker.js", service_worker, name="service_worker"),
    path("feedback/", submit_feedback, name="submit_feedback"),
    path(
        "feedback/<int:report_id>/screenshot/",
        feedback_screenshot,
        name="feedback_screenshot",
    ),
    path("login/", ParentLoginView.as_view(), name="parent_login"),
    path(
        "password/reset/",
        ParentPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password/reset/sent/",
        ParentPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password/new/<uidb64>/<token>/",
        ParentPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/changed/",
        ParentPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("logout/", session_logout, name="logout"),
    path(
        "pair-device/",
        pair_device_via_link,
        name="pair_device_via_link",
    ),
    path("child/", child_select, name="child_select"),
    path("child/home/", child_dashboard, name="child_dashboard"),
    path("child/state/", child_state, name="child_state"),
    path(
        "child/first-login/",
        child_theme_onboarding,
        name="child_theme_onboarding",
    ),
    path("child/avatar/<int:child_id>/", child_avatar, name="child_avatar"),
    path("child/tasks/<int:task_id>/submit/", child_submit_task, name="child_submit_task"),
    path(
        "child/assigned-tasks/<int:assigned_task_id>/complete/",
        child_complete_assigned_task,
        name="child_complete_assigned_task",
    ),
    path(
        "child/task-requests/<int:claim_id>/resubmit/",
        child_resubmit_task,
        name="child_resubmit_task",
    ),
    path(
        "child/task-requests/<int:claim_id>/acknowledge/",
        child_acknowledge_task_response,
        name="child_acknowledge_task_response",
    ),
    path(
        "child/task-evidence/<int:claim_id>/<str:size>/",
        task_evidence,
        name="task_evidence",
    ),
    path(
        "child/rewards/<int:reward_id>/request/",
        child_request_reward,
        name="child_request_reward",
    ),
    path(
        "child/lottery/purchase/",
        child_purchase_lottery_ticket,
        name="child_purchase_lottery_ticket",
    ),
    path(
        "child/lottery/<int:ticket_id>/reveal/",
        child_reveal_lottery_ticket,
        name="child_reveal_lottery_ticket",
    ),
    path(
        "child/reward-requests/<int:request_id>/cancel/",
        child_cancel_reward,
        name="child_cancel_reward",
    ),
    path("child/proposals/create/", child_create_proposal, name="child_create_proposal"),
    path(
        "child/goals/<int:goal_id>/mode/",
        child_set_goal_mode,
        name="child_set_goal_mode",
    ),
    path(
        "child/goals/<int:goal_id>/add-points/",
        child_add_goal_points,
        name="child_add_goal_points",
    ),
    path(
        "child/goals/<int:goal_id>/request-completion/",
        child_request_goal_completion,
        name="child_request_goal_completion",
    ),
    path("child/theme/", child_set_theme, name="child_set_theme"),
    path("child/gifts/points/", child_give_points, name="child_give_points"),
    path("child/birthday/", child_set_birth_date, name="child_set_birth_date"),
    path("child/pin/", child_change_pin, name="child_change_pin"),
    path("child/avatar/", child_set_avatar, name="child_set_avatar"),
    path("parents/", parent_dashboard, name="parent_dashboard"),
    path(
        "parents/pending-requests/state/",
        parent_pending_state,
        name="parent_pending_state",
    ),
    path(
        "parents/goals/<int:goal_id>/add-points/",
        parent_add_goal_points,
        name="parent_add_goal_points",
    ),
    path(
        "parents/goals/<int:goal_id>/return-points/",
        parent_return_goal_points,
        name="parent_return_goal_points",
    ),
    path(
        "parents/goals/<int:goal_id>/edit/",
        parent_edit_goal,
        name="parent_edit_goal",
    ),
    path(
        "parents/goals/<int:goal_id>/close/",
        parent_close_goal,
        name="parent_close_goal",
    ),
    path(
        "parents/goals/<int:goal_id>/delete/",
        parent_delete_goal,
        name="parent_delete_goal",
    ),
    path(
        "parents/goal-requests/<int:request_id>/<str:decision>/",
        parent_decide_goal_completion,
        name="parent_decide_goal_completion",
    ),
    path(
        "parents/accounts/parents/new/",
        parent_create_parent_account,
        name="parent_create_parent_account",
    ),
    path(
        "parents/accounts/children/new/",
        parent_create_child_account,
        name="parent_create_child_account",
    ),
    path(
        "parents/accounts/parents/<int:account_id>/edit/",
        parent_edit_parent_account,
        name="parent_edit_parent_account",
    ),
    path(
        "parents/accounts/parents/<int:account_id>/remove/",
        parent_remove_parent_account,
        name="parent_remove_parent_account",
    ),
    path(
        "parents/accounts/children/<int:child_id>/edit/",
        parent_edit_child_account,
        name="parent_edit_child_account",
    ),
    path(
        "parents/accounts/children/<int:child_id>/remove/",
        parent_remove_child_account,
        name="parent_remove_child_account",
    ),
    path(
        "parents/catalog/<str:kind>/",
        parent_create_catalog,
        name="parent_create_catalog",
    ),
    path(
        "parents/catalog/<str:kind>/<int:item_id>/toggle/",
        parent_toggle_catalog,
        name="parent_toggle_catalog",
    ),
    path(
        "parents/catalog/<str:kind>/<int:item_id>/edit/",
        parent_edit_catalog,
        name="parent_edit_catalog",
    ),
    path(
        "parents/catalog/<str:kind>/<int:item_id>/delete/",
        parent_delete_catalog,
        name="parent_delete_catalog",
    ),
    path(
        "parents/tasks/<int:claim_id>/<str:decision>/",
        parent_decide_task,
        name="parent_decide_task",
    ),
    path(
        "parents/rewards/<int:request_id>/<str:decision>/",
        parent_decide_reward,
        name="parent_decide_reward",
    ),
    path(
        "parents/proposals/<int:proposal_id>/<str:decision>/",
        parent_decide_proposal,
        name="parent_decide_proposal",
    ),
    path(
        "parents/birthday-requests/<int:request_id>/<str:decision>/",
        parent_decide_birth_date,
        name="parent_decide_birth_date",
    ),
    path(
        "parents/children/<int:child_id>/balance/",
        parent_adjust_balance,
        name="parent_adjust_balance",
    ),
    path(
        "parents/children/<int:child_id>/penalty/",
        parent_apply_penalty,
        name="parent_apply_penalty",
    ),
    path(
        "parents/children/<int:child_id>/award-task/",
        parent_award_task,
        name="parent_award_task",
    ),
    path(
        "parents/children/<int:child_id>/assign-tasks/",
        parent_assign_tasks,
        name="parent_assign_tasks",
    ),
    path(
        "parents/assigned-tasks/<int:assigned_task_id>/cancel/",
        parent_cancel_assigned_task,
        name="parent_cancel_assigned_task",
    ),
    path(
        "parents/assigned-task-batches/<int:batch_id>/cancel/",
        parent_cancel_assigned_task_batch,
        name="parent_cancel_assigned_task_batch",
    ),
    path(
        "parents/children/<int:child_id>/assign-penalty/",
        parent_assign_child_penalty,
        name="parent_assign_child_penalty",
    ),
    path(
        "parents/penalties/<int:penalty_id>/assign/",
        parent_assign_penalty,
        name="parent_assign_penalty",
    ),
    path(
        "parents/children/<int:child_id>/minimum-balance/",
        parent_set_min_balance,
        name="parent_set_min_balance",
    ),
    path(
        "parents/children/<int:child_id>/unlock/",
        parent_unlock_child,
        name="parent_unlock_child",
    ),
    path(
        "parents/settings/family/",
        parent_update_family_preferences,
        name="parent_update_family_preferences",
    ),
    path(
        "parents/settings/network/",
        parent_update_network_access,
        name="parent_update_network_access",
    ),
    path(
        "parents/devices/pair/",
        parent_pair_device,
        name="parent_pair_device",
    ),
    path(
        "parents/devices/pairing-link/",
        parent_generate_pairing_link,
        name="parent_generate_pairing_link",
    ),
    path(
        "parents/devices/<int:device_id>/revoke/",
        parent_revoke_device,
        name="parent_revoke_device",
    ),
    path(
        "parents/devices/<int:device_id>/rename/",
        parent_rename_device,
        name="parent_rename_device",
    ),
    path(
        "parents/devices/revoke-all/",
        parent_revoke_all_devices,
        name="parent_revoke_all_devices",
    ),
    path(
        "parents/settings/backup/",
        parent_configure_backup,
        name="parent_configure_backup",
    ),
    path(
        "parents/settings/email/",
        parent_configure_smtp,
        name="parent_configure_smtp",
    ),
    path(
        "parents/settings/backup/run/",
        parent_run_backup,
        name="parent_run_backup",
    ),
    path(
        "parents/feedback/<int:report_id>/status/",
        parent_update_feedback_status,
        name="parent_update_feedback_status",
    ),
    path("push/subscribe/", push_subscribe, name="push_subscribe"),
    path("push/unsubscribe/", push_unsubscribe, name="push_unsubscribe"),
    path("child/push/subscribe/", child_push_subscribe, name="child_push_subscribe"),
    path("child/push/unsubscribe/", child_push_unsubscribe, name="child_push_unsubscribe"),
]


# Legacy aliases intentionally have no URL names, so reverse() only emits the
# English canonical routes above. GET and HEAD requests receive a permanent
# redirect; other methods are handled by the original view without changing
# their method or request body.
urlpatterns += [
    path("pakeitimai/", _legacy_route(changelog, "changelog")),
    path("atsiliepimas/", _legacy_route(submit_feedback, "submit_feedback")),
    path(
        "atsiliepimas/<int:report_id>/nuotrauka/",
        _legacy_route(feedback_screenshot, "feedback_screenshot"),
    ),
    path("prisijungti/", _legacy_route(ParentLoginView.as_view(), "parent_login")),
    path(
        "slaptazodis/atkurti/",
        _legacy_route(ParentPasswordResetView.as_view(), "password_reset"),
    ),
    path(
        "slaptazodis/issiusta/",
        _legacy_route(ParentPasswordResetDoneView.as_view(), "password_reset_done"),
    ),
    path(
        "slaptazodis/naujas/<uidb64>/<token>/",
        _legacy_route(ParentPasswordResetConfirmView.as_view(), "password_reset_confirm"),
    ),
    path(
        "slaptazodis/pakeistas/",
        _legacy_route(ParentPasswordResetCompleteView.as_view(), "password_reset_complete"),
    ),
    path("atsijungti/", _legacy_route(session_logout, "logout")),
    path("susieti-irengini/", _legacy_route(pair_device_via_link, "pair_device_via_link")),
    path("vaikas/", _legacy_route(child_select, "child_select")),
    path("vaikas/mano/", _legacy_route(child_dashboard, "child_dashboard")),
    path("vaikas/busena/", _legacy_route(child_state, "child_state")),
    path(
        "vaikas/pirmas-prisijungimas/",
        _legacy_route(child_theme_onboarding, "child_theme_onboarding"),
    ),
    path("vaikas/avataras/<int:child_id>/", _legacy_route(child_avatar, "child_avatar")),
    path("vaikas/darbas/<int:task_id>/", _legacy_route(child_submit_task, "child_submit_task")),
    path(
        "vaikas/paskirtas-darbas/<int:assigned_task_id>/atlikta/",
        _legacy_route(child_complete_assigned_task, "child_complete_assigned_task"),
    ),
    path(
        "vaikas/darbo-prasymas/<int:claim_id>/pateikti-is-naujo/",
        _legacy_route(child_resubmit_task, "child_resubmit_task"),
    ),
    path(
        "vaikas/darbo-prasymas/<int:claim_id>/supratau/",
        _legacy_route(child_acknowledge_task_response, "child_acknowledge_task_response"),
    ),
    path(
        "darbo-irodymas/<int:claim_id>/<str:size>/",
        _legacy_route(task_evidence, "task_evidence"),
    ),
    path(
        "vaikas/prizas/<int:reward_id>/",
        _legacy_route(child_request_reward, "child_request_reward"),
    ),
    path(
        "vaikas/loterija/pirkti/",
        _legacy_route(child_purchase_lottery_ticket, "child_purchase_lottery_ticket"),
    ),
    path(
        "vaikas/loterija/<int:ticket_id>/atidengti/",
        _legacy_route(child_reveal_lottery_ticket, "child_reveal_lottery_ticket"),
    ),
    path(
        "vaikas/prizo-prasymas/<int:request_id>/atsaukti/",
        _legacy_route(child_cancel_reward, "child_cancel_reward"),
    ),
    path("vaikas/pasiulyti/", _legacy_route(child_create_proposal, "child_create_proposal")),
    path(
        "vaikas/tikslas/<int:goal_id>/rezimas/",
        _legacy_route(child_set_goal_mode, "child_set_goal_mode"),
    ),
    path(
        "vaikas/tikslas/<int:goal_id>/prideti/",
        _legacy_route(child_add_goal_points, "child_add_goal_points"),
    ),
    path(
        "vaikas/tikslas/<int:goal_id>/uzbaigti/",
        _legacy_route(child_request_goal_completion, "child_request_goal_completion"),
    ),
    path("vaikas/tema/", _legacy_route(child_set_theme, "child_set_theme")),
    path("vaikas/dovana/", _legacy_route(child_give_points, "child_give_points")),
    path("vaikas/gimtadienis/", _legacy_route(child_set_birth_date, "child_set_birth_date")),
    path("vaikas/pin/", _legacy_route(child_change_pin, "child_change_pin")),
    path("vaikas/avataras/", _legacy_route(child_set_avatar, "child_set_avatar")),
    path("tevai/", _legacy_route(parent_dashboard, "parent_dashboard")),
    path(
        "tevai/laukianciu-prasymu-busena/",
        _legacy_route(parent_pending_state, "parent_pending_state"),
    ),
    path(
        "tevai/tikslai/<int:goal_id>/prideti/",
        _legacy_route(parent_add_goal_points, "parent_add_goal_points"),
    ),
    path(
        "tevai/tikslai/<int:goal_id>/grazinti/",
        _legacy_route(parent_return_goal_points, "parent_return_goal_points"),
    ),
    path(
        "tevai/tikslai/<int:goal_id>/redaguoti/",
        _legacy_route(parent_edit_goal, "parent_edit_goal"),
    ),
    path(
        "tevai/tikslai/<int:goal_id>/uzdaryti/",
        _legacy_route(parent_close_goal, "parent_close_goal"),
    ),
    path(
        "tevai/tikslai/<int:goal_id>/istrinti/",
        _legacy_route(parent_delete_goal, "parent_delete_goal"),
    ),
    path(
        "tevai/tikslo-prasymas/<int:request_id>/<str:decision>/",
        _legacy_route(parent_decide_goal_completion, "parent_decide_goal_completion"),
    ),
    path(
        "tevai/paskyros/tevai/nauja/",
        _legacy_route(parent_create_parent_account, "parent_create_parent_account"),
    ),
    path(
        "tevai/paskyros/vaikai/nauja/",
        _legacy_route(parent_create_child_account, "parent_create_child_account"),
    ),
    path(
        "tevai/paskyros/tevai/<int:account_id>/redaguoti/",
        _legacy_route(parent_edit_parent_account, "parent_edit_parent_account"),
    ),
    path(
        "tevai/paskyros/tevai/<int:account_id>/salinti/",
        _legacy_route(parent_remove_parent_account, "parent_remove_parent_account"),
    ),
    path(
        "tevai/paskyros/vaikai/<int:child_id>/redaguoti/",
        _legacy_route(parent_edit_child_account, "parent_edit_child_account"),
    ),
    path(
        "tevai/paskyros/vaikai/<int:child_id>/salinti/",
        _legacy_route(parent_remove_child_account, "parent_remove_child_account"),
    ),
    path(
        "tevai/katalogas/<str:kind>/",
        _legacy_route(parent_create_catalog, "parent_create_catalog"),
    ),
    path(
        "tevai/katalogas/<str:kind>/<int:item_id>/perjungti/",
        _legacy_route(parent_toggle_catalog, "parent_toggle_catalog"),
    ),
    path(
        "tevai/katalogas/<str:kind>/<int:item_id>/redaguoti/",
        _legacy_route(parent_edit_catalog, "parent_edit_catalog"),
    ),
    path(
        "tevai/katalogas/<str:kind>/<int:item_id>/trinti/",
        _legacy_route(parent_delete_catalog, "parent_delete_catalog"),
    ),
    path(
        "tevai/darbas/<int:claim_id>/<str:decision>/",
        _legacy_route(parent_decide_task, "parent_decide_task"),
    ),
    path(
        "tevai/prizas/<int:request_id>/<str:decision>/",
        _legacy_route(parent_decide_reward, "parent_decide_reward"),
    ),
    path(
        "tevai/pasiulymas/<int:proposal_id>/<str:decision>/",
        _legacy_route(parent_decide_proposal, "parent_decide_proposal"),
    ),
    path(
        "tevai/gimtadienis/<int:request_id>/<str:decision>/",
        _legacy_route(parent_decide_birth_date, "parent_decide_birth_date"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/balansas/",
        _legacy_route(parent_adjust_balance, "parent_adjust_balance"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/bausme/",
        _legacy_route(parent_apply_penalty, "parent_apply_penalty"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/atliktas-darbas/",
        _legacy_route(parent_award_task, "parent_award_task"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/paskirti-darbus/",
        _legacy_route(parent_assign_tasks, "parent_assign_tasks"),
    ),
    path(
        "tevai/paskirtas-darbas/<int:assigned_task_id>/atsaukti/",
        _legacy_route(parent_cancel_assigned_task, "parent_cancel_assigned_task"),
    ),
    path(
        "tevai/paskirtu-darbu-sarasas/<int:batch_id>/atsaukti/",
        _legacy_route(parent_cancel_assigned_task_batch, "parent_cancel_assigned_task_batch"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/skirti-nuoboda/",
        _legacy_route(parent_assign_child_penalty, "parent_assign_child_penalty"),
    ),
    path(
        "tevai/nuoboda/<int:penalty_id>/skirti/",
        _legacy_route(parent_assign_penalty, "parent_assign_penalty"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/limitas/",
        _legacy_route(parent_set_min_balance, "parent_set_min_balance"),
    ),
    path(
        "tevai/vaikas/<int:child_id>/atrakinti/",
        _legacy_route(parent_unlock_child, "parent_unlock_child"),
    ),
    path(
        "tevai/nustatymai/seima/",
        _legacy_route(parent_update_family_preferences, "parent_update_family_preferences"),
    ),
    path(
        "tevai/nustatymai/tinklas/",
        _legacy_route(parent_update_network_access, "parent_update_network_access"),
    ),
    path(
        "tevai/irenginiai/susieti-si/",
        _legacy_route(parent_pair_device, "parent_pair_device"),
    ),
    path(
        "tevai/irenginiai/nuoroda/",
        _legacy_route(parent_generate_pairing_link, "parent_generate_pairing_link"),
    ),
    path(
        "tevai/irenginiai/<int:device_id>/atsaukti/",
        _legacy_route(parent_revoke_device, "parent_revoke_device"),
    ),
    path(
        "tevai/irenginiai/<int:device_id>/pervadinti/",
        _legacy_route(parent_rename_device, "parent_rename_device"),
    ),
    path(
        "tevai/irenginiai/atsaukti-visus/",
        _legacy_route(parent_revoke_all_devices, "parent_revoke_all_devices"),
    ),
    path(
        "tevai/nustatymai/kopijos/",
        _legacy_route(parent_configure_backup, "parent_configure_backup"),
    ),
    path(
        "tevai/nustatymai/el-pastas/",
        _legacy_route(parent_configure_smtp, "parent_configure_smtp"),
    ),
    path(
        "tevai/nustatymai/kopijos/paleisti/",
        _legacy_route(parent_run_backup, "parent_run_backup"),
    ),
    path(
        "tevai/atsiliepimas/<int:report_id>/busena/",
        _legacy_route(parent_update_feedback_status, "parent_update_feedback_status"),
    ),
    path(
        "vaikas/push/subscribe/",
        _legacy_route(child_push_subscribe, "child_push_subscribe"),
    ),
    path(
        "vaikas/push/unsubscribe/",
        _legacy_route(child_push_unsubscribe, "child_push_unsubscribe"),
    ),
]
