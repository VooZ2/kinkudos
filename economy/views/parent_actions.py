
from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from economy.auth import (
    ensure_child_accessible,
    get_accessible_child_or_404,
    parent_account_required,
    parent_required,
)
from economy.forms import (
    AdjustmentForm,
    ApplyPenaltyForm,
    ApprovalCostForm,
    AssignPenaltiesForm,
    AssignTasksForm,
    AwardTasksForm,
    ChildAccountForm,
    ChildEditForm,
    GoalAmountForm,
    MinBalanceForm,
    ParentAccountForm,
    ParentEditForm,
    PenaltyForm,
    RejectForm,
    RewardForm,
    SaveAssignmentPresetForm,
    SavingsGoalForm,
    TaskDecisionCommentForm,
    TaskForm,
)
from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    AssignmentPreset,
    BirthDateChangeRequest,
    GoalCompletionRequest,
    GoalStatus,
    LedgerKind,
    PenaltyTemplate,
    Proposal,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    Task,
    TaskClaim,
    TaskCompletion,
)
from economy.push import (
    notify_assigned_tasks,
    notify_birth_date_decision,
    notify_proposal_decision,
    notify_reward_decision,
    notify_task_decision,
    notify_task_revision,
)
from economy.services import (
    add_saved_points,
    apply_assignment_preset,
    approve_goal_completion,
    approve_proposal,
    approve_reward_request,
    approve_task_claim,
    assign_tasks,
    cancel_assigned_task,
    cancel_assigned_task_batch,
    close_savings_goal,
    deactivate_parent_account,
    delete_savings_goal,
    ensure_task_completion,
    keep_goal_active,
    post_ledger_entry,
    reject_proposal,
    reject_reward_request,
    reject_task_claim,
    request_task_revision,
    return_saved_points,
    save_assignment_preset,
    update_savings_goal,
)


@parent_account_required
@require_POST
def parent_create_catalog(request, kind):
    forms = {"task": TaskForm, "penalty": PenaltyForm, "reward": RewardForm}
    form_class = forms.get(kind)
    if form_class is None:
        raise Http404
    form = form_class(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, _("Catalog item created."))
    else:
        messages.error(request, _("Check the entered data."))
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_create_parent_account(request):
    form = ParentAccountForm(request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, _("Parent account “%(username)s” created.") % {"username": user.username})
    else:
        messages.error(request, _("Check the new parent account details."))
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_create_child_account(request):
    form = ChildAccountForm(request.POST)
    if form.is_valid():
        child = form.save()
        messages.success(request, _("Child profile “%(name)s” created.") % {"name": child.name})
    else:
        messages.error(request, _("Check the new child profile details."))
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_edit_parent_account(request, account_id):
    account = get_object_or_404(get_user_model(), pk=account_id, is_active=True)
    if account.is_staff and not request.user.is_staff:
        messages.error(
            request,
            _("Only a parent administrator can manage an administrator account."),
        )
        return redirect("parent_dashboard")
    form = ParentEditForm(request.POST, account=account, actor=request.user)
    if form.is_valid():
        form.save()
        if account.pk == request.user.pk and form.cleaned_data.get("new_password"):
            update_session_auth_hash(request, account)
        messages.success(request, _("Parent account “%(username)s” updated.") % {"username": account.username})
    else:
        messages.error(request, _("Check the parent account details."))
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_remove_parent_account(request, account_id):
    account = get_object_or_404(get_user_model(), pk=account_id, is_active=True)
    if account.pk == request.user.pk:
        messages.error(request, _("You cannot remove the account you are currently using."))
    elif account.is_staff and not request.user.is_staff:
        messages.error(
            request,
            _("Only a parent administrator can manage an administrator account."),
        )
    else:
        deactivated = deactivate_parent_account(account)
        if deactivated:
            messages.success(
                request,
                _("Parent account “%(username)s” removed.") % {"username": account.username},
            )
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_edit_child_account(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = ChildEditForm(request.POST, child=child)
    if form.is_valid():
        form.save(actor=request.user)
        messages.success(request, _("Child profile “%(name)s” updated.") % {"name": child.name})
    else:
        messages.error(request, _("Check the child profile details."))
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_decide_birth_date(request, request_id, decision):
    try:
        with transaction.atomic():
            change = (
                BirthDateChangeRequest.objects.select_for_update()
                .select_related("child")
                .get(pk=request_id)
            )
            ensure_child_accessible(request, change.child)
            if change.status != RequestStatus.PENDING:
                raise ValidationError(_("This request has already been resolved."))
            if decision == "approve":
                change.child.birth_date = change.requested_birth_date
                change.child.birth_date_initialized = True
                change.child.save(
                    update_fields=["birth_date", "birth_date_initialized"]
                )
                change.status = RequestStatus.APPROVED
                success_message = _("Birthday change approved.")
            elif decision == "reject":
                change.status = RequestStatus.REJECTED
                success_message = _("Birthday change rejected.")
            else:
                raise Http404
            change.decided_by = request.user
            change.decided_at = timezone.now()
            change.save(update_fields=["status", "decided_by", "decided_at"])
        notify_birth_date_decision(change, approved=decision == "approve")
        messages.success(request, success_message)
    except BirthDateChangeRequest.DoesNotExist:
        raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_remove_child_account(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    child.is_active = False
    child.save(update_fields=["is_active"])
    messages.success(request, _("Child profile “%(name)s” removed.") % {"name": child.name})
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_edit_catalog(request, kind, item_id):
    forms = {"task": TaskForm, "penalty": PenaltyForm, "reward": RewardForm}
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    form_class = forms.get(kind)
    model = models.get(kind)
    if form_class is None or model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    form = form_class(request.POST, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, _("“%(title)s” updated.") % {"title": item.title})
    else:
        messages.error(request, _("Check the edited data."))
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_toggle_catalog(request, kind, item_id):
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    model = models.get(kind)
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    item.is_active = not item.is_active
    item.save(update_fields=["is_active"])
    messages.success(
        request,
        _("“%(title)s” is now %(state)s.")
        % {"title": item.title, "state": _("visible") if item.is_active else _("hidden")},
    )
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_delete_catalog(request, kind, item_id):
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    model = models.get(kind)
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    item.is_active = False
    item.is_deleted = True
    item.save(update_fields=["is_active", "is_deleted"])
    messages.success(request, _("“%(title)s” deleted.") % {"title": item.title})
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_required
@require_POST
def parent_decide_task(request, claim_id, decision):
    claim = get_object_or_404(TaskClaim.objects.select_related("child"), pk=claim_id)
    ensure_child_accessible(request, claim.child)
    try:
        if decision == "approve":
            approve_task_claim(claim=claim, actor=request.user)
            claim.refresh_from_db()
            notify_task_decision(claim, approved=True)
            messages.success(request, _("Task approved."))
        elif decision == "reject":
            form = TaskDecisionCommentForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Check the comment."))
            claim = reject_task_claim(
                claim=claim,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            notify_task_decision(claim, approved=False)
            messages.success(request, _("Task rejected."))
        elif decision == "revise":
            form = TaskDecisionCommentForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Check the comment."))
            request_task_revision(
                claim=claim,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            claim.refresh_from_db()
            notify_task_revision(claim)
            messages.success(request, _("The task was returned for improvements."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_decide_reward(request, request_id, decision):
    reward_request = get_object_or_404(
        RewardRequest.objects.select_related("child"), pk=request_id
    )
    ensure_child_accessible(request, reward_request.child)
    try:
        if decision == "approve":
            approve_reward_request(request=reward_request, actor=request.user)
            reward_request.refresh_from_db()
            notify_reward_decision(reward_request, approved=True)
            messages.success(request, _("Reward approved."))
        elif decision == "reject":
            form = RejectForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("A rejection reason is required."))
            locked = reject_reward_request(
                request=reward_request,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            notify_reward_decision(locked, approved=False)
            messages.success(request, _("Reward request rejected."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_decide_proposal(request, proposal_id, decision):
    proposal = get_object_or_404(Proposal.objects.select_related("child"), pk=proposal_id)
    ensure_child_accessible(request, proposal.child)
    try:
        if decision == "approve":
            form = ApprovalCostForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Enter the final point amount."))
            approve_proposal(
                proposal=proposal,
                actor=request.user,
                final_cost=form.cleaned_data["final_cost"],
                goal_mode=request.POST.get("goal_mode") or None,
            )
            proposal.refresh_from_db()
            notify_proposal_decision(proposal, approved=True)
            messages.success(request, _("Suggestion approved."))
        elif decision == "reject":
            form = RejectForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("A rejection reason is required."))
            proposal = reject_proposal(
                proposal=proposal,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            notify_proposal_decision(proposal, approved=False)
            messages.success(request, _("Suggestion rejected."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_decide_goal_completion(request, request_id, decision):
    completion_request = get_object_or_404(
        GoalCompletionRequest.objects.select_related("goal", "goal__child"),
        pk=request_id,
        goal__child__is_active=True,
    )
    ensure_child_accessible(request, completion_request.goal.child)
    try:
        if decision == "complete":
            approve_goal_completion(
                completion_request=completion_request,
                actor=request.user,
            )
            messages.success(request, _("Goal completed."))
        elif decision == "keep_active":
            keep_goal_active(
                completion_request=completion_request,
                actor=request.user,
            )
            messages.info(request, _("The goal will stay active."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-home")

@parent_account_required
@require_POST
def parent_add_goal_points(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal.objects.select_related("child"),
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    ensure_child_accessible(request, goal.child)
    form = GoalAmountForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError(_("Enter a valid point amount."))
        add_saved_points(
            goal=goal,
            child=goal.child,
            amount=form.cleaned_data["amount"],
            actor=request.user,
        )
        messages.success(request, _("Points were saved for this goal."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_return_goal_points(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal.objects.select_related("child"),
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    ensure_child_accessible(request, goal.child)
    try:
        amount = return_saved_points(goal=goal, actor=request.user)
        messages.success(
            request,
            _("%(amount)s points are available for rewards again.") % {"amount": amount},
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_edit_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal.objects.select_related("child"),
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    ensure_child_accessible(request, goal.child)
    form = SavingsGoalForm(request.POST, instance=goal)
    try:
        if not form.is_valid():
            raise ValidationError(_("Check the goal details."))
        update_savings_goal(
            goal=goal,
            title=form.cleaned_data["title"],
            target_amount=form.cleaned_data["target_amount"],
            icon=form.cleaned_data["icon"],
            actor=request.user,
        )
        messages.success(request, _("Goal updated."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_close_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal.objects.select_related("child"),
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    ensure_child_accessible(request, goal.child)
    try:
        close_savings_goal(goal=goal, actor=request.user)
        messages.success(request, _("Goal closed."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_account_required
@require_POST
def parent_delete_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal.objects.select_related("child"),
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    ensure_child_accessible(request, goal.child)
    try:
        _deleted_goal, returned_amount = delete_savings_goal(
            goal=goal,
            actor=request.user,
        )
        if returned_amount:
            messages.success(
                request,
                _("Goal deleted and %(amount)s points returned.")
                % {"amount": returned_amount},
            )
        else:
            messages.success(request, _("Goal deleted."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")

@parent_required
@require_POST
def parent_adjust_balance(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = AdjustmentForm(request.POST)
    if form.is_valid():
        post_ledger_entry(
            child=child,
            delta=form.cleaned_data["amount"],
            kind=LedgerKind.ADJUSTMENT,
            description=form.cleaned_data["description"],
            actor=request.user,
        )
        messages.success(request, _("Balance adjusted."))
    else:
        messages.error(request, _("Check the balance adjustment."))
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_apply_penalty(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = ApplyPenaltyForm(request.POST)
    if form.is_valid():
        penalty = get_object_or_404(
            PenaltyTemplate,
            pk=form.cleaned_data["penalty_id"],
            is_active=True,
        )
        post_ledger_entry(
            child=child,
            delta=penalty.amount,
            kind=LedgerKind.PENALTY,
            description=f"{penalty.title}: {form.cleaned_data['reason']}",
            actor=request.user,
            source_id=penalty.pk,
        )
        messages.success(request, _("Penalty assigned."))
    else:
        messages.error(request, _("A reason is required."))
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_award_task(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = AwardTasksForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Choose at least one active task."))
        return redirect("parent_dashboard")

    tasks = list(form.cleaned_data["task_ids"])
    today = timezone.localdate()
    already_credited = set(
        TaskCompletion.objects.filter(
            child=child,
            task__in=tasks,
            completed_on=today,
        ).values_list("task_id", flat=True)
    )
    tasks = [task for task in tasks if task.pk not in already_credited]
    if not tasks:
        messages.error(
            request,
            _("Those tasks were already credited to this child today."),
        )
        return redirect("parent_dashboard")
    with transaction.atomic():
        for task in tasks:
            post_ledger_entry(
                child=child,
                delta=task.reward,
                kind=LedgerKind.TASK,
                description=task.title,
                actor=request.user,
                source_id=task.pk,
            )
            ensure_task_completion(
                child=child,
                task=task,
                completed_on=today,
            )
    total = sum(task.reward for task in tasks)
    messages.success(
        request,
        _("%(name)s received %(count)s task(s) (total +%(total)s).")
        % {"name": child.name, "count": len(tasks), "total": total},
    )
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_assign_tasks(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = AssignTasksForm(request.POST)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect("parent_dashboard")
    try:
        batch = assign_tasks(
            child=child,
            actor=request.user,
            tasks=list(form.cleaned_data["task_ids"]),
            custom_title=form.cleaned_data["custom_title"],
            custom_points=form.cleaned_data["custom_points"],
            blocks_rewards=form.cleaned_data["blocks_rewards"],
            task_notes=form.cleaned_data["task_notes"],
            custom_note=form.cleaned_data["custom_note"],
        )
        notify_assigned_tasks(batch)
        messages.success(
            request,
            _("Tasks were assigned to %(name)s for today.")
            % {"name": child.name},
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_save_assignment_preset(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = SaveAssignmentPresetForm(request.POST)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect("parent_dashboard")
    try:
        save_assignment_preset(
            child=child,
            actor=request.user,
            name=form.cleaned_data["preset_name"],
            tasks=list(form.cleaned_data["task_ids"]),
            task_notes=form.cleaned_data["task_notes"],
            custom_title=form.cleaned_data["custom_title"],
            custom_points=form.cleaned_data["custom_points"],
            custom_note=form.cleaned_data["custom_note"],
            blocks_rewards=form.cleaned_data["blocks_rewards"],
            cadence=form.cleaned_data["cadence"],
            weekday_mask=form.cleaned_data["weekday_mask"],
            weekend_mode=form.cleaned_data["weekend_mode"],
            weekly_weekday=form.cleaned_data["weekly_weekday"],
            run_at=form.cleaned_data["run_at"],
        )
        messages.success(request, _('Saved set "%(name)s".') % {
            "name": form.cleaned_data["preset_name"],
        })
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_apply_assignment_preset(request, preset_id):
    preset = get_object_or_404(
        AssignmentPreset.objects.select_related("child"),
        pk=preset_id,
        child__is_active=True,
    )
    ensure_child_accessible(request, preset.child)
    try:
        batch = apply_assignment_preset(preset=preset, actor=request.user)
        if batch is None:
            messages.info(
                request,
                _("Nothing from this set is available to assign today."),
            )
        else:
            notify_assigned_tasks(batch)
            messages.success(
                request,
                _("Tasks were assigned to %(name)s for today.")
                % {"name": preset.child.name},
            )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_toggle_assignment_preset(request, preset_id):
    preset = get_object_or_404(
        AssignmentPreset,
        pk=preset_id,
        child__is_active=True,
    )
    preset.is_paused = not preset.is_paused
    preset.save(update_fields=["is_paused", "updated_at"])
    if preset.is_paused:
        messages.success(request, _('Paused "%(name)s".') % {"name": preset.name})
    else:
        messages.success(request, _('Resumed "%(name)s".') % {"name": preset.name})
    return redirect("parent_dashboard")

@parent_account_required
@require_POST
def parent_delete_assignment_preset(request, preset_id):
    preset = get_object_or_404(
        AssignmentPreset,
        pk=preset_id,
        child__is_active=True,
    )
    name = preset.name
    preset.delete()
    messages.success(request, _('Deleted "%(name)s".') % {"name": name})
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_cancel_assigned_task(request, assigned_task_id):
    assigned_task = get_object_or_404(
        AssignedTask.objects.select_related("batch", "batch__child"),
        pk=assigned_task_id,
        batch__child__is_active=True,
    )
    ensure_child_accessible(request, assigned_task.batch.child)
    try:
        cancel_assigned_task(assigned_task=assigned_task, actor=request.user)
        messages.success(request, _("The assigned task was cancelled."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_cancel_assigned_task_batch(request, batch_id):
    batch = get_object_or_404(
        AssignedTaskBatch.objects.select_related("child"),
        pk=batch_id,
        child__is_active=True,
    )
    ensure_child_accessible(request, batch.child)
    cancelled = cancel_assigned_task_batch(batch=batch, actor=request.user)
    if cancelled:
        messages.success(request, _("The remaining assigned tasks were cancelled."))
    else:
        messages.info(request, _("There are no waiting tasks to cancel."))
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_assign_child_penalty(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = AssignPenaltiesForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Choose at least one active penalty."))
        return redirect("parent_dashboard")

    penalties = list(form.cleaned_data["penalty_ids"])
    reason = form.cleaned_data["reason"].strip()
    with transaction.atomic():
        for penalty in penalties:
            description = penalty.title if not reason else f"{penalty.title}: {reason}"
            post_ledger_entry(
                child=child,
                delta=penalty.amount,
                kind=LedgerKind.PENALTY,
                description=description,
                actor=request.user,
                source_id=penalty.pk,
            )
    total = sum(penalty.amount for penalty in penalties)
    messages.success(
        request,
        _("%(name)s received %(count)s penalty/penalties (total %(total)s).")
        % {"name": child.name, "count": len(penalties), "total": total},
    )
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_assign_penalty(request, penalty_id):
    penalty = get_object_or_404(PenaltyTemplate, pk=penalty_id, is_active=True)
    child = get_accessible_child_or_404(request, request.POST.get("child_id"))
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, _("A reason is required."))
        return redirect("parent_dashboard")
    post_ledger_entry(
        child=child,
        delta=penalty.amount,
        kind=LedgerKind.PENALTY,
        description=f"{penalty.title}: {reason}",
        actor=request.user,
        source_id=penalty.pk,
    )
    messages.success(
        request,
        _("Penalty “%(penalty)s” assigned to %(name)s.")
        % {"penalty": penalty.title, "name": child.name},
    )
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_set_min_balance(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    form = MinBalanceForm(request.POST)
    if form.is_valid():
        child.min_balance = form.cleaned_data["min_balance"]
        child.save(update_fields=["min_balance"])
        messages.success(request, _("Credit limit changed."))
    return redirect("parent_dashboard")

@parent_required
@require_POST
def parent_unlock_child(request, child_id):
    child = get_accessible_child_or_404(request, child_id)
    child.failed_pin_attempts = 0
    child.locked_until = None
    child.save(update_fields=["failed_pin_attempts", "locked_until"])
    messages.success(request, _("%(name)s unlocked.") % {"name": child.name})
    return redirect("parent_dashboard")
