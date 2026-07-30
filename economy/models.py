from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


class FamilySettings(models.Model):
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
    evidence_retention_days = models.PositiveSmallIntegerField(
        choices=EvidenceRetention.choices,
        default=EvidenceRetention.THIRTY_DAYS,
    )
    feedback_screenshot_retention_days = models.PositiveSmallIntegerField(
        choices=EvidenceRetention.choices,
        default=EvidenceRetention.NINETY_DAYS,
    )
    recovery_code_hash = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = _("family settings")
        verbose_name_plural = _("family settings")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

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
        indexes: ClassVar = [
            models.Index(
                fields=["child", "task", "completed_on"],
                name="task_done_child_day_idx",
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


class ProposalType(models.TextChoices):
    REWARD = "reward", _("Reward")
    GOAL = "goal", _("Savings goal")


class Proposal(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="proposals")
    proposal_type = models.CharField(max_length=16, choices=ProposalType.choices)
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=32, default="⭐")
    suggested_cost = models.PositiveIntegerField(null=True, blank=True)
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
    status = models.CharField(max_length=16, choices=GoalStatus.choices, default=GoalStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "-created_at"]

    @property
    def progress_percent(self):
        if self.target_amount <= 0:
            return 100
        return max(0, min(100, round(self.child.balance / self.target_amount * 100)))


class LedgerKind(models.TextChoices):
    TASK = "task", _("Task")
    ASSIGNED_TASK = "assigned_task", _("Assigned task")
    PENALTY = "penalty", _("Penalty")
    REWARD = "reward", _("Reward")
    ADJUSTMENT = "adjustment", _("Adjustment")
    GIFT = "gift", _("Gift")
    BIRTHDAY = "birthday", _("Birthday")


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
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(user__isnull=False, child__isnull=True)
                    | Q(user__isnull=True, child__isnull=False)
                ),
                name="push_subscription_has_one_owner",
            )
        ]


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
