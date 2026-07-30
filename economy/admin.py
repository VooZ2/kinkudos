from django.contrib import admin

from .models import (
    BackupAuditEvent,
    BirthDateChangeRequest,
    ChildProfile,
    FamilySettings,
    LedgerEntry,
    PenaltyTemplate,
    Proposal,
    PushSubscription,
    Reward,
    RewardRequest,
    SavingsGoal,
    Task,
    TaskClaim,
)


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "theme", "balance", "min_balance", "is_active")
    readonly_fields = ("balance", "pin_hash", "failed_pin_attempts", "locked_until")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("child", "delta", "balance_after", "kind", "description", "created_at")
    readonly_fields = [field.name for field in LedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(FamilySettings)
admin.site.register(Task)
admin.site.register(TaskClaim)
admin.site.register(PenaltyTemplate)
admin.site.register(Reward)
admin.site.register(RewardRequest)
admin.site.register(Proposal)
admin.site.register(SavingsGoal)
admin.site.register(PushSubscription)
admin.site.register(BirthDateChangeRequest)
admin.site.register(BackupAuditEvent)
