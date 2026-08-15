import base64
import binascii
import hashlib
import ipaddress
import re
import secrets
from datetime import time as dt_time
from datetime import timedelta
from typing import ClassVar
from urllib.parse import urlsplit

from asgiref.local import Local
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from .device_detection import identify_device
from .net import require_global_destination

_family_settings_cache = Local()

DEVICE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PARENT_PUSH_SUBSCRIPTION_LIMIT = 10
CHILD_PUSH_SUBSCRIPTION_LIMIT = 5
PUSH_ENDPOINT_MAX_LENGTH = 2048
PUSH_KEY_MAX_LENGTH = 128


def _decode_web_push_key(value, *, expected_length, field_name):
    if not isinstance(value, str) or not value or len(value) > PUSH_KEY_MAX_LENGTH:
        raise ValidationError({field_name: _("The Web Push key is invalid.")})
    if "=" in value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValidationError({field_name: _("The Web Push key is invalid.")})
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, binascii.Error) as exc:
        raise ValidationError({field_name: _("The Web Push key is invalid.")}) from exc
    if len(decoded) != expected_length:
        raise ValidationError({field_name: _("The Web Push key is invalid.")})
    return decoded


def validate_push_subscription_data(endpoint, p256dh, auth):
    """Validate browser-supplied Web Push data before it reaches the database."""

    if not isinstance(endpoint, str) or len(endpoint) > PUSH_ENDPOINT_MAX_LENGTH:
        raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")})
    try:
        parsed = urlsplit(endpoint)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")}) from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port is not None and not 1 <= port <= 65535
    ):
        raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")})

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        if not address.is_global:
            raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")})
    else:
        try:
            ascii_hostname = hostname.encode("idna").decode("ascii").lower().rstrip(".")
        except UnicodeError as exc:
            raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")}) from exc
        labels = ascii_hostname.split(".")
        if (
            len(ascii_hostname) > 253
            or any(not label or len(label) > 63 for label in labels)
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
                for label in labels
            )
            or all(label.isdigit() for label in labels)
        ):
            raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")})
        if ascii_hostname == "localhost" or ascii_hostname.endswith(
            (".localhost", ".local", ".internal", ".home.arpa")
        ):
            raise ValidationError({"endpoint": _("The Web Push endpoint is invalid.")})
        try:
            require_global_destination(ascii_hostname, port or 443)
        except ValueError as exc:
            raise ValidationError(
                {"endpoint": _("The Web Push endpoint is invalid.")}
            ) from exc

    public_key = _decode_web_push_key(
        p256dh,
        expected_length=65,
        field_name="p256dh",
    )
    if not public_key.startswith(b"\x04"):
        raise ValidationError({"p256dh": _("The Web Push key is invalid.")})
    _decode_web_push_key(auth, expected_length=16, field_name="auth")
    return endpoint, p256dh, auth


def generate_device_code():
    return "".join(secrets.choice(DEVICE_CODE_ALPHABET) for _ in range(6))


class FamilySettings(models.Model):
    class NetworkAccessMode(models.TextChoices):
        OPEN = "open", _("Internet access")
        CHILDREN = "children", _("Restrict child access")
        ALL = "all", _("Restrict all access")

    class EvidenceRetention(models.IntegerChoices):
        FOREVER = 0, _("Keep indefinitely")
        SEVEN_DAYS = 7, _("7 days")
        THIRTY_DAYS = 30, _("30 days")
        NINETY_DAYS = 90, _("90 days")

    family_name = models.CharField(max_length=80, blank=True, default="")
    currency_name = models.CharField(max_length=32, default="Points")
    default_min_balance = models.IntegerField(default=-100)
    photo_bonus_points = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(10000)],
    )
    birthday_points = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(10000)],
    )
    lottery_enabled = models.BooleanField(default=True)
    lottery_ticket_cost = models.PositiveSmallIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
    )
    lottery_weekly_limit = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    evidence_retention_days = models.PositiveSmallIntegerField(
        choices=EvidenceRetention.choices,
        default=EvidenceRetention.THIRTY_DAYS,
    )
    feedback_screenshot_retention_days = models.PositiveSmallIntegerField(
        choices=EvidenceRetention.choices,
        default=EvidenceRetention.NINETY_DAYS,
    )
    network_access_mode = models.CharField(
        max_length=16,
        choices=NetworkAccessMode.choices,
        default=NetworkAccessMode.OPEN,
    )
    allowed_networks = models.TextField(blank=True, default="")
    recovery_code_hash = models.CharField(max_length=255, blank=True)
    setup_completed_at = models.DateTimeField(null=True, blank=True)
    default_language = models.CharField(max_length=8, blank=True, default="")
    timezone_name = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = _("family settings")
        verbose_name_plural = _("family settings")

    def save(self, *args, **kwargs):
        self.pk = 1
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and not type(self).objects.filter(pk=1).exists():
            # Avoid update_fields against a missing singleton (stale request-local
            # instance after a rolled-back transaction, or first insert).
            kwargs = {
                key: value
                for key, value in kwargs.items()
                if key not in {"update_fields", "force_update"}
            }
            self._state.adding = True
        super().save(*args, **kwargs)
        if getattr(_family_settings_cache, "active", False):
            _family_settings_cache.instance = self

    @classmethod
    def load(cls):
        if getattr(_family_settings_cache, "active", False):
            cached = getattr(_family_settings_cache, "instance", None)
            if cached is not None:
                return cached
        instance, _ = cls.objects.get_or_create(pk=1)
        if getattr(_family_settings_cache, "active", False):
            _family_settings_cache.instance = instance
        return instance

    @classmethod
    def clear_load_cache(cls):
        if hasattr(_family_settings_cache, "instance"):
            del _family_settings_cache.instance

    @classmethod
    def activate_load_cache(cls):
        cls.clear_load_cache()
        _family_settings_cache.active = True

    @classmethod
    def deactivate_load_cache(cls):
        cls.clear_load_cache()
        _family_settings_cache.active = False

    @property
    def display_name(self):
        return f"{self.family_name.strip()} {str(_('Family'))}".strip()

    @property
    def header_name(self):
        return f"{self.family_name.strip()} {str(_('family'))}".strip()


class Theme(models.TextChoices):
    NEUTRAL = "neutral", _("Neutral")
    MAGIC_ACADEMY = "magic_academy", _("Magic Academy")
    BLOCK_WORLD = "block_world", _("Block World")
    HERO_HQ = "hero_hq", _("Superhero HQ")
    ART_STUDIO = "art_studio", _("Art Studio")
    PANDA_PET = "panda_pet", _("Panda World")
    BLOCKVILLE = "blockville", _("Blockville World")


class BackupAuditEvent(models.Model):
    class Action(models.TextChoices):
        CONFIGURED = "configured", _("Backup settings configured")
        MANUAL_RUN = "manual_run", _("Manual backup requested")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="backup_audit_events",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    provider = models.CharField(max_length=32, blank=True)
    target = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class DeviceToken(models.Model):
    class Kind(models.TextChoices):
        PHONE = "phone", _("Phone")
        TABLET = "tablet", _("Tablet")
        COMPUTER = "computer", _("Computer")
        UNKNOWN = "unknown", _("Unknown device")

    token_hash = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=80, blank=True)
    device_code = models.CharField(max_length=6, unique=True, blank=True, editable=False)
    device_kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        default=Kind.UNKNOWN,
    )
    device_platform = models.CharField(max_length=16, default="unknown")
    device_browser = models.CharField(max_length=16, default="unknown")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="paired_devices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    @staticmethod
    def digest(raw_token):
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, *, created_by, label="", user_agent=""):
        raw_token = secrets.token_urlsafe(32)
        profile = identify_device(user_agent)
        device_code = generate_device_code()
        while cls.objects.filter(device_code=device_code).exists():
            device_code = generate_device_code()
        instance = cls.objects.create(
            token_hash=cls.digest(raw_token),
            label=label.strip()[:80],
            device_code=device_code,
            device_kind=profile.kind,
            device_platform=profile.platform,
            device_browser=profile.browser,
            created_by=created_by,
        )
        return instance, raw_token

    @property
    def device_icon(self):
        return {
            self.Kind.PHONE: "icon-mobile-screen-button",
            self.Kind.TABLET: "icon-tablet-screen-button",
            self.Kind.COMPUTER: "icon-desktop",
            self.Kind.UNKNOWN: "icon-circle-info",
        }.get(self.device_kind, "icon-circle-info")

    @property
    def device_summary(self):
        device_names = {
            (self.Kind.PHONE, "ios"): _("iPhone"),
            (self.Kind.PHONE, "android"): _("Android phone"),
            (self.Kind.PHONE, "windows"): _("Windows phone"),
            (self.Kind.TABLET, "ios"): _("iPad"),
            (self.Kind.TABLET, "android"): _("Android tablet"),
            (self.Kind.COMPUTER, "macos"): _("Mac"),
            (self.Kind.COMPUTER, "windows"): _("Windows PC"),
            (self.Kind.COMPUTER, "linux"): _("Linux PC"),
        }
        name = device_names.get(
            (self.device_kind, self.device_platform),
            self.get_device_kind_display(),
        )
        browser_names = {
            "chrome": "Chrome",
            "edge": "Edge",
            "firefox": "Firefox",
            "opera": "Opera",
            "safari": "Safari",
        }
        browser = browser_names.get(self.device_browser)
        return f"{name} · {browser}" if browser else str(name)

    @property
    def display_name(self):
        return self.label or self.device_summary

    @property
    def last_seen_at(self):
        return self.last_used_at or self.created_at

    @property
    def is_inactive(self):
        return self.last_seen_at < timezone.now() - timedelta(days=30)

    @property
    def is_revoked(self):
        return self.revoked_at is not None


class DevicePairingLink(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_pairing_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    @classmethod
    def issue(cls, *, created_by, lifetime=timedelta(minutes=10)):
        raw_token = secrets.token_urlsafe(32)
        instance = cls.objects.create(
            token_hash=DeviceToken.digest(raw_token),
            created_by=created_by,
            expires_at=timezone.now() + lifetime,
        )
        return instance, raw_token


class AttemptCounter(models.Model):
    class Scope(models.TextChoices):
        CHILD_PIN_DEVICE = "child_pin_device", _("Child PIN by device")
        CHILD_PIN_PROFILE = "child_pin_profile", _("Child PIN by profile")
        CHILD_PIN_IP = "child_pin_ip", _("Child PIN by IP")
        CHILD_PIN_SITE = "child_pin_site", _("Child PIN site-wide")
        PARENT_LOGIN_IP = "parent_login_ip", _("Parent login by IP")
        PARENT_LOGIN_ACCOUNT = "parent_login_account", _("Parent login by account")
        PASSWORD_RESET_IP = "password_reset_ip", _("Password reset by IP")
        PASSWORD_RESET_ACCOUNT = "password_reset_account", _("Password reset by account")
        DEVICE_PAIRING = "device_pairing", _("Device pairing")
        ADMIN_LOGIN_IP = "admin_login_ip", _("Admin login by IP")
        SETUP_CLAIM_IP = "setup_claim_ip", _("Initial setup by IP")
        CAREGIVER_INVITE_IP = "caregiver_invite_ip", _("Caregiver invite by IP")
        CAREGIVER_INVITE_PARENT = "caregiver_invite_parent", _("Caregiver invite by parent")
        CAREGIVER_PIN_PROFILE = "caregiver_pin_profile", _("Caregiver PIN by profile")
        CAREGIVER_PIN_IP = "caregiver_pin_ip", _("Caregiver PIN by IP")

    scope = models.CharField(max_length=32, choices=Scope.choices)
    key_hash = models.CharField(max_length=64)
    window_start = models.DateTimeField()
    count = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scope", "key_hash", "window_start"],
                name="uniq_attempt_counter_window",
            )
        ]
        indexes = [models.Index(fields=["scope", "key_hash"])]


class SecurityAuditEvent(models.Model):
    class Action(models.TextChoices):
        DEVICE_PAIRED = "device_paired", _("Child device paired")
        DEVICE_REVOKED = "device_revoked", _("Child device revoked")
        ALL_DEVICES_REVOKED = "all_devices_revoked", _("All child devices revoked")
        NETWORK_POLICY_CHANGED = "network_policy_changed", _("Network access changed")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="security_audit_events",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    detail = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class ChildProfile(models.Model):
    name = models.CharField(max_length=80, unique=True)
    vocative_name = models.CharField(max_length=80, blank=True)
    theme = models.CharField(max_length=32, choices=Theme.choices, default=Theme.NEUTRAL)
    theme_selected = models.BooleanField(default=False)
    randomize_theme_daily = models.BooleanField(default=False)
    theme_randomized_on = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    birth_date_initialized = models.BooleanField(default=False)
    pin_hash = models.CharField(max_length=255)
    balance = models.IntegerField(default=0)
    min_balance = models.IntegerField(default=-100)
    lottery_enabled = models.BooleanField(default=True)
    failed_pin_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def address_name(self):
        if get_language() != "lt":
            return self.name.strip()
        if self.vocative_name.strip():
            return self.vocative_name.strip()
        name = self.name.strip()
        lower_name = name.lower()
        endings = (
            ("ius", "iau"),
            ("as", "ai"),
            ("is", "i"),
            ("ys", "y"),
            ("us", "au"),
        )
        for ending, replacement in endings:
            if lower_name.endswith(ending):
                return name[: -len(ending)] + replacement
        return name

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def set_pin(self, raw_pin):
        if not (raw_pin.isdigit() and len(raw_pin) == 4):
            raise ValidationError(_("The PIN must contain exactly 4 digits."))
        self.pin_hash = make_password(raw_pin)

    def verify_pin(self, raw_pin):
        if self.is_locked:
            return False
        if check_password(raw_pin, self.pin_hash):
            self.failed_pin_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_pin_attempts", "locked_until"])
            return True
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=5)
            self.failed_pin_attempts = 0
        self.save(update_fields=["failed_pin_attempts", "locked_until"])
        return False


EMOJI_SUGGESTIONS = [
    "⭐", "✨", "🧹", "📚", "🛏️", "🍽️", "🐾", "🎓",
    "📱", "🎁", "🧸", "🎮", "⚽", "🏀", "🚲", "🎨",
    "🎵", "🧩", "🧼", "🧺", "🗑️", "🌱", "🍎", "🏆",
]


class CatalogBase(models.Model):
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=32, default="⭐")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class Task(CatalogBase):
    reward = models.PositiveIntegerField()


class PenaltyTemplate(CatalogBase):
    amount = models.IntegerField(validators=[MaxValueValidator(-1)])


class Reward(CatalogBase):
    cost = models.PositiveIntegerField()


class RequestStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    NEEDS_CHANGES = "needs_changes", _("Needs changes")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")
    CANCELLED = "cancelled", _("Cancelled")


class TaskClaim(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.PROTECT, related_name="task_claims")
    task = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="claims")
    task_title = models.CharField(max_length=120)
    reward_snapshot = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    rejection_reason = models.TextField(blank=True)
    revision_note = models.TextField(blank=True)
    child_note = models.CharField(max_length=200, blank=True, default="")
    evidence_image = models.ImageField(upload_to="task-evidence/full/%Y/%m/", blank=True)
    evidence_thumbnail = models.ImageField(
        upload_to="task-evidence/thumbnails/%Y/%m/",
        blank=True,
    )
    evidence_uploaded_at = models.DateTimeField(null=True, blank=True)
    evidence_purged_at = models.DateTimeField(null=True, blank=True)
    photo_bonus_snapshot = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_task_claims",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    child_acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["child", "task"],
                condition=Q(
                    status__in=[
                        RequestStatus.PENDING,
                        RequestStatus.NEEDS_CHANGES,
                    ]
                ),
                name="unique_pending_task_per_child",
            )
        ]

    def __str__(self):
        return f"{self.child}: {self.task_title}"

    @property
    def total_reward(self):
        return self.reward_snapshot + self.photo_bonus_snapshot

    @property
    def has_evidence(self):
        return bool(self.evidence_image and self.evidence_thumbnail)


class AssignedTaskBatch(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="assigned_task_batches",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_task_batches",
    )
    blocks_rewards = models.BooleanField(default=False)
    assigned_on = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    nudge_at = models.DateTimeField(null=True, blank=True)
    nudge_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar = ["-created_at", "-pk"]


class AssignedTaskStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")


class AssignedTask(models.Model):
    batch = models.ForeignKey(
        AssignedTaskBatch,
        on_delete=models.PROTECT,
        related_name="items",
    )
    task = models.ForeignKey(
        Task,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    title_snapshot = models.CharField(max_length=120)
    icon_snapshot = models.CharField(max_length=32, default="🧹")
    reward_snapshot = models.PositiveIntegerField()
    note_snapshot = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=AssignedTaskStatus.choices,
        default=AssignedTaskStatus.PENDING,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cancelled_assigned_tasks",
    )
    ledger_entry = models.OneToOneField(
        "LedgerEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assigned_task",
    )

    class Meta:
        ordering: ClassVar = ["pk"]

    @property
    def is_expired(self):
        return (
            self.status == AssignedTaskStatus.PENDING
            and self.batch.assigned_on < timezone.localdate()
        )


class AssignmentPresetCadence(models.TextChoices):
    DAILY = "daily", _("Every day")
    WEEKDAYS = "weekdays", _("Chosen weekdays")
    WEEKEND = "weekend", _("Weekend")
    WEEKLY = "weekly", _("Once a week")


class AssignmentPresetWeekendMode(models.TextChoices):
    SATURDAY = "sat", _("Saturday")
    SUNDAY = "sun", _("Sunday")
    BOTH = "both", _("Saturday and Sunday")


def _default_preset_run_at():
    return dt_time(7, 0)


class AssignmentPreset(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name="assignment_presets",
    )
    name = models.CharField(max_length=80)
    blocks_rewards = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    cadence = models.CharField(
        max_length=16,
        choices=AssignmentPresetCadence.choices,
        default=AssignmentPresetCadence.DAILY,
    )
    weekday_mask = models.PositiveSmallIntegerField(default=0)
    weekend_mode = models.CharField(
        max_length=8,
        choices=AssignmentPresetWeekendMode.choices,
        default=AssignmentPresetWeekendMode.BOTH,
        blank=True,
    )
    weekly_weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    run_at = models.TimeField(default=_default_preset_run_at)
    last_auto_assigned_on = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assignment_presets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["name", "pk"]

    def __str__(self):
        return f"{self.child}: {self.name}"


class AssignmentPresetItem(models.Model):
    preset = models.ForeignKey(
        AssignmentPreset,
        on_delete=models.CASCADE,
        related_name="items",
    )
    task = models.ForeignKey(
        Task,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assignment_preset_items",
    )
    custom_title = models.CharField(max_length=120, blank=True, default="")
    custom_points = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering: ClassVar = ["sort_order", "pk"]


class TaskCompletion(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="task_completions",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="completions",
    )
    completed_on = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar = ["-created_at", "-pk"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["child", "task", "completed_on"],
                name="unique_task_completion_per_child_day",
            )
        ]


class RewardRequest(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.PROTECT, related_name="reward_requests")
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name="requests")
    reward_title = models.CharField(max_length=120)
    cost_snapshot = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    rejection_reason = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_reward_requests",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["child", "reward"],
                condition=Q(status=RequestStatus.PENDING),
                name="unique_pending_reward_per_child",
            )
        ]


class GoalMode(models.TextChoices):
    AVAILABLE = "available", _("Current goal")
    SAVED = "saved", _("Saved")


class ProposalType(models.TextChoices):
    REWARD = "reward", _("Reward")
    GOAL = "goal", _("Savings goal")


class Proposal(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="proposals")
    proposal_type = models.CharField(max_length=16, choices=ProposalType.choices)
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=32, default="⭐")
    suggested_cost = models.PositiveIntegerField(null=True, blank=True)
    goal_mode = models.CharField(
        max_length=16,
        choices=GoalMode.choices,
        null=True,
        blank=True,
    )
    final_cost = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    parent_note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_proposals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class GoalStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")


class SavingsGoal(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=32, default="⭐")
    target_amount = models.PositiveIntegerField()
    mode = models.CharField(
        max_length=16,
        choices=GoalMode.choices,
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=16, choices=GoalStatus.choices, default=GoalStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(target_amount__gt=0),
                name="savings_goal_positive_target",
            ),
            models.UniqueConstraint(
                fields=["child"],
                condition=Q(status=GoalStatus.ACTIVE, mode=GoalMode.AVAILABLE),
                name="one_current_goal_per_child",
            ),
        ]

    @property
    def saved_amount(self):
        annotated = getattr(self, "_saved_amount", None)
        if annotated is not None:
            return max(0, int(annotated))
        return sum(
            contribution.amount
            for contribution in self.contributions.filter(
                state=SavingsContributionState.ACTIVE
            )
        )

    @property
    def progress_amount(self):
        if self.mode == GoalMode.SAVED:
            return min(self.target_amount, self.saved_amount)
        if self.mode == GoalMode.AVAILABLE:
            return min(self.target_amount, max(0, self.child.balance))
        return 0

    @property
    def is_reached(self):
        return self.progress_amount >= self.target_amount

    @property
    def progress_percent(self):
        if self.target_amount <= 0:
            return 100
        return max(0, min(100, round(self.progress_amount / self.target_amount * 100)))


class SavingsContributionState(models.TextChoices):
    ACTIVE = "active", _("Saved")
    RETURNED = "returned", _("Returned")
    CONSUMED = "consumed", _("Used")


class SavingsContribution(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.PROTECT,
        related_name="contributions",
    )
    amount = models.PositiveIntegerField()
    state = models.CharField(
        max_length=16,
        choices=SavingsContributionState.choices,
        default=SavingsContributionState.ACTIVE,
    )
    ledger_entry = models.OneToOneField(
        "LedgerEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="savings_contribution",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="savings_contribution_positive_amount",
            )
        ]
        indexes = [
            models.Index(
                fields=["goal", "state"],
                name="savings_contrib_goal_state_idx",
            )
        ]


class GoalActivityType(models.TextChoices):
    CREATED = "created", _("Goal created")
    MODE_SELECTED = "mode_selected", _("Savings mode selected")
    CURRENT_CHANGED = "current_changed", _("Current goal changed")
    TRANSFERRED = "transferred", _("Points saved to goal")
    RETURNED = "returned", _("Points returned from goal")
    REACHED = "reached", _("Goal reached")
    COMPLETED = "completed", _("Goal completed")
    CLOSED = "closed", _("Goal closed")


class SavingsGoalEvent(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.PROTECT,
        related_name="events",
    )
    event_type = models.CharField(max_length=24, choices=GoalActivityType.choices)
    description = models.CharField(max_length=240)
    amount = models.PositiveIntegerField(null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="savings_goal_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class GoalCompletionRequest(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.PROTECT,
        related_name="completion_requests",
    )
    status = models.CharField(
        max_length=16,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_goal_completion_requests",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["requested_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["goal"],
                condition=Q(status=RequestStatus.PENDING),
                name="one_pending_goal_completion_per_goal",
            )
        ]


class LedgerKind(models.TextChoices):
    TASK = "task", _("Task")
    ASSIGNED_TASK = "assigned_task", _("Assigned task")
    PENALTY = "penalty", _("Penalty")
    REWARD = "reward", _("Reward")
    LOTTERY = "lottery", _("Surprise card")
    ADJUSTMENT = "adjustment", _("Adjustment")
    GIFT = "gift", _("Gift")
    BIRTHDAY = "birthday", _("Birthday")
    SAVINGS_TRANSFER = "savings_transfer", _("Saved to goal")
    SAVINGS_RETURN = "savings_return", _("Returned from goal")
    GOAL_COMPLETION = "goal_completion", _("Goal completion")


class LedgerEntry(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.PROTECT, related_name="ledger_entries")
    delta = models.IntegerField()
    balance_after = models.IntegerField()
    kind = models.CharField(max_length=16, choices=LedgerKind.choices)
    description = models.CharField(max_length=240)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(_("Point transactions cannot be changed."))
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("Point transactions cannot be deleted."))


class LotteryTicketStatus(models.TextChoices):
    OPEN = "open", _("Open")
    REVEALED = "revealed", _("Revealed")


class LotteryTicket(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="lottery_tickets",
    )
    week_start = models.DateField()
    values = models.JSONField()
    prize_amount = models.IntegerField()
    applied_delta = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=LotteryTicketStatus.choices,
        default=LotteryTicketStatus.OPEN,
    )
    purchase_ledger_entry = models.OneToOneField(
        LedgerEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="lottery_ticket_purchase",
    )
    result_ledger_entry = models.OneToOneField(
        LedgerEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="lottery_ticket_result",
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    revealed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar = ["-purchased_at", "-pk"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["child"],
                condition=Q(status=LotteryTicketStatus.OPEN),
                name="one_open_lottery_ticket_per_child",
            )
        ]
        indexes: ClassVar = [
            models.Index(
                fields=["child", "week_start"],
                name="lottery_child_week_idx",
            )
        ]


class LotteryReminder(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name="lottery_reminders",
    )
    week_start = models.DateField()
    scheduled_for = models.DateTimeField()
    handled_at = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    class Meta:
        ordering: ClassVar = ["-week_start", "-pk"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["child", "week_start"],
                name="one_lottery_reminder_per_child_week",
            )
        ]


class PointGift(models.Model):
    sender = models.ForeignKey(
        ChildProfile, on_delete=models.PROTECT, related_name="sent_point_gifts"
    )
    recipient = models.ForeignKey(
        ChildProfile, on_delete=models.PROTECT, related_name="received_point_gifts"
    )
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=models.F("recipient")),
                name="point_gift_different_children",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="point_gift_positive_amount",
            ),
        ]


class BirthdayAward(models.Model):
    child = models.ForeignKey(
        ChildProfile, on_delete=models.PROTECT, related_name="birthday_awards"
    )
    year = models.PositiveSmallIntegerField()
    points = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    ledger_entry = models.OneToOneField(
        LedgerEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="birthday_award",
    )
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-awarded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["child", "year"], name="one_birthday_award_per_year"
            )
        ]


class BirthDateChangeRequest(models.Model):
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="birth_date_change_requests",
    )
    previous_birth_date = models.DateField(null=True, blank=True)
    requested_birth_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_birth_date_changes",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["child"],
                condition=Q(status=RequestStatus.PENDING),
                name="one_pending_birth_date_change_per_child",
            )
        ]


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    child = models.ForeignKey(
        ChildProfile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    device = models.ForeignKey(
        DeviceToken,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.CharField(max_length=PUSH_ENDPOINT_MAX_LENGTH, unique=True)
    p256dh = models.CharField(max_length=PUSH_KEY_MAX_LENGTH)
    auth = models.CharField(max_length=PUSH_KEY_MAX_LENGTH)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(user__isnull=False, child__isnull=True, device__isnull=True)
                    | Q(user__isnull=True, child__isnull=False, device__isnull=False)
                ),
                name="push_subscription_has_one_owner",
            )
        ]

    def clean(self):
        super().clean()
        validate_push_subscription_data(self.endpoint, self.p256dh, self.auth)


class FeedbackType(models.TextChoices):
    BUG = "bug", _("Problem")
    IDEA = "idea", _("Suggestion")


class FeedbackStatus(models.TextChoices):
    NEW = "new", _("New")
    REVIEWED = "reviewed", _("Reviewed")
    PLANNED = "planned", _("Planned")
    RESOLVED = "resolved", _("Resolved")


class FeedbackReport(models.Model):
    report_type = models.CharField(
        max_length=12,
        choices=FeedbackType.choices,
        default=FeedbackType.BUG,
    )
    status = models.CharField(
        max_length=12,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.NEW,
    )
    description = models.TextField(max_length=2000)
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback_reports",
    )
    child = models.ForeignKey(
        ChildProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback_reports",
    )
    reporter_name = models.CharField(max_length=150)
    reporter_role = models.CharField(max_length=12)
    family_name = models.CharField(max_length=80, blank=True)
    page_path = models.CharField(max_length=500, blank=True)
    app_version = models.CharField(max_length=32)
    language = models.CharField(max_length=16, blank=True)
    theme = models.CharField(max_length=32, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    screenshot = models.ImageField(
        upload_to="feedback/screenshots/%Y/%m/",
        blank=True,
    )
    screenshot_purged_at = models.DateTimeField(null=True, blank=True)
    email_notified_at = models.DateTimeField(null=True, blank=True)
    email_error = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(parent__isnull=False, child__isnull=True)
                    | Q(parent__isnull=True, child__isnull=False)
                ),
                name="feedback_report_has_one_reporter",
            )
        ]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["report_type", "-created_at"]),
        ]


CAREGIVER_INVITE_LIFETIME = timedelta(hours=6)
CAREGIVER_LOGIN_CODE_LENGTH = 8


def _generate_caregiver_login_code():
    return "".join(
        secrets.choice(DEVICE_CODE_ALPHABET) for _ in range(CAREGIVER_LOGIN_CODE_LENGTH)
    )


class CaregiverInvite(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=80)
    email = models.EmailField(blank=True)
    access_until = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caregiver_invites",
    )
    children = models.ManyToManyField(
        "ChildProfile",
        related_name="caregiver_invites",
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    caregiver = models.ForeignKey(
        "CaregiverProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invites",
    )

    class Meta:
        ordering = ["-created_at", "-pk"]

    @property
    def is_pending(self):
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
        )

    @classmethod
    def issue(cls, *, created_by, label, access_until, children, email=""):
        raw_token = secrets.token_urlsafe(32)
        instance = cls.objects.create(
            token_hash=DeviceToken.digest(raw_token),
            label=label.strip(),
            email=(email or "").strip(),
            access_until=access_until,
            created_by=created_by,
            expires_at=timezone.now() + CAREGIVER_INVITE_LIFETIME,
        )
        instance.children.set(children)
        return instance, raw_token


class CaregiverProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caregiver_profile",
    )
    label = models.CharField(max_length=80)
    login_code = models.CharField(max_length=16, unique=True)
    pin_hash = models.CharField(max_length=255)
    access_until = models.DateField()
    children = models.ManyToManyField(
        "ChildProfile",
        related_name="caregivers",
        blank=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_caregivers",
    )
    failed_pin_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label", "pk"]

    def __str__(self):
        return self.label

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    @property
    def has_access(self):
        if not self.is_active:
            return False
        if not self.user_id or not self.user.is_active:
            return False
        return self.access_until >= timezone.localdate()

    def set_pin(self, raw_pin):
        if not (raw_pin.isdigit() and len(raw_pin) == 4):
            raise ValidationError(_("The PIN must contain exactly 4 digits."))
        self.pin_hash = make_password(raw_pin)

    def verify_pin(self, raw_pin):
        if self.is_locked:
            return False
        if check_password(raw_pin, self.pin_hash):
            self.failed_pin_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_pin_attempts", "locked_until"])
            return True
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=5)
            self.failed_pin_attempts = 0
        self.save(update_fields=["failed_pin_attempts", "locked_until"])
        return False

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])
        user = self.user
        if user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active"])
        PushSubscription.objects.filter(user=user).delete()

    @classmethod
    def create_from_invite(cls, *, invite, raw_pin):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        for _ in range(20):
            login_code = _generate_caregiver_login_code()
            if not cls.objects.filter(login_code=login_code).exists():
                break
        else:
            raise ValidationError(_("Could not create a guest sign-in link."))
        username = f"guest_{login_code.lower()}"
        user = User.objects.create_user(username=username)
        user.set_unusable_password()
        user.save(update_fields=["password"])
        profile = cls(
            user=user,
            label=invite.label,
            login_code=login_code,
            access_until=invite.access_until,
            created_by=invite.created_by,
        )
        profile.set_pin(raw_pin)
        profile.save()
        profile.children.set(invite.children.all())
        return profile
