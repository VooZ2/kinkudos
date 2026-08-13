# Tasks and approvals

Paths: **Parents → Manage → Tasks** for the catalogue and **Parents → Home**
for decisions. KinKudos offers two ways to award completed work: a child
submits a task for approval, or a parent directly records a completed task.

## Build the task catalogue

Create shared tasks with a short, observable title, a positive point value, and
an optional emoji. The catalogue is shared, but each child sees only tasks
currently available to them.

Catalogue rows can expose these actions:

- **Edit** opens one form at a time with **Save** and **Cancel**; **Delete**
  is separated below;
- **Hide** keeps the item and its history but removes it from child selection;
  hidden rows look muted and show a **Hidden** state;
- **Show** makes a hidden item available again;
- **Delete** removes the item from active use according to the implemented
  catalogue behavior.

Changes affect new uses only. Previous **History** entries keep enough of the
original task information to remain understandable.

## Child-submitted tasks

1. A child selects an available catalogue task and may attach a photo and an
   optional short note (**What I did**, at most 200 characters). Completing an
   assigned task does not use this note.
2. The task appears in **Parents → Home → Pending requests**. If the child
   wrote a note, a comment icon opens a read-only dialog; there is no icon when
   the note is empty. The note is not a chat and does not award a photo bonus.
3. Choose one decision:

| Decision | Result |
| --- | --- |
| **Approve** | Awards the shown task points and the configured photo bonus when a photo was submitted. |
| **Ask to improve** | Returns the task to the child with an optional explanation; no points move yet. |
| **Reject** | Closes the task without points. An optional explanation can tell the child why. |

A child can have one active submission for the same task at a time. The same
catalogue task can be submitted and approved more than once in one local day;
each approved claim still awards its points. **Assign tasks for today** and
**Add completed task** still credit that catalogue task at most once per local
day.

A task photo is private to the family: it is resized, stripped of camera
metadata, and kept according to the family retention rule.

## Add a completed task directly

On a child card in **Parents → Home**, use **Add completed task**. Select one
or more catalogue tasks and choose the action to award them. Points are added
immediately, without a child submission or second approval.

## Assign tasks for today

Use **Assign tasks for today** on a child card to send selected catalogue tasks
for the current day. You can also add one custom task, an optional note, and a
saved set that can go out on a schedule. See [Assign tasks for today](assign-tasks-today.md).

- Assigned tasks expire at midnight in the server’s local time and then leave
  today’s lists.
- The child completes each assigned task; points are added immediately. That
  completion has no child note. Parents with notifications enabled also
  receive a Web Push alert.
- A task is unavailable when it is already waiting for approval, assigned
  today, or credited today.
- You can optionally block **new** reward purchases until the assigned tasks
  are finished.
- You can cancel one unfinished task or all remaining tasks in a batch.
- Incomplete assigned items do not appear in Activity History; only a
  completed assigned task creates a ledger entry.

## Penalties and adjustments

Create penalty templates in **Parents → Manage → Penalties** with a clear title,
negative point amount, and optional emoji. On a child card, open **More** and
choose **Assign penalty** to apply selected templates with an optional shared
reason. This creates a permanent negative History entry.

Use **More → Adjust points** for a one-off correction or something that is not
a task, reward, or penalty. Enter a positive or negative amount and a required
reason. See [Activity history and filters](history.md) for the full record.

[Parent dashboard and child cards →](dashboard-and-child-cards.md) · [Create and manage tasks →](create-and-manage-tasks.md) · [Activity history →](history.md) · [Lietuviškai](tasks-and-approvals.lt.md)
