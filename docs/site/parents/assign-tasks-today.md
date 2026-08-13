# Assign tasks for today

Assigning work gives one child a small, explicit list for the current day. Use
**Assign tasks for today** on that child’s card in **Parents → Home**.

> **For:** Parents<br>
> **Result:** The child receives a list of tasks that expires at local midnight

## Assign a daily list

1. Open the child’s card and choose **Assign tasks for today**.
2. Select catalogue tasks. You may also add one **Custom task (optional)** with
   a title and point value.
3. Add an optional note under a selected task or the custom task if a short
   instruction would help. Notes exist only in this dialog, not in
   **Manage → Tasks**.
4. Decide whether unfinished assigned work should block **new** reward
   requests.
5. Choose **Send tasks**, then ask the child to open their dashboard and
   confirm the list is visible.

The child completes each assigned task themselves and receives its points
immediately. There is no separate parent-approval step for that completion, and
there is no child claim note on that check. Parents with notifications enabled
also receive a Web Push alert. Close the dialog with **X** if you are not
sending yet.

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View Assign tasks for today with an optional note</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-assign-note-desktop-26-7-0.png" alt="Assign tasks for today dialog with an optional note under a selected task and today’s assigned batches" loading="lazy">
</details>

The screenshot uses fictional demonstration data.

## Optional notes

A parent note is stored on the assigned item when you send it. Later catalogue
edits do not change a note that was already sent. The child sees it clearly
under the task title, using the colours and wording of their current world.
This is not the optional **What I did** note a child can add when submitting a
catalogue task for approval.

## Saved assignment sets

Use **Save as a set** in the same dialog when the same list should go out on a
schedule. Name the set, choose **How often?**, and set **Send at** (the
default is 07:00 in the server’s local time). Then choose **Save set**.

How often:

| Option | What it does |
| --- | --- |
| **Every day** | Sends on each local calendar day. |
| **Chosen weekdays** | Sends only on the weekdays you tick. |
| **Weekend** | Saturday, Sunday, or both. |
| **Once a week** | Sends on one chosen weekday. |

Only the options for the chosen schedule are used. KinKudos does not include
separate holiday or school-term modes.

Saved sets for that child appear at the top of the dialog:

- **Apply** sends the set now, using the same availability rules as a manual
  assign.
- **Pause** keeps the set for later **Apply** but skips automatic sending.
- **Resume** turns automatic sending back on.
- **Delete** removes the set.

A family can keep up to five saved sets per child. Automatic sending uses the
same roughly 30-minute timer as lottery reminders: on a matching local day,
once the clock is at or after **Send at**, the set is sent once. Unavailable
catalogue tasks are skipped the same way as a manual assign.

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View saved assignment sets and How often options</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-assign-saved-set-desktop-26-7-0.png" alt="Assign dialog showing a saved set with Apply, Pause, and Delete, plus How often schedule options" loading="lazy">
</details>

The screenshot uses fictional demonstration data.

## Today’s batches only

The dialog’s **Today's assigned tasks** area lists only batches sent today, so
you can cancel one unfinished item or the remaining set. Unfinished work from
yesterday is not listed there: pending assigned items expire at local midnight
for the child and stop appearing as today’s work.

## Important limits

- A catalogue task cannot be assigned when it is already pending review,
  already assigned today, or already credited today. Those rows show
  **Unavailable today**. A child-submitted catalogue claim can still be
  approved more than once in the same local day; Assign and Award stay once
  per local day.
- Unfinished assignments expire at midnight in the server’s local time. They
  disappear from the child’s list and stop blocking new reward requests. They
  do not award points.
- Incomplete assigned items do not create Activity History / ledger entries.
  Only a completed assigned task (or a later point correction) appears there.
- You can cancel one unfinished item or the remaining set. A cancelled item
  does not award points.
- The reward block applies only to new reward requests. It does not cancel a
  request already awaiting a parent decision and does not prevent other child
  actions.

## Gentle reminder

About three hours after a batch is sent, KinKudos may notify the child if any
item is still waiting. That reminder uses the same timer command as lottery
reminders. Unfinished work is not penalised automatically.

## When to use a normal task instead

Use a normal child-submitted task when the work does not have to be completed
today or should wait for parent review. See [review completed tasks](review-completed-tasks.md).

[Parent dashboard →](dashboard-and-child-cards.md) · [Activity history →](history.md) · [Lietuviškai](assign-tasks-today.lt.md)
