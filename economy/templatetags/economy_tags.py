from django import template
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

register = template.Library()

ICONS = {
    "sparkles": "✦",
    "broom": "⌁",
    "book": "▤",
    "bed": "▰",
    "dish": "◒",
    "paw": "●",
    "school": "⌂",
    "screen": "▣",
    "gift": "◆",
    "star": "★",
}

THEME_TEXT = {
    "magic_academy": {
        "submit": _("Send an owl"),
        "task_button": _("Send an owl"),
        "task_modal_title": _("Send an owl"),
        "task_modal_submit": _("Send an owl"),
        "reward": _("Exchange galleons"),
        "proposal": _("Write in the spellbook"),
        "nav_tasks": _("Assignments"),
        "nav_rewards": _("Magic Shop"),
        "nav_goals": _("Dream Enchantments"),
        "nav_history": _("Magic Chronicle"),
    },
    "block_world": {
        "submit": _("Submit block"),
        "task_button": _("Submit block"),
        "task_modal_title": _("Submit block"),
        "task_modal_submit": _("Submit block"),
        "reward": _("Take from the chest"),
        "proposal": _("Craft a recipe"),
        "nav_tasks": _("Missions"),
        "nav_rewards": _("Reward Chest"),
        "nav_goals": _("Building Plan"),
        "nav_history": _("Activity Log"),
    },
    "neutral": {
        "submit": _("Submit"),
        "task_button": _("Submit"),
        "task_modal_title": _("Submit task"),
        "task_modal_submit": _("Submit"),
        "reward": _("Order"),
        "proposal": _("Suggest"),
        "nav_tasks": _("Tasks"),
        "nav_rewards": _("Rewards"),
        "nav_goals": _("Goals"),
        "nav_history": _("History"),
    },
    "hero_hq": {
        "submit": _("Activate mission"),
        "task_button": _("Activate mission"),
        "task_modal_title": _("Send a signal to HQ"),
        "task_modal_submit": _("Send signal"),
        "reward": _("Request from arsenal"),
        "proposal": _("Propose a secret plan"),
        "nav_tasks": _("Hero Missions"),
        "nav_rewards": _("HQ Arsenal"),
        "nav_goals": _("Secret Plan"),
        "nav_history": _("Mission Log"),
    },
    "art_studio": {
        "submit": _("Present artwork"),
        "task_button": _("Present artwork"),
        "task_modal_title": _("Project ready for review"),
        "task_modal_submit": _("Submit project"),
        "reward": _("Choose inspiration"),
        "proposal": _("Suggest an idea"),
        "nav_tasks": _("Creative Projects"),
        "nav_rewards": _("Inspiration Shop"),
        "nav_goals": _("My Gallery"),
        "nav_history": _("Creative Journal"),
    },
    "panda_pet": {
        "submit": _("Feed the panda"),
        "task_button": _("Feed the panda"),
        "task_modal_title": _("Bamboo is ready!"),
        "task_modal_submit": _("Give bamboo"),
        "reward": _("Open treat chest"),
        "proposal": _("Make a panda wish"),
        "nav_tasks": _("Panda Tasks"),
        "nav_rewards": _("Treat Chest"),
        "nav_goals": _("Panda's Dream"),
        "nav_history": _("Panda Tracks"),
    },
}


@register.filter
def icon_symbol(value):
    return ICONS.get(value, value or "⭐")


@register.filter
def theme_text(theme, action):
    return THEME_TEXT.get(theme, THEME_TEXT["neutral"]).get(action, action)


@register.filter
def absolute(value):
    try:
        return abs(int(value))
    except (TypeError, ValueError):
        return value


@register.filter
def user_display_name(user):
    if not user:
        return ""
    full_name = user.get_full_name().strip()
    return full_name or user.get_username()


def _lithuanian_form(number, singular, paucal, plural):
    last_two = number % 100
    last = number % 10
    if last == 1 and last_two != 11:
        return singular
    if 2 <= last <= 9 and not 12 <= last_two <= 19:
        return paucal
    return plural


@register.filter
def currency_unit(value, theme="neutral"):
    """Return the grammatically correct unit for a child theme."""
    try:
        number = abs(int(value))
    except (TypeError, ValueError):
        number = 0

    theme = str(theme)
    if get_language() == "lt":
        units = {
            "neutral": ("taškas", "taškai", "taškų"),
            "block_world": ("smaragdas", "smaragdai", "smaragdų"),
            "magic_academy": ("galeonas", "galeonai", "galeonų"),
            "hero_hq": ("ženklelis", "ženkleliai", "ženklelių"),
            "art_studio": ("perlas", "perlai", "perlų"),
            "panda_pet": ("bambukas", "bambukai", "bambukų"),
        }
        return _lithuanian_form(number, *units.get(theme, units["neutral"]))

    units = {
        "neutral": ("point", "points"),
        "block_world": ("emerald", "emeralds"),
        "magic_academy": ("galleon", "galleons"),
        "hero_hq": ("badge", "badges"),
        "art_studio": ("pearl", "pearls"),
        "panda_pet": ("bamboo", "bamboo"),
    }
    singular, plural = units.get(theme, units["neutral"])
    return singular if number == 1 else plural


@register.filter
def token_unit(value, currency_name="Points"):
    """Backward-compatible alias for the neutral point unit."""
    return currency_unit(value, "neutral")
