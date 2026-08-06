# Parent dashboard and child cards

Path: **Parents → Home**. Home is the fast action centre: it shows pending
requests first and child cards underneath them.

## Home hierarchy

1. **Pending requests** — review decisions that need a parent.
2. **Child cards** — check each child and open a quick action.

When there are no requests, the compact empty state says **No pending
requests**. The child cards remain directly below it.

<details class="screenshot-disclosure">
<summary>View Parent Home pending requests on mobile</summary>
<img class="screenshot-image" src="../../assets/parent-home-pending-requests-mobile-26-6-0.png" alt="Parent Home pending requests on mobile" loading="lazy">
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
- five quick actions.

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
has saved points; `0 saved` is not shown. A child without goals has no empty
goal block or placeholder.

<details class="screenshot-disclosure">
<summary>View Parent Home child cards on mobile</summary>
<img class="screenshot-image" src="../../assets/parent-home-child-cards-mobile-26-6-0.png" alt="Parent Home child cards on mobile" loading="lazy">
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

Selecting the summary opens **Manage → Goals**.

## Five quick actions

Use the accessible action names rather than relying on an icon:

| Action | Use it for |
| --- | --- |
| **Add completed task** | Award selected catalogue tasks immediately after checking the work. |
| **Assign penalty** | Apply agreed penalty templates and an optional shared reason. |
| **Assign tasks for today** | Send catalogue tasks, plus one optional custom task, until midnight. |
| **Adjust points** | Add or remove points with a required reason. |
| **Set credit** | Change this child’s lower spending limit. |

Icon-only controls expose their action name through their tooltip and
accessible label. Family documentation does not depend on icon shapes.

## Assigned tasks for today

An assigned task is available only on the day it is sent. At midnight in the
server’s local time, unfinished tasks expire and remain understandable in
History, but they no longer block the child.

You can choose **Block reward purchases until these tasks are finished**. This
blocks only new reward requests from that child; it does not cancel a request
already waiting for a parent and does not block other actions. Individual
unfinished tasks or the remaining set can be cancelled from the same card.

## Pending requests

Requests are grouped by child. The available decisions are:

- **Approve** — accepts the task, reward, proposal, or birthday-date change.
- **Ask to improve** — returns a submitted task to the child with an optional
  explanation; it can be submitted again.
- **Reject** — closes the request without awarding points or granting a
  reward. Reasons are required for rewards and proposals.

For a task with a photo, select the thumbnail to view it at full size. Photos
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
