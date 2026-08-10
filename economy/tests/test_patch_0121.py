from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    BirthDateChangeRequest,
    ChildProfile,
    LedgerKind,
    RequestStatus,
    Reward,
    RewardRequest,
    Task,
    TaskClaim,
)
from economy.services import approve_reward_request, approve_task_claim


class Patch0121Tests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Very-safe-pass-123!",
        )
        self.child = ChildProfile.objects.create(
            name="Child",
            theme_selected=True,
        )
        self.child.set_pin("1234")
        self.child.save(update_fields=["pin_hash"])

    def sign_in_child(self):
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def test_first_birthday_is_saved_but_later_change_needs_parent_approval(self):
        self.sign_in_child()
        response = self.client.post(
            reverse("child_set_birth_date"),
            {"birth_date": "2018-07-29"},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        self.child.refresh_from_db()
        self.assertEqual(self.child.birth_date, date(2018, 7, 29))
        self.assertTrue(self.child.birth_date_initialized)
        self.assertFalse(BirthDateChangeRequest.objects.exists())

        self.client.post(
            reverse("child_set_birth_date"),
            {"birth_date": "2018-07-30"},
        )
        self.child.refresh_from_db()
        self.assertEqual(self.child.birth_date, date(2018, 7, 29))
        change = BirthDateChangeRequest.objects.get()
        self.assertEqual(change.status, RequestStatus.PENDING)

        self.client.logout()
        self.client.force_login(self.parent)
        self.client.post(
            reverse("parent_decide_birth_date", args=[change.pk, "approve"])
        )
        self.child.refresh_from_db()
        change.refresh_from_db()
        self.assertEqual(self.child.birth_date, date(2018, 7, 30))
        self.assertEqual(change.status, RequestStatus.APPROVED)
        self.assertEqual(change.decided_by, self.parent)

    def test_only_one_birthday_change_can_wait(self):
        self.child.birth_date = date(2018, 7, 29)
        self.child.birth_date_initialized = True
        self.child.save(update_fields=["birth_date", "birth_date_initialized"])
        self.sign_in_child()
        self.client.post(
            reverse("child_set_birth_date"),
            {"birth_date": "2018-07-30"},
        )
        self.client.post(
            reverse("child_set_birth_date"),
            {"birth_date": "2018-07-31"},
        )
        self.assertEqual(
            BirthDateChangeRequest.objects.filter(
                status=RequestStatus.PENDING
            ).count(),
            1,
        )

    def test_child_state_is_private_and_not_cached(self):
        response = self.client.get(reverse("child_state"))
        self.assertEqual(response.status_code, 302)
        self.sign_in_child()
        response = self.client.get(reverse("child_state"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        signature = response.json()["signature"]
        self.child.balance = 10
        self.child.save(update_fields=["balance"])
        self.assertNotEqual(
            self.client.get(reverse("child_state")).json()["signature"],
            signature,
        )

    def test_parent_history_identifies_task_approver(self):
        task = Task.objects.create(title="Task", reward=10)
        claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
        )
        approve_task_claim(claim=claim, actor=self.parent)
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Approved by")
        self.assertContains(response, self.parent.username)
        self.assertContains(response, 'class="history-row-actions"', html=False)
        self.assertContains(response, 'class="history-kind-icon"', html=False)
        self.assertNotContains(response, 'history-meta-icon', html=False)
        html = response.content.decode()
        row_start = html.index('<div class="ledger-row">')
        row_end = html.index('</div>', html.index('class="history-row-actions"', row_start))
        row_html = html[row_start:row_end]
        self.assertLess(row_html.index('class="profile-mini'), row_html.index("<div>"))
        self.assertGreater(row_html.index('class="history-kind-icon"'), row_html.index("<div>"))
        self.assertEqual(
            self.child.ledger_entries.get(kind=LedgerKind.TASK).actor,
            self.parent,
        )

    def test_authenticated_header_uses_logo_and_footer_version(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, 'class="brand-mark brand-logo"', html=False)
        self.assertContains(response, 'class="footer-product">KinKudos · ', html=False)
        self.assertContains(response, "v26.6.4")
        self.assertNotContains(response, 'class="app-version"', html=False)

    def test_reward_approval_uses_task_decision_icons(self):
        reward = Reward.objects.create(title="Reward", cost=10)
        RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_pending_state"))
        fragment = response.json()["html"]

        self.assertIn(
            'class="pending-request-row',
            fragment,
        )
        self.assertIn('href="#icon-circle-check"', fragment)
        self.assertIn('href="#icon-circle-xmark"', fragment)
        self.assertIn('aria-label="Approve"', fragment)
        self.assertIn('aria-label="Reject"', fragment)

    def test_account_creation_actions_use_short_lithuanian_labels(self):
        self.client.cookies["django_language"] = "lt"
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, ">Kurti paskyrą</button>", html=False)
        self.assertContains(response, ">Sukurti profilį</button>", html=False)
        self.assertContains(response, ">Paskyros tipas</span>", html=False)
        self.assertContains(response, ">Tėvų paskyra</option>", html=False)
        self.assertContains(response, ">Vaiko profilis</option>", html=False)
        self.assertContains(response, ">Esamos paskyros</h3>", html=False)
        self.assertContains(response, ">Vaikų profiliai</h4>", html=False)
        self.assertNotContains(response, ">Kurti naujas paskyras</h3>", html=False)

    def test_child_history_identifies_reward_approver_and_rejector(self):
        self.child.balance = 100
        self.child.save(update_fields=["balance"])
        reward = Reward.objects.create(title="Approved reward", cost=10)
        approved = RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        approve_reward_request(request=approved, actor=self.parent)
        rejected_reward = Reward.objects.create(title="Rejected reward", cost=20)
        RewardRequest.objects.create(
            child=self.child,
            reward=rejected_reward,
            reward_title=rejected_reward.title,
            cost_snapshot=rejected_reward.cost,
            status=RequestStatus.REJECTED,
            rejection_reason="Not today",
            decided_by=self.parent,
            decided_at=timezone.now(),
        )

        self.sign_in_child()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "Approved reward")
        self.assertContains(response, "Approved by")
        self.assertContains(response, "Rejected reward")
        self.assertContains(response, "Rejected by")
        self.assertContains(response, self.parent.username, count=2)
        self.assertContains(response, 'class="history-row-actions"', html=False)
