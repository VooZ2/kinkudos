import logging
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from economy.auth import current_child, parent_account_required
from economy.email_config import smtp_config
from economy.forms import (
    FeedbackReportForm,
    FeedbackStatusForm,
)
from economy.images import (
    ImageProcessingError,
    process_feedback_screenshot,
)
from economy.models import (
    FamilySettings,
    FeedbackReport,
)

logger = logging.getLogger("economy.views")


def _feedback_actor(request):
    if request.user.is_authenticated:
        return request.user, None
    return None, current_child(request)

def _feedback_redirect(request):
    target = request.POST.get("next", "")
    if (
        target
        and target.startswith("/")
        and url_has_allowed_host_and_scheme(
            target,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        return target
    return reverse("home")

@require_POST
def submit_feedback(request):
    parent, child = _feedback_actor(request)
    if parent is None and child is None:
        raise Http404

    recent_reports = FeedbackReport.objects.filter(
        created_at__gte=timezone.now() - timedelta(minutes=1)
    )
    recent_reports = (
        recent_reports.filter(parent=parent)
        if parent is not None
        else recent_reports.filter(child=child)
    )
    if recent_reports.count() >= 3:
        messages.error(
            request,
            _("Too many reports were sent. Wait a minute and try again."),
        )
        return redirect(_feedback_redirect(request))

    form = FeedbackReportForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(
            request,
            _("Check the feedback description and screenshot."),
        )
        return redirect(_feedback_redirect(request))

    screenshot = form.cleaned_data.get("screenshot")
    screenshot_bytes = None
    if screenshot:
        try:
            screenshot_bytes = process_feedback_screenshot(screenshot)
        except ImageProcessingError:
            messages.error(
                request,
                _("The image could not be processed. Choose another file."),
            )
            return redirect(_feedback_redirect(request))

    family = FamilySettings.load()
    report = form.save(commit=False)
    report.parent = parent
    report.child = child
    report.reporter_name = parent.username if parent is not None else child.name
    report.reporter_role = "parent" if parent is not None else "child"
    report.family_name = family.family_name
    page_path = request.POST.get("page_path", "")
    report.page_path = (
        page_path.split("?", 1)[0].split("#", 1)[0][:500]
        if page_path.startswith("/")
        else ""
    )
    report.app_version = settings.APP_VERSION
    report.language = request.LANGUAGE_CODE[:16]
    report.theme = child.theme if child is not None else ""
    report.user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
    report.save()
    if screenshot_bytes:
        report.screenshot.save(
            f"{uuid4().hex}.webp",
            ContentFile(screenshot_bytes),
            save=True,
        )

    email_failed = False
    email = smtp_config()
    if email.get("enabled") and email.get("feedback_email"):
        try:
            parent_url = request.build_absolute_uri(
                f"{reverse('parent_dashboard')}#parent-settings"
            )
            send_mail(
                _(
                    "KinKudos feedback #%(report_id)s: %(report_type)s"
                )
                % {
                    "report_id": report.pk,
                    "report_type": report.get_report_type_display(),
                },
                "\n".join(
                    [
                        f"ID: {report.pk}",
                        f"Type: {report.get_report_type_display()}",
                        f"Reporter: {report.reporter_name} ({report.reporter_role})",
                        f"Family: {report.family_name}",
                        f"Version: {report.app_version}",
                        f"Page: {report.page_path}",
                        f"Language: {report.language}",
                        f"Theme: {report.theme or '-'}",
                        "",
                        report.description,
                        "",
                        f"Review: {parent_url}",
                    ]
                ),
                email.get("from_email"),
                [email.get("feedback_email")],
                fail_silently=False,
            )
            report.email_notified_at = timezone.now()
            report.email_error = ""
            report.save(update_fields=["email_notified_at", "email_error"])
        except Exception as exc:  # SMTP failures must not lose the saved report.
            logger.warning("Feedback email notification failed", exc_info=True)
            report.email_error = type(exc).__name__[:240]
            report.save(update_fields=["email_error"])
            email_failed = True

    if email_failed:
        messages.warning(
            request,
            _("Feedback was saved, but the email notification could not be sent."),
        )
    else:
        messages.success(request, _("Thank you. Your feedback was sent."))
    return redirect(_feedback_redirect(request))

def feedback_screenshot(request, report_id):
    report = get_object_or_404(FeedbackReport, pk=report_id)
    child = current_child(request)
    if not request.user.is_authenticated and (
        child is None or report.child_id != child.pk
    ):
        raise Http404
    if not report.screenshot:
        raise Http404
    response = FileResponse(report.screenshot.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response

@parent_account_required
@require_POST
def parent_update_feedback_status(request, report_id):
    report = get_object_or_404(FeedbackReport, pk=report_id)
    form = FeedbackStatusForm(request.POST)
    if form.is_valid():
        report.status = form.cleaned_data["status"]
        report.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Feedback status updated."))
    else:
        messages.error(request, _("Choose a valid feedback status."))
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")
