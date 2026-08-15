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
        "assigned_note_label": _("Owl tip"),
        "assigned_nudge_title": _("Your enchanted duties are waiting"),
        "assigned_nudge_help": _("Finish today's list before the magic fades tonight."),
        "waiting_parents_eyebrow": _("Waiting for the professors"),
        "lottery_title": _("Enchanted Surprise"),
        "settings_eyebrow": _("Your spellbook"),
        "settings_title": _("My magic"),
        "settings_world_title": _("Choose a world"),
        "settings_world_hint": _("Tap a world. It changes colours, words, and sounds."),
        "settings_world_sub": _("Owls & galleons"),
        "settings_daily_title": _("Surprise world"),
        "settings_daily_sub": _("New every day"),
        "settings_avatar_title": _("My portrait"),
        "settings_cam": _("Take photo"),
        "settings_gal": _("From gallery"),
        "settings_bday_title": _("Birthday feast"),
        "settings_pin_title": _("Secret code"),
        "settings_pin_step_old": _("Old code"),
        "settings_pin_step_new": _("New code"),
        "settings_pin_step_repeat": _("Repeat new code"),
        "settings_pin_save": _("Save secret code"),
        "settings_cta_theme": _("Enter this world"),
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
        "assigned_note_label": _("Build tip"),
        "assigned_nudge_title": _("Your missions are still waiting"),
        "assigned_nudge_help": _("Finish today's assigned missions before midnight."),
        "waiting_parents_eyebrow": _("Waiting for the builders"),
        "lottery_title": _("Hidden Emerald Grid"),
        "settings_eyebrow": _("Your base"),
        "settings_title": _("Build my look"),
        "settings_world_title": _("Pick a biome"),
        "settings_world_hint": _("Square buttons. Big taps."),
        "settings_world_sub": _("Emeralds"),
        "settings_daily_title": _("Surprise biome"),
        "settings_daily_sub": _("New every day"),
        "settings_avatar_title": _("My skin"),
        "settings_cam": _("Camera"),
        "settings_gal": _("Gallery"),
        "settings_bday_title": _("Spawn day"),
        "settings_pin_title": _("Passcode"),
        "settings_pin_step_old": _("Old passcode"),
        "settings_pin_step_new": _("New passcode"),
        "settings_pin_step_repeat": _("Repeat new"),
        "settings_pin_save": _("Save passcode"),
        "settings_cta_theme": _("Build this world"),
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
        "assigned_note_label": _("Note from parents"),
        "assigned_nudge_title": _("Your tasks are still waiting"),
        "assigned_nudge_help": _("Finish today's assigned tasks before midnight."),
        "waiting_parents_eyebrow": _("Waiting for parents"),
        "lottery_title": _("Everyday Surprise"),
        "settings_eyebrow": _("Your profile"),
        "settings_title": _("My space"),
        "settings_world_title": _("Choose a world"),
        "settings_world_hint": _("You can switch whenever you want."),
        "settings_world_sub": _("Points"),
        "settings_daily_title": _("Surprise world"),
        "settings_daily_sub": _("New every day"),
        "settings_avatar_title": _("My photo"),
        "settings_cam": _("Take photo"),
        "settings_gal": _("Choose photo"),
        "settings_bday_title": _("Birthday"),
        "settings_pin_title": _("My PIN"),
        "settings_pin_step_old": _("Old PIN"),
        "settings_pin_step_new": _("New PIN"),
        "settings_pin_step_repeat": _("Repeat new PIN"),
        "settings_pin_save": _("Save new PIN"),
        "settings_cta_theme": _("Use this world"),
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
        "assigned_note_label": _("HQ tip"),
        "assigned_nudge_title": _("HQ is still waiting"),
        "assigned_nudge_help": _("Complete today's priority missions before midnight."),
        "waiting_parents_eyebrow": _("Waiting for HQ"),
        "lottery_title": _("Classified Surprise"),
        "settings_eyebrow": _("Hero profile"),
        "settings_title": _("HQ setup"),
        "settings_world_title": _("Select HQ theme"),
        "settings_world_hint": _("Big comic cards. One tap."),
        "settings_world_sub": _("Badges"),
        "settings_daily_title": _("Surprise HQ"),
        "settings_daily_sub": _("New each day"),
        "settings_avatar_title": _("Hero portrait"),
        "settings_cam": _("Snap"),
        "settings_gal": _("Files"),
        "settings_bday_title": _("Origin day"),
        "settings_pin_title": _("Access code"),
        "settings_pin_step_old": _("Current code"),
        "settings_pin_step_new": _("New code"),
        "settings_pin_step_repeat": _("Repeat new"),
        "settings_pin_save": _("Save code"),
        "settings_cta_theme": _("Activate"),
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
        "assigned_note_label": _("Director's note"),
        "assigned_nudge_title": _("Studio projects are waiting"),
        "assigned_nudge_help": _("Finish today's commissioned projects before midnight."),
        "waiting_parents_eyebrow": _("Waiting for the director"),
        "lottery_title": _("Silver Mystery Canvas"),
        "settings_eyebrow": _("My studio"),
        "settings_title": _("Make it mine"),
        "settings_world_title": _("Pick a mood"),
        "settings_world_hint": _("Organic cards — like paint swatches."),
        "settings_world_sub": _("Pearls"),
        "settings_daily_title": _("Surprise mood"),
        "settings_daily_sub": _("New each morning"),
        "settings_avatar_title": _("Self-portrait"),
        "settings_cam": _("Camera"),
        "settings_gal": _("Photos"),
        "settings_bday_title": _("Celebration day"),
        "settings_pin_title": _("Private sketch code"),
        "settings_pin_step_old": _("Old code"),
        "settings_pin_step_new": _("New code"),
        "settings_pin_step_repeat": _("Repeat new"),
        "settings_pin_save": _("Save sketch code"),
        "settings_cta_theme": _("Paint this world"),
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
        "assigned_note_label": _("Panda tip"),
        "assigned_nudge_title": _("The panda is still waiting"),
        "assigned_nudge_help": _("Finish today's bamboo tasks before bedtime."),
        "waiting_parents_eyebrow": _("Waiting for the panda keepers"),
        "lottery_title": _("Bamboo Surprise"),
        "settings_eyebrow": _("Panda den"),
        "settings_title": _("My cozy den"),
        "settings_world_title": _("Visit a world"),
        "settings_world_hint": _("Round cards — easy for little fingers."),
        "settings_world_sub": _("Bamboo"),
        "settings_daily_title": _("Surprise world"),
        "settings_daily_sub": _("Wake up new"),
        "settings_avatar_title": _("My panda face"),
        "settings_cam": _("Say cheese"),
        "settings_gal": _("Pick photo"),
        "settings_bday_title": _("Cake day"),
        "settings_pin_title": _("Secret bamboo code"),
        "settings_pin_step_old": _("Old code"),
        "settings_pin_step_new": _("New code"),
        "settings_pin_step_repeat": _("Say it again"),
        "settings_pin_save": _("Save bamboo code"),
        "settings_cta_theme": _("Go to this world"),
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
        "assigned_note_label": _("Quest tip"),
        "assigned_nudge_title": _("Your quests are still waiting"),
        "assigned_nudge_help": _("Finish today's assigned quests before the day resets."),
        "waiting_parents_eyebrow": _("Waiting for verification"),
        "lottery_title": _("Mystery Crate"),
        "settings_eyebrow": _("Player pad"),
        "settings_title": _("Customize"),
        "settings_world_title": _("Select skin pack"),
        "settings_world_hint": _("Dark UI + glow — like a game menu."),
        "settings_world_sub": _("Cubes"),
        "settings_daily_title": _("Random skin"),
        "settings_daily_sub": _("Daily roll"),
        "settings_avatar_title": _("Player icon"),
        "settings_cam": _("Capture"),
        "settings_gal": _("Inventory"),
        "settings_bday_title": _("Player birthday"),
        "settings_pin_title": _("Lock code"),
        "settings_pin_step_old": _("Old lock"),
        "settings_pin_step_new": _("New lock"),
        "settings_pin_step_repeat": _("Confirm lock"),
        "settings_pin_save": _("Save lock code"),
        "settings_cta_theme": _("Equip world"),
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
