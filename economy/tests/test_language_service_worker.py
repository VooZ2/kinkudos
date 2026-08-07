import hashlib
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from economy.models import FamilySettings

ROOT = Path(__file__).resolve().parents[2]


class LanguageSwitchFlowTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "language-review-parent",
            password="Safe-language-review-pass-123!",
        )

    def switch_language(self, language, next_url):
        return self.client.post(
            reverse("set_language"),
            {"language": language, "next": next_url},
        )

    def test_parent_login_switches_language_and_preserves_destination(self):
        destination = f"{reverse('parent_login')}?from=review#language"

        response = self.switch_language("lt", destination)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, destination)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "lt")
        redirected = self.client.get(response.url)
        self.assertContains(redirected, '<html lang="lt">', html=False)
        self.assertContains(redirected, "Prisijungti")

        response = self.switch_language("en", destination)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, destination)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")
        redirected = self.client.get(response.url)
        self.assertContains(redirected, '<html lang="en">', html=False)
        self.assertContains(redirected, "Sign in")

    def test_explicit_language_survives_family_default_and_signed_in_switches(self):
        family = FamilySettings.load()
        family.default_language = "lt"
        family.save(update_fields=["default_language"])

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get(reverse("parent_login"))
        self.assertContains(response, '<html lang="en">', html=False)

        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, '<html lang="en">', html=False)
        self.assertContains(response, "Home")

        response = self.switch_language("lt", f"{reverse('parent_dashboard')}#parent-settings")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('parent_dashboard')}#parent-settings")
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "lt")
        redirected = self.client.get(response.url)
        self.assertContains(redirected, '<html lang="lt">', html=False)
        self.assertContains(redirected, "Nustatymai")

    def test_repeated_switching_uses_one_server_side_redirect_per_action(self):
        destination = f"{reverse('parent_login')}?step=repeat#language"

        for language in ("lt", "en", "lt", "en"):
            response = self.switch_language(language, destination)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, destination)
            self.assertEqual(
                response.cookies[settings.LANGUAGE_COOKIE_NAME].value,
                language,
            )
            redirected = self.client.get(response.url)
            self.assertContains(redirected, f'<html lang="{language}">', html=False)

    def test_language_form_keeps_native_navigation_and_preserves_current_url(self):
        script = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
        start = script.index('document.querySelectorAll(".language-switcher-menu")')
        end = script.index("function urlBase64ToUint8Array", start)
        language_handler = script[start:end]

        self.assertEqual(script.count('document.querySelectorAll(".language-switcher-menu")'), 1)
        self.assertIn("window.location.hash", language_handler)
        self.assertNotIn("requestSubmit", language_handler)
        self.assertNotIn("preventDefault", language_handler)
        self.assertNotIn("window.location.reload", language_handler)
        self.assertNotIn("window.location.assign", language_handler)
        self.assertNotIn("languageNavigationPending", script)
        self.assertNotIn('setAttribute("aria-disabled"', script)

    def test_public_language_options_remain_enabled(self):
        for url in (reverse("home"), reverse("parent_login")):
            response = self.client.get(url)
            content = response.content.decode()
            menu = content[content.index('class="language-switcher-menu"'):]
            menu = menu[:menu.index("</form>") + 7]
            self.assertEqual(content.count('class="language-switcher-menu"'), 1)
            self.assertEqual(menu.count('class="language-switcher-option"'), 2)
            self.assertEqual(menu.count('type="submit"'), 2)
            self.assertEqual(menu.count('name="language"'), 2)
            self.assertIn('value="en"', menu)
            self.assertIn('value="lt"', menu)
            self.assertIn('class="language-switcher-menu"', menu)
            self.assertNotIn('aria-disabled="true"', menu)
            self.assertNotIn('disabled="disabled"', menu)

        stylesheet = (ROOT / "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".language-switcher-option:active", stylesheet)
        self.assertIn("touch-action: manipulation", stylesheet)
        self.assertIn(
            ".system-page .topbar { position: relative; z-index: 10; }",
            stylesheet,
        )
        self.assertNotIn(
            ".system-page .topbar, .system-page .page, .system-page .site-footer",
            stylesheet,
        )


class ServiceWorkerStabilityTests(TestCase):
    def test_service_worker_source_is_identical_for_english_and_lithuanian(self):
        english = Client()
        english.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        lithuanian = Client()
        lithuanian.cookies[settings.LANGUAGE_COOKIE_NAME] = "lt"

        english_response = english.get(reverse("service_worker"))
        lithuanian_response = lithuanian.get(reverse("service_worker"))

        self.assertEqual(english_response.status_code, 200)
        self.assertEqual(lithuanian_response.status_code, 200)
        self.assertEqual(
            hashlib.sha256(english_response.content).digest(),
            hashlib.sha256(lithuanian_response.content).digest(),
        )

    def test_service_worker_has_no_language_dependent_rendered_content(self):
        source = (ROOT / "templates/economy/service-worker.js").read_text(encoding="utf-8")

        self.assertNotIn("{% translate", source)
        self.assertNotIn("{% load i18n", source)
        self.assertNotIn("family_settings", source)
        self.assertIn('{{ app_version }}', source)

    def test_service_worker_does_not_intercept_document_navigation(self):
        source = (ROOT / "templates/economy/service-worker.js").read_text(encoding="utf-8")

        self.assertNotIn('addEventListener("fetch"', source)
        self.assertNotIn("respondWith", source)
        self.assertIn('self.addEventListener("push"', source)
        self.assertIn('self.addEventListener("notificationclick"', source)
        self.assertIn("kinkudos-state-changed", source)
        self.assertIn("clients.matchAll", source)

    def test_registration_is_single_and_refresh_fallback_does_not_need_a_controller(self):
        source = (ROOT / "static/js/app.js").read_text(encoding="utf-8")

        self.assertEqual(source.count('.register("/service-worker.js"'), 1)
        self.assertNotIn("serviceWorker.unregister", source)
        self.assertNotIn("controllerchange", source)
        self.assertNotIn("navigator.serviceWorker.controller", source)
        self.assertIn('event.data?.type === STATE_CHANGED_MESSAGE', source)
        self.assertIn("scheduleChildStateCheck()", source)
        self.assertIn("scheduleParentStateCheck()", source)

    def test_manifest_remains_standalone_and_versioned(self):
        response = self.client.get(reverse("manifest"))
        manifest = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(len(manifest["icons"]), 2)
        self.assertTrue(all(icon["src"].startswith("/static/icons/") for icon in manifest["icons"]))
        for icon in manifest["icons"]:
            self.assertEqual(self.client.get(icon["src"]).status_code, 200)
