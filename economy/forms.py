from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from pillow_heif import register_heif_opener

from .models import (
    BirthDateChangeRequest,
    ChildProfile,
    FamilySettings,
    FeedbackReport,
    FeedbackStatus,
    PenaltyTemplate,
    Proposal,
    RequestStatus,
    Reward,
    Task,
    Theme,
)

register_heif_opener()

PASSWORD_HELP = (
    _("At least 12 characters; cannot be similar to the username, commonly used, "
      "or entirely numeric.")
)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-control")


def validate_unique_parent_email(email, exclude_pk=None):
    normalized = email.strip().lower()
    query = get_user_model().objects.filter(email__iexact=normalized, is_active=True)
    if exclude_pk is not None:
        query = query.exclude(pk=exclude_pk)
    if query.exists():
        raise forms.ValidationError(_("This email address is already in use."))
    return normalized


class EmojiFormMixin(StyledFormMixin):
    empty_icon_by_default = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "icon" in self.fields:
            self.fields["icon"].widget = forms.TextInput(
                attrs={
                    "class": "field-control emoji-input",
                    "list": "emoji-options",
                    "maxlength": "8",
                    "placeholder": _("Choose an icon"),
                    "autocomplete": "off",
                }
            )
            self.fields["icon"].help_text = _("Choose an emoji or enter one using your device keyboard.")
            instance = getattr(self, "instance", None)
            if (
                self.empty_icon_by_default
                and not self.is_bound
                and (instance is None or instance.pk is None)
            ):
                self.initial["icon"] = ""

    def clean_icon(self):
        icon = self.cleaned_data["icon"].strip()
        if not icon or len(icon) > 8 or any(ord(char) < 32 for char in icon):
            raise forms.ValidationError(_("Choose one short emoji."))
        return icon


class ChildPinForm(StyledFormMixin, forms.Form):
    child_id = forms.IntegerField(widget=forms.HiddenInput)
    pin = forms.CharField(
        label="PIN",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(
            attrs={
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError(_("The PIN must contain digits only."))
        return pin


class TaskForm(EmojiFormMixin, forms.ModelForm):
    empty_icon_by_default = True
    reward = forms.IntegerField(
        label=_("Points"),
        min_value=1,
        error_messages={"min_value": _("Enter a positive point amount.")},
    )

    class Meta:
        model = Task
        fields = ["title", "reward", "icon"]
        labels = {"title": _("Task"), "reward": _("Points"), "icon": _("Icon")}

    def clean_reward(self):
        reward = self.cleaned_data["reward"]
        if reward <= 0:
            raise forms.ValidationError(_("Enter a positive point amount."))
        return reward


class PenaltyForm(EmojiFormMixin, forms.ModelForm):
    empty_icon_by_default = True
    amount = forms.IntegerField(
        label=_("Points"),
        min_value=1,
        error_messages={"min_value": _("Enter a positive point amount.")},
    )

    class Meta:
        model = PenaltyTemplate
        fields = ["title", "amount", "icon"]
        labels = {"title": _("Penalty"), "amount": _("Points"), "icon": _("Icon")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs["min"] = 1
        instance = getattr(self, "instance", None)
        if not self.is_bound and instance is not None and instance.pk and instance.amount:
            self.initial["amount"] = abs(instance.amount)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError(_("Enter a positive point amount."))
        return -amount


class RewardForm(EmojiFormMixin, forms.ModelForm):
    empty_icon_by_default = True
    cost = forms.IntegerField(
        label=_("Points"),
        min_value=1,
        error_messages={"min_value": _("Enter a positive point amount.")},
    )

    class Meta:
        model = Reward
        fields = ["title", "cost", "icon"]
        labels = {"title": _("Reward"), "cost": _("Points"), "icon": _("Icon")}

    def clean_cost(self):
        cost = self.cleaned_data["cost"]
        if cost <= 0:
            raise forms.ValidationError(_("Enter a positive point amount."))
        return cost


class ProposalForm(EmojiFormMixin, forms.ModelForm):
    empty_icon_by_default = True

    class Meta:
        model = Proposal
        fields = ["proposal_type", "title", "suggested_cost", "icon"]
        labels = {
            "proposal_type": _("Type"),
            "title": _("Title"),
            "suggested_cost": _("Suggested point amount"),
            "icon": _("Icon"),
        }


class AdjustmentForm(StyledFormMixin, forms.Form):
    amount = forms.IntegerField(label=_("Change"))
    description = forms.CharField(label=_("Reason"), max_length=240)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount == 0:
            raise forms.ValidationError(_("The point amount cannot be zero."))
        return amount


class ApplyPenaltyForm(StyledFormMixin, forms.Form):
    penalty_id = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(label=_("Reason"), max_length=240)


class AwardTasksForm(forms.Form):
    task_ids = forms.ModelMultipleChoiceField(
        label=_("Tasks"),
        queryset=Task.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": _("Choose at least one task.")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task_ids"].queryset = Task.objects.filter(
            is_active=True,
            is_deleted=False,
        )


class AssignTasksForm(forms.Form):
    task_ids = forms.ModelMultipleChoiceField(
        label=_("Tasks"),
        queryset=Task.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    custom_title = forms.CharField(
        label=_("Custom task"),
        max_length=120,
        required=False,
    )
    custom_points = forms.IntegerField(
        label=_("Points"),
        min_value=1,
        required=False,
    )
    blocks_rewards = forms.BooleanField(
        label=_("Block reward purchases"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task_ids"].queryset = Task.objects.filter(
            is_active=True,
            is_deleted=False,
        )

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("custom_title") or "").strip()
        points = cleaned.get("custom_points")
        if bool(title) != bool(points):
            raise forms.ValidationError(
                _("Enter both the custom task name and its point amount.")
            )
        if not cleaned.get("task_ids") and not title:
            raise forms.ValidationError(
                _("Choose at least one task or add a custom task.")
            )
        cleaned["custom_title"] = title
        return cleaned


class AssignPenaltiesForm(forms.Form):
    penalty_ids = forms.ModelMultipleChoiceField(
        label=_("Penalties"),
        queryset=PenaltyTemplate.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": _("Choose at least one penalty.")},
    )
    reason = forms.CharField(
        label=_("Shared reason"),
        max_length=240,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["penalty_ids"].queryset = PenaltyTemplate.objects.filter(
            is_active=True,
            is_deleted=False,
        )


class RejectForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(label=_("Rejection reason"), max_length=500)


class TaskDecisionCommentForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(
        label=_("Comment (optional)"),
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ApprovalCostForm(StyledFormMixin, forms.Form):
    final_cost = forms.IntegerField(label=_("Final point amount"), min_value=1)


class MinBalanceForm(StyledFormMixin, forms.Form):
    min_balance = forms.IntegerField(label=_("Minimum allowed balance"), max_value=0)


class ThemeForm(StyledFormMixin, forms.Form):
    theme = forms.ChoiceField(
        label=_("Theme"),
        choices=Theme.choices,
    )
    randomize_theme_daily = forms.BooleanField(
        label=_("Change my theme randomly every day"),
        help_text=_("A different theme will be selected automatically once a day."),
        required=False,
    )


class FirstThemeForm(StyledFormMixin, forms.Form):
    theme = forms.ChoiceField(
        label=_("Choose your world"),
        choices=[
            (Theme.MAGIC_ACADEMY, _("Magic Academy")),
            (Theme.BLOCK_WORLD, _("Block World")),
            (Theme.HERO_HQ, format_lazy("🛡️ {}", _("Superhero HQ"))),
            (Theme.ART_STUDIO, format_lazy("🎨 {}", _("Art Studio"))),
            (Theme.PANDA_PET, format_lazy("🐼 {}", _("Panda World"))),
            (Theme.BLOCKVILLE, format_lazy("◆ {}", _("Blockville World"))),
        ],
        widget=forms.RadioSelect,
    )


class ChangePinForm(StyledFormMixin, forms.Form):
    current_pin = forms.CharField(
        label=_("Current PIN"),
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )
    new_pin = forms.CharField(
        label=_("New PIN"),
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )
    confirm_pin = forms.CharField(
        label=_("Repeat new PIN"),
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )

    def clean(self):
        cleaned = super().clean()
        for field_name in ("current_pin", "new_pin", "confirm_pin"):
            value = cleaned.get(field_name, "")
            if value and not value.isdigit():
                self.add_error(field_name, _("The PIN must contain digits only."))
        if cleaned.get("new_pin") != cleaned.get("confirm_pin"):
            self.add_error("confirm_pin", _("The new PINs do not match."))
        return cleaned


class AvatarForm(StyledFormMixin, forms.Form):
    avatar = forms.ImageField(
        label=_("New avatar"),
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif"}
        ),
    )

    def clean_avatar(self):
        avatar = self.cleaned_data["avatar"]
        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_("The image cannot be larger than 5 MB."))
        image_format = getattr(getattr(avatar, "image", None), "format", "")
        if image_format not in {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}:
            raise forms.ValidationError(_("Use a JPEG, PNG, WebP, HEIC, or HEIF image."))
        return avatar


class TaskEvidenceForm(StyledFormMixin, forms.Form):
    proof = forms.ImageField(
        label=_("Task photo"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif",
                "data-evidence-input": "",
            }
        ),
    )
    remove_evidence = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def clean_proof(self):
        proof = self.cleaned_data.get("proof")
        if proof is None:
            return None
        if proof.size > 12 * 1024 * 1024:
            raise forms.ValidationError(_("The image cannot be larger than 12 MB."))
        image_format = getattr(getattr(proof, "image", None), "format", "")
        if image_format not in {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}:
            raise forms.ValidationError(_("Use a JPEG, PNG, WebP, HEIC, or HEIF image."))
        return proof


class FeedbackReportForm(StyledFormMixin, forms.ModelForm):
    screenshot = forms.ImageField(
        label=_("Screenshot"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif",
            }
        ),
    )

    class Meta:
        model = FeedbackReport
        fields = ["report_type", "description", "screenshot"]
        labels = {
            "report_type": _("Type"),
            "description": _("Description"),
            "screenshot": _("Screenshot"),
        }
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5, "maxlength": 2000}
            )
        }

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 5:
            raise forms.ValidationError(
                _("Describe the problem or suggestion in a little more detail.")
            )
        return description

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get("screenshot")
        if screenshot is None:
            return None
        if screenshot.size > 12 * 1024 * 1024:
            raise forms.ValidationError(_("The image cannot be larger than 12 MB."))
        image_format = getattr(getattr(screenshot, "image", None), "format", "")
        if image_format not in {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}:
            raise forms.ValidationError(_("Use a JPEG, PNG, WebP, HEIC, or HEIF image."))
        return screenshot


class FeedbackStatusForm(StyledFormMixin, forms.Form):
    status = forms.ChoiceField(
        label=_("Status"),
        choices=FeedbackStatus.choices,
    )


class FamilyPreferencesForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FamilySettings
        fields = [
            "family_name",
            "photo_bonus_points",
            "birthday_points",
            "evidence_retention_days",
            "feedback_screenshot_retention_days",
        ]
        labels = {
            "family_name": _("Family name"),
            "photo_bonus_points": _("Points for a task photo"),
            "birthday_points": _("Birthday points"),
            "evidence_retention_days": _("Keep task photos for"),
            "feedback_screenshot_retention_days": _("Keep feedback images for"),
        }
        help_texts = {
            "family_name": _("Shown in family-facing headings and messages."),
            "photo_bonus_points": _(
                "Use 0 to disable the photo bonus. The value is captured when a task is submitted."
            ),
            "birthday_points": _(
                "Each child receives this many points once a year on their birthday. Use 0 to disable birthday gifts."
            ),
            "evidence_retention_days": _(
                "Pending and revision-requested task photos are never removed."
            ),
            "feedback_screenshot_retention_days": _(
                "Only screenshots from resolved feedback are removed automatically."
            ),
        }


class BackupSettingsForm(StyledFormMixin, forms.Form):
    provider = forms.ChoiceField(
        label=_("Storage provider"),
        choices=[
            ("backblaze_s3", _("Backblaze B2 (recommended)")),
            ("s3", _("S3-compatible storage")),
        ],
    )
    endpoint = forms.CharField(
        label=_("S3 endpoint"),
        max_length=255,
        help_text=_("For example: s3.eu-central-003.backblazeb2.com"),
    )
    bucket = forms.CharField(label=_("Bucket name"), max_length=128)
    region = forms.CharField(
        label=_("Region"),
        max_length=64,
        required=False,
        help_text=_("Optional for providers that do not require a region."),
    )
    access_key_id = forms.CharField(label=_("Application key ID"), max_length=255)
    secret_access_key = forms.CharField(
        label=_("Application key"),
        max_length=512,
        widget=forms.PasswordInput(render_value=False),
    )
    current_password = forms.CharField(
        label=_("Your account password"),
        widget=forms.PasswordInput(render_value=False),
        help_text=_("Required before changing backup credentials."),
    )

    def clean_endpoint(self):
        return self.cleaned_data["endpoint"].strip().removeprefix("https://").rstrip("/")

    def clean_bucket(self):
        bucket = self.cleaned_data["bucket"].strip().strip("/")
        if "/" in bucket or any(character.isspace() for character in bucket):
            raise forms.ValidationError(_("Enter a valid bucket name."))
        return bucket


class SmtpSettingsForm(StyledFormMixin, forms.Form):
    enabled = forms.BooleanField(label=_("Enable email"), required=False)
    host = forms.CharField(label=_("SMTP server"), max_length=255)
    port = forms.IntegerField(label=_("SMTP port"), min_value=1, max_value=65535)
    security = forms.ChoiceField(
        label=_("Encryption"),
        choices=[
            ("tls", _("STARTTLS")),
            ("ssl", _("SSL/TLS")),
            ("none", _("None")),
        ],
    )
    username = forms.CharField(label=_("SMTP username"), max_length=255)
    password = forms.CharField(
        label=_("SMTP password"),
        max_length=512,
        widget=forms.PasswordInput(render_value=False),
        help_text=_("Enter the SMTP password again whenever you save these settings."),
    )
    from_email = forms.EmailField(label=_("Sender email address"))
    feedback_email = forms.EmailField(label=_("Feedback recipient email address"))
    current_password = forms.CharField(
        label=_("Your account password"),
        widget=forms.PasswordInput(render_value=False),
        help_text=_("Required before changing sensitive email settings."),
    )


class BirthDateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ChildProfile
        fields = ["birth_date"]
        labels = {"birth_date": _("Birthday")}
        widgets = {
            "birth_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            )
        }
        help_texts = {
            "birth_date": _("Used only to award the yearly birthday gift.")
        }


class PointGiftForm(StyledFormMixin, forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=ChildProfile.objects.none(),
        label=_("Recipient"),
    )
    amount = forms.IntegerField(label=_("Points to give"), min_value=1)

    def __init__(self, *args, sender, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.fields["recipient"].queryset = ChildProfile.objects.filter(
            is_active=True
        ).exclude(pk=sender.pk)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        available = max(self.sender.balance, 0)
        if amount > available:
            raise forms.ValidationError(
                _("You can give only points you have already earned.")
            )
        return amount


class ParentAccountForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(label=_("Email address"))

    class Meta:
        model = get_user_model()
        fields = ("username", "email")
        labels = {"username": _("Username"), "email": _("Email address")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = (
            _("Up to 150 characters. Letters, numbers, and @ . + - _ are allowed.")
        )
        self.fields["password1"].label = _("Password")
        self.fields["password1"].help_text = PASSWORD_HELP
        self.fields["password2"].label = _("Repeat password")
        self.fields["password2"].help_text = _("Enter the same password again.")

    def clean_email(self):
        return validate_unique_parent_email(self.cleaned_data["email"])


class ParentEditForm(StyledFormMixin, forms.Form):
    username = forms.CharField(label=_("Username"), max_length=150)
    email = forms.EmailField(
        label=_("Email address"),
        help_text=_("The password reset link will be sent to this address."),
    )
    new_password = forms.CharField(
        label=_("New password"),
        required=False,
        widget=forms.PasswordInput(),
        help_text=format_lazy(
            "{} {}",
            PASSWORD_HELP,
            _("Leave blank to keep the current password."),
        ),
    )
    confirm_password = forms.CharField(
        label=_("Repeat new password"),
        required=False,
        widget=forms.PasswordInput(),
    )

    def __init__(self, *args, account, **kwargs):
        self.account = account
        kwargs.setdefault("initial", {"username": account.username, "email": account.email})
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if (
            get_user_model()
            .objects.filter(username__iexact=username)
            .exclude(pk=self.account.pk)
            .exists()
        ):
            raise forms.ValidationError(_("This username is already in use."))
        return username

    def clean_email(self):
        return validate_unique_parent_email(
            self.cleaned_data["email"],
            exclude_pk=self.account.pk,
        )

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("new_password", "")
        confirmation = cleaned.get("confirm_password", "")
        if password != confirmation:
            self.add_error("confirm_password", _("The passwords do not match."))
        if password:
            try:
                password_validation.validate_password(password, user=self.account)
            except ValidationError:
                self.add_error("new_password", _("The password does not meet the security requirements."))
        return cleaned

    def save(self):
        self.account.username = self.cleaned_data["username"]
        self.account.email = self.cleaned_data["email"]
        if self.cleaned_data["new_password"]:
            self.account.set_password(self.cleaned_data["new_password"])
        self.account.save()
        return self.account


class ParentPasswordResetForm(StyledFormMixin, PasswordResetForm):
    email = forms.EmailField(
        label=_("Email address"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )


class ParentSetPasswordForm(StyledFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = _("New password")
        self.fields["new_password1"].help_text = PASSWORD_HELP
        self.fields["new_password2"].label = _("Repeat new password")
        self.fields["new_password2"].help_text = _("Enter the same password again.")


class ChildAccountForm(StyledFormMixin, forms.Form):
    name = forms.CharField(label=_("Child's name"), max_length=80)
    vocative_name = forms.CharField(
        label=_("Vocative name"),
        max_length=80,
        required=False,
        help_text=_("Used in Lithuanian greetings. Leave blank to generate it automatically."),
    )
    pin = forms.CharField(
        label="PIN",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )
    confirm_pin = forms.CharField(
        label=_("Repeat PIN"),
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )
    min_balance = forms.IntegerField(label=_("Initial credit"), max_value=0, required=False)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if ChildProfile.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(_("A child profile with this name already exists."))
        return name

    def clean(self):
        cleaned = super().clean()
        pin = cleaned.get("pin", "")
        if pin and not pin.isdigit():
            self.add_error("pin", _("The PIN must contain digits only."))
        if cleaned.get("pin") != cleaned.get("confirm_pin"):
            self.add_error("confirm_pin", _("The PINs do not match."))
        return cleaned

    def save(self):
        settings = FamilySettings.load()
        child = ChildProfile(
            name=self.cleaned_data["name"],
            vocative_name=self.cleaned_data["vocative_name"].strip(),
            theme=Theme.NEUTRAL,
            theme_selected=False,
            min_balance=(
                self.cleaned_data["min_balance"]
                if self.cleaned_data["min_balance"] is not None
                else settings.default_min_balance
            ),
        )
        child.set_pin(self.cleaned_data["pin"])
        child.save()
        return child


class ChildEditForm(StyledFormMixin, forms.Form):
    name = forms.CharField(label=_("Child's name"), max_length=80)
    vocative_name = forms.CharField(
        label=_("Vocative name"),
        max_length=80,
        required=False,
        help_text=_("Used in Lithuanian greetings. Leave blank to generate it automatically."),
    )
    min_balance = forms.IntegerField(label=_("Credit"), max_value=0)
    birth_date = forms.DateField(
        label=_("Birthday"),
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        help_text=_("Parents may change this date without an additional approval."),
    )
    new_pin = forms.CharField(
        label=_("New PIN"),
        min_length=4,
        max_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
        help_text=_("Leave blank to keep the current PIN."),
    )
    confirm_pin = forms.CharField(
        label=_("Repeat new PIN"),
        min_length=4,
        max_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"}),
    )

    def __init__(self, *args, child, **kwargs):
        self.child = child
        kwargs.setdefault(
            "initial",
            {
                "name": child.name,
                "vocative_name": child.vocative_name,
                "min_balance": child.min_balance,
                "birth_date": child.birth_date,
            },
        )
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if ChildProfile.objects.filter(name__iexact=name).exclude(pk=self.child.pk).exists():
            raise forms.ValidationError(_("This child name is already in use."))
        return name

    def clean(self):
        cleaned = super().clean()
        pin = cleaned.get("new_pin", "")
        if pin and not pin.isdigit():
            self.add_error("new_pin", _("The PIN must contain digits only."))
        if pin != cleaned.get("confirm_pin", ""):
            self.add_error("confirm_pin", _("The PINs do not match."))
        return cleaned

    def save(self, *, actor):
        previous_birth_date = self.child.birth_date
        requested_birth_date = self.cleaned_data["birth_date"]
        self.child.name = self.cleaned_data["name"]
        self.child.vocative_name = self.cleaned_data["vocative_name"].strip()
        self.child.min_balance = self.cleaned_data["min_balance"]
        update_fields = ["name", "vocative_name", "min_balance"]
        if requested_birth_date != previous_birth_date:
            self.child.birth_date = requested_birth_date
            self.child.birth_date_initialized = True
            update_fields.extend(["birth_date", "birth_date_initialized"])
        if self.cleaned_data["new_pin"]:
            self.child.set_pin(self.cleaned_data["new_pin"])
            update_fields.append("pin_hash")
        self.child.save(update_fields=update_fields)
        if requested_birth_date != previous_birth_date:
            BirthDateChangeRequest.objects.filter(
                child=self.child,
                status=RequestStatus.PENDING,
            ).update(
                status=RequestStatus.REJECTED,
                decided_by=actor,
                decided_at=timezone.now(),
            )
            BirthDateChangeRequest.objects.create(
                child=self.child,
                previous_birth_date=previous_birth_date,
                requested_birth_date=requested_birth_date,
                status=RequestStatus.APPROVED,
                decided_by=actor,
                decided_at=timezone.now(),
            )
        return self.child
