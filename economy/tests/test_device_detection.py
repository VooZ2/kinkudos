from django.test import SimpleTestCase

from economy.device_detection import identify_device


class DeviceDetectionTests(SimpleTestCase):
    def test_common_user_agents_are_classified_without_fingerprinting(self):
        cases = {
            "iphone": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1",
                ("phone", "ios", "safari"),
            ),
            "ipad": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1",
                ("tablet", "ios", "safari"),
            ),
            "android_phone": (
                "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                "Mobile Safari/537.36",
                ("phone", "android", "chrome"),
            ),
            "android_tablet": (
                "Mozilla/5.0 (Linux; Android 14; Tablet) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                "Safari/537.36",
                ("tablet", "android", "chrome"),
            ),
            "mac": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                ("computer", "macos", "safari"),
            ),
        }

        for name, (user_agent, expected) in cases.items():
            with self.subTest(name=name):
                profile = identify_device(user_agent)
                self.assertEqual(
                    (profile.kind, profile.platform, profile.browser),
                    expected,
                )

    def test_empty_user_agent_falls_back_to_unknown(self):
        profile = identify_device("")

        self.assertEqual(profile.kind, "unknown")
        self.assertEqual(profile.platform, "unknown")
        self.assertEqual(profile.browser, "unknown")
