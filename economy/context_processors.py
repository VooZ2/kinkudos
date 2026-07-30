from django.conf import settings

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
}


def family_context(request):
    url_name = request.resolver_match.url_name if request.resolver_match else ""
    public_header = (
        url_name in PUBLIC_HEADER_ROUTES
        and not request.user.is_authenticated
        and not request.session.get("child_id")
    )
    return {
        "family_settings": FamilySettings.load(),
        "app_version": settings.APP_VERSION,
        "project_name": "KinKudos",
        "public_header": public_header,
        "emoji_suggestions": EMOJI_SUGGESTIONS,
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        "email_enabled": settings.EMAIL_ENABLED,
        "feedback_email_configured": bool(
            settings.EMAIL_ENABLED and settings.FEEDBACK_EMAIL
        ),
        "feedback_available": bool(
            request.user.is_authenticated or request.session.get("child_id")
        ),
    }
