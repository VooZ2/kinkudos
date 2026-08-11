import logging
import smtplib

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from economy.auth import parent_required
from economy.backups import backup_status, configure_backup, request_manual_backup
from economy.email_config import save_smtp_config, verify_smtp
from economy.forms import (
    BackupSettingsForm,
    FamilyPreferencesForm,
    NetworkAccessForm,
    SmtpSettingsForm,
)
from economy.models import (
    BackupAuditEvent,
    FamilySettings,
    SecurityAuditEvent,
)
from economy.net import client_ip

logger = logging.getLogger("economy.views")


@parent_required
@require_POST
def parent_update_family_preferences(request):
    family = FamilySettings.load()
    form = FamilyPreferencesForm(request.POST, instance=family)
    if form.is_valid():
        form.save()
        messages.success(request, _("Family settings saved."))
    else:
        messages.error(request, _("Check the family settings."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_required
@require_POST
def parent_update_network_access(request):
    if not request.user.is_staff:
        messages.error(
            request,
            _("Only a parent administrator can change network access."),
        )
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    family = FamilySettings.load()
    form = NetworkAccessForm(
        request.POST,
        instance=family,
        current_ip=client_ip(request),
    )
    if not form.is_valid():
        messages.error(request, _("Check the network access settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    family = form.save()
    SecurityAuditEvent.objects.create(
        actor=request.user,
        action=SecurityAuditEvent.Action.NETWORK_POLICY_CHANGED,
        detail=family.network_access_mode,
    )
    messages.success(request, _("Network access settings saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_required
@require_POST
def parent_configure_smtp(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can change email settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    form = SmtpSettingsForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the email settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    config = {
        key: form.cleaned_data[key]
        for key in (
            "enabled",
            "host",
            "port",
            "security",
            "username",
            "password",
            "from_email",
            "feedback_email",
        )
    }
    try:
        verify_smtp(config)
        save_smtp_config(config)
    except (OSError, ValueError, smtplib.SMTPException):
        logger.warning("SMTP settings verification failed", exc_info=True)
        messages.error(
            request,
            _("Email settings were not saved. Check the server details and credentials."),
        )
    else:
        messages.success(request, _("Email settings were verified and saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_required
@require_POST
def parent_configure_backup(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can change backup settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    form = BackupSettingsForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the backup settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    try:
        status = configure_backup(form.cleaned_data)
    except RuntimeError as exc:
        messages.error(request, _("Backup settings were not saved: %(error)s") % {"error": exc})
    else:
        BackupAuditEvent.objects.create(
            actor=request.user,
            action=BackupAuditEvent.Action.CONFIGURED,
            provider=status.get("provider", ""),
            target=status.get("target", ""),
        )
        messages.success(request, _("Backup storage was verified and saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_required
@require_POST
def parent_run_backup(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can start a backup."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    try:
        request_manual_backup()
    except RuntimeError as exc:
        messages.error(request, _("The backup could not be started: %(error)s") % {"error": exc})
    else:
        status = backup_status()
        BackupAuditEvent.objects.create(
            actor=request.user,
            action=BackupAuditEvent.Action.MANUAL_RUN,
            provider=status.get("provider", ""),
            target=status.get("target", ""),
        )
        messages.success(request, _("Backup started. Refresh this page to see its status."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")
