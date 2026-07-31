from django.conf import settings

from .auth import current_child
from .email_config import smtp_config
from .models import EMOJI_SUGGESTIONS, FamilySettings

PUBLIC_HEADER_ROUTES = {
    "home",
    "changelog",
    "offline",
    "parent_login",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
    "child_select",
    "pair_device_via_link",
}


def family_context(request):
    email = smtp_config()
    child = current_child(request)
    url_name = request.resolver_match.url_name if request.resolver_match else ""
    public_header = (
        url_name in PUBLIC_HEADER_ROUTES
        and not request.user.is_authenticated
        and child is None
    )
    return {
        "family_settings": FamilySettings.load(),
        "app_version": settings.APP_VERSION,
        "project_name": "KinKudos",
        "public_header": public_header,
        "emoji_suggestions": EMOJI_SUGGESTIONS,
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        "email_enabled": bool(email.get("enabled")),
        "feedback_email_configured": bool(
            email.get("enabled") and email.get("feedback_email")
        ),
        "feedback_available": bool(
            request.user.is_authenticated or child is not None
        ),
    }
