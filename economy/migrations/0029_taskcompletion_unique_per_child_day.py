from django.db import migrations, models


def dedupe_task_completions(apps, schema_editor):
    TaskCompletion = apps.get_model("economy", "TaskCompletion")
    seen = set()
    for row in TaskCompletion.objects.order_by("pk").values(
        "pk", "child_id", "task_id", "completed_on"
    ):
        key = (row["child_id"], row["task_id"], row["completed_on"])
        if key in seen:
            TaskCompletion.objects.filter(pk=row["pk"]).delete()
        else:
            seen.add(key)


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0028_alter_attemptcounter_scope"),
    ]

    operations = [
        migrations.RunPython(dedupe_task_completions, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="taskcompletion",
            name="task_done_child_day_idx",
        ),
        migrations.AddConstraint(
            model_name="taskcompletion",
            constraint=models.UniqueConstraint(
                fields=("child", "task", "completed_on"),
                name="unique_task_completion_per_child_day",
            ),
        ),
    ]
