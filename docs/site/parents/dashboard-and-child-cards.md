# Parent dashboard and child cards

Path: **Parents → Home**. Home is the fast action centre: it shows pending
requests first and child cards underneath them.

## Home hierarchy

1. **Pending requests** — review decisions that need a parent.
2. **Child cards** — check each child and open a quick action.

The pending panel always has an in-panel **Pending requests** heading. When
requests exist, a count badge appears beside that heading. When there are none,
the compact empty state says **No pending requests**. The child cards remain
directly below the panel.

The parent **Home** navigation item also shows that pending count. On a phone
the badge sits on the house-icon corner; on a wider screen it stays a compact
count on the right of the Home row.

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View Parent Home pending requests on mobile</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-home-pending-requests-mobile-26-6-7.png" alt="Parent Home pending requests panel with heading and count badge on mobile" loading="lazy">
</details>

The screenshot uses fictional demonstration data.

## Child cards

Each card can show:

- the child’s avatar and name;
- the current spendable point balance;
- credit, which is the lower balance limit;
- scratch-ticket usage when scratch tickets are enabled;
- the separately saved-points total, when it is greater than zero;
- one relevant savings-goal summary, when the child has an active goal;
- primary actions **Add** and **Assign**, plus **More**.

Credit and Tickets appear as left-aligned metadata items on separate lines;
there is no middle-dot separator between them.

The compact indicators can look like this:

| Indicator | Meaning |
| --- | --- |
| `463 Points` | Spendable points now. |
| `Credit -100` | The lowest balance this child may spend down to; it is not 100 extra points. |
| `Tickets 0/3` | Scratch tickets used and the weekly limit. |
| `50 saved` | Points saved separately for goals. |

Points is the spendable balance. Points saved separately for a goal are
excluded from it and cannot be used for rewards. A zero or negative balance
gives a use-available goal zero progress. The **Tickets** line is hidden when
scratch tickets are disabled. The `saved` line is shown only when the child
has saved points; `0 saved` is not shown. An information control next to that
total explains the reserved points; the goal strip below it has no separate
information button. A child without goals has no empty goal block or
placeholder.

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View Parent Home child cards on mobile</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-home-child-cards-mobile-26-6-7.png" alt="Parent Home child cards with Add, Assign, and More actions on mobile" loading="lazy">
</details>

The screenshot uses fictional demonstration data.

## Goal summary

One relevant goal may appear on a child card. The priority is:

1. a reached goal waiting for a parent decision;
2. the **Current goal**;
3. a separately saved goal closest to completion.

The summary can show the goal title, current progress and target, a progress
bar, and a status such as **Current goal**, **Uses available points**, **Saved**,
or **Reached goal**. A saved goal may also be identified as **Saved
separately**, and an additional-goal count can show that more goals exist.

The goal strip has no separate information button. Selecting the whole strip
opens **Manage → Goals**.

## Child card actions

The primary row shows two labelled actions and a **More** control. Use the
accessible action names rather than relying on an icon:

| Action | Where | Use it for |
| --- | --- | --- |
| **Add completed task** | Primary row (**Add**) | Award selected catalogue tasks immediately after checking the work. |
| **Assign tasks for today** | Primary row (**Assign**) | Send today’s catalogue tasks, one optional custom task, and optional notes. The dialog lists only today’s batches. |
| **Adjust points** | **More** | Add or remove points with a required reason. |
| **Assign penalty** | **More** | Apply agreed penalty templates and an optional shared reason. |
| **Set credit** | **More** | Change this child’s lower spending limit. |

**More** opens a short dialog titled **More actions**. Icon-only controls expose
their action name through their tooltip and accessible label. Family
documentation does not depend on icon shapes.

## Assigned tasks for today

An assigned task is available only on the day it is sent. At midnight in the
server’s local time, unfinished items expire: they leave the child’s list and
stop blocking new reward requests. Incomplete assigned items do not create
Activity History entries; only a completed assigned task appears in the
ledger.

The **Assign tasks for today** dialog lists only today’s batches. Unfinished
work from a previous day is not kept there. Optional notes and saved
assignment sets are documented in [Assign tasks for today](assign-tasks-today.md).

You can choose **Block reward purchases until these tasks are finished**. This
blocks only new reward requests from that child; it does not cancel a request
already waiting for a parent and does not block other actions. Individual
unfinished tasks or the remaining set can be cancelled from the same card.

## Pending requests

Requests appear in the pending panel and are easy to scan by child. The child’s
name and the type (**Task** or **Reward**) sit on one line. On a phone,
decision actions sit left-aligned under the request copy. The available
decisions are:

- **Approve** — accepts the task, reward, proposal, or birthday-date change.
- **Ask to improve** — returns a submitted task to the child with an optional
  explanation; it can be submitted again.
- **Reject** — closes the request without awarding points or granting a
  reward. Reasons are required for rewards and proposals.

When approving a savings-goal proposal that still needs a save mode, the dialog
offers **Use available points** and **Save separately** as inline option cards
(radio + label).

For a task with a child note, a comment icon opens a read-only dialog. There is
no icon when the note is empty. For a task with a photo, select the thumbnail
to view it at full size. The note does not award a photo bonus. Photos
are private family data and follow the retention rule in [Parent
settings](settings.md).

## History

Use **History** to answer questions such as “Did this reward get approved?” or
“Why did the balance change?”. A point change is a permanent record. If
something needs correcting, use **Adjust points** to create a transparent new
entry instead of rewriting the past.

Selecting a child in the History filter applies immediately and keeps the
other active filters. Rejected decisions are also recorded even when no points
moved. See [Activity history and filters](history.md) for the complete list of
events and filters.

[Tasks and approvals →](tasks-and-approvals.md) · [Activity history →](history.md) · [Child space →](child-space.md)
