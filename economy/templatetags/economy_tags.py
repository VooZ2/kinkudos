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
        "assigned_eyebrow": _("Message from the owl post"),
        "assigned_title": _("Today's enchanted duties"),
        "assigned_help": _("Complete each duty before the magic fades at midnight."),
        "assigned_complete": _("Spell complete"),
        "assigned_reward_block": _("The magic shop opens after today's enchanted duties are complete."),
        "lottery_title": _("Enchanted Prophecy"),
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
        "assigned_eyebrow": _("Priority build"),
        "assigned_title": _("Today's assigned missions"),
        "assigned_help": _("Complete every mission before the world resets at midnight."),
        "assigned_complete": _("Mission complete"),
        "assigned_reward_block": _("The reward chest unlocks after today's assigned missions are complete."),
        "lottery_title": _("Hidden Emerald Grid"),
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
        "assigned_eyebrow": _("Priority"),
        "assigned_title": _("Tasks from your parents"),
        "assigned_help": _("Complete each task today. They expire at midnight."),
        "assigned_complete": _("Completed"),
        "assigned_reward_block": _("Complete the assigned tasks to unlock new reward requests."),
        "lottery_title": _("Lucky Ticket"),
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
        "assigned_eyebrow": _("Incoming HQ orders"),
        "assigned_title": _("Today's priority missions"),
        "assigned_help": _("Complete every mission before midnight."),
        "assigned_complete": _("Mission accomplished"),
        "assigned_reward_block": _("The HQ arsenal unlocks after today's priority missions are complete."),
        "lottery_title": _("Classified Chance Card"),
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
        "assigned_eyebrow": _("Studio priority"),
        "assigned_title": _("Today's commissioned projects"),
        "assigned_help": _("Finish every project before the studio closes at midnight."),
        "assigned_complete": _("Project finished"),
        "assigned_reward_block": _("The inspiration shop opens after today's commissioned projects are finished."),
        "lottery_title": _("Silver Mystery Canvas"),
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
        "assigned_eyebrow": _("Panda priority"),
        "assigned_title": _("Today's bamboo tasks"),
        "assigned_help": _("Help the panda finish every task before bedtime at midnight."),
        "assigned_complete": _("Task finished"),
        "assigned_reward_block": _("The treat chest opens after today's bamboo tasks are finished."),
        "lottery_title": _("Bamboo Surprise"),
    },
    "blockville": {
        "submit": _("Complete challenge"),
        "task_button": _("Complete challenge"),
        "task_modal_title": _("Complete challenge"),
        "task_modal_submit": _("Complete challenge"),
        "task_photo": _("Attach Proof"),
        "pending": _("Pending Verification..."),
        "revision": _("Challenge returned: fix issues"),
        "reward": _("Claim prize"),
        "reward_pending": _("Prize requested!"),
        "proposal": _("Create a prize idea"),
        "gift": _("Send cubes to sibling"),
        "birthday": _("Annual Blockville Gift!"),
        "nav_home": _("HQ"),
        "nav_tasks": _("Block quests"),
        "nav_rewards": _("Prize shop"),
        "nav_goals": _("Building plans"),
        "nav_history": _("Mission Log"),
        "assigned_eyebrow": _("Priority challenge"),
        "assigned_title": _("Today's assigned quests"),
        "assigned_help": _("Complete every quest before the day resets at midnight."),
        "assigned_complete": _("Quest complete"),
        "assigned_reward_block": _("The prize shop unlocks after today's assigned quests are complete."),
        "lottery_title": _("Mystery Prize Crate"),
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
            "blockville": ("kubelis", "kubeliai", "kubelių"),
        }
        return _lithuanian_form(number, *units.get(theme, units["neutral"]))

    units = {
        "neutral": ("point", "points"),
        "block_world": ("emerald", "emeralds"),
        "magic_academy": ("galleon", "galleons"),
        "hero_hq": ("badge", "badges"),
        "art_studio": ("pearl", "pearls"),
        "panda_pet": ("bamboo", "bamboo"),
        "blockville": ("cube", "cubes"),
    }
    singular, plural = units.get(theme, units["neutral"])
    return singular if number == 1 else plural


@register.filter
def token_unit(value, currency_name="Points"):
    """Backward-compatible alias for the neutral point unit."""
    return currency_unit(value, "neutral")
