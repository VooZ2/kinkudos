from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from economy.models import (
    BirthdayAward,
    ChildProfile,
    FamilySettings,
    LedgerKind,
    PointGift,
    Task,
    Theme,
)
from economy.services import award_birthdays, transfer_points
from economy.templatetags.economy_tags import currency_unit


class GiftTests(TestCase):
    def setUp(self):
        self.sender = ChildProfile.objects.create(
            name="Sender", balance=40, theme_selected=True
        )
        self.recipient = ChildProfile.objects.create(
            name="Recipient", balance=-20, theme_selected=True
        )

    def test_transfer_is_atomic_and_creates_two_history_entries(self):
        gift = transfer_points(
            sender=self.sender, recipient=self.recipient, amount=15
        )
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual((self.sender.balance, self.recipient.balance), (25, -5))
        self.assertEqual(PointGift.objects.count(), 1)
        entries = list(
            gift.sender.ledger_entries.filter(
                kind=LedgerKind.GIFT, source_id=gift.pk
            )
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].delta, -15)
        self.assertEqual(
            gift.recipient.ledger_entries.get(
                kind=LedgerKind.GIFT, source_id=gift.pk
            ).delta,
            15,
        )

    def test_credit_and_self_transfer_are_rejected(self):
        self.sender.balance = -1
        self.sender.save(update_fields=["balance"])
        with self.assertRaises(ValidationError):
            transfer_points(sender=self.sender, recipient=self.recipient, amount=1)
        self.sender.balance = 10
        self.sender.save(update_fields=["balance"])
        with self.assertRaises(ValidationError):
            transfer_points(sender=self.sender, recipient=self.sender, amount=1)
        self.assertFalse(PointGift.objects.exists())

    def test_gift_history_uses_gift_icon(self):
        transfer_points(sender=self.sender, recipient=self.recipient, amount=2)
        session = self.client.session
        session["child_id"] = self.sender.pk
        session.save()

        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(
            response,
            '<use href="#icon-gift"></use>',
            html=False,
        )
        self.assertNotContains(
            response,
            '<span class="ledger-icon">G</span>',
            html=False,
        )


class BirthdayTests(TestCase):
    def setUp(self):
        family = FamilySettings.load()
        family.birthday_points = 25
        family.save()

    @override_settings(USE_TZ=True)
    def test_awarded_once_per_year(self):
        child = ChildProfile.objects.create(
            name="Birthday child",
            birth_date=date(2018, 7, 29),
            balance=5,
            theme_selected=True,
        )
        first = award_birthdays(current_date=date(2026, 7, 29))
        second = award_birthdays(current_date=date(2026, 7, 29))
        child.refresh_from_db()
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(child.balance, 30)
        self.assertEqual(BirthdayAward.objects.count(), 1)
        self.assertEqual(child.ledger_entries.get().kind, LedgerKind.BIRTHDAY)

    def test_february_29_is_awarded_on_february_28_in_non_leap_year(self):
        child = ChildProfile.objects.create(
            name="Leap child",
            birth_date=date(2020, 2, 29),
            theme_selected=True,
        )
        self.assertEqual(
            len(award_birthdays(current_date=date(2027, 2, 28))), 1
        )
        child.refresh_from_db()
        self.assertEqual(child.balance, 25)


class ThemeAndViewTests(TestCase):
    def test_currency_forms_for_new_themes(self):
        with override("lt"):
            for theme, forms in {
                Theme.HERO_HQ: ("ženklelis", "ženkleliai", "ženklelių"),
                Theme.ART_STUDIO: ("perlas", "perlai", "perlų"),
                Theme.PANDA_PET: ("bambukas", "bambukai", "bambukų"),
                Theme.BLOCKVILLE: ("kubelis", "kubeliai", "kubelių"),
            }.items():
                self.assertEqual(currency_unit(1, theme), forms[0])
                self.assertEqual(currency_unit(5, theme), forms[1])
                self.assertEqual(currency_unit(10, theme), forms[2])
                self.assertEqual(currency_unit(21, theme), forms[0])
                self.assertEqual(currency_unit(111, theme), forms[2])

    def test_child_dashboard_has_search_gift_and_birthday_forms(self):
        child = ChildProfile.objects.create(
            name="Child", balance=10, theme=Theme.HERO_HQ, theme_selected=True
        )
        ChildProfile.objects.create(name="Other", theme_selected=True)
        Task.objects.create(title="Clean room", reward=10)
        session = self.client.session
        session["child_id"] = child.pk
        session.save()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "data-task-search")
        self.assertContains(response, 'role="combobox"', html=False)
        self.assertContains(response, 'data-task-search-results', html=False)
        self.assertContains(response, 'role="listbox"', html=False)
        self.assertContains(response, 'id="task-card-', html=False)
        self.assertContains(response, reverse("child_give_points"))
        self.assertContains(response, reverse("child_set_birth_date"))
        self.assertContains(response, "Hero Missions")

    def test_blockville_theme_has_currency_and_game_copy(self):
        child = ChildProfile.objects.create(
            name="Theme tester",
            balance=12,
            theme=Theme.BLOCKVILLE,
            theme_selected=True,
        )
        Task.objects.create(title="Test quest", reward=5)
        session = self.client.session
        session["child_id"] = child.pk
        session.save()
        response = self.client.get(reverse("child_dashboard"))
        self.assertContains(response, "theme-blockville")
        self.assertContains(response, "Block quests")
        self.assertContains(response, "Complete challenge")
        self.assertContains(response, "<strong>12</strong><span>cubes</span>", html=True)
