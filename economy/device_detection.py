"""Small, privacy-preserving device classification helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    kind: str
    platform: str
    browser: str


def identify_device(user_agent):
    """Classify a browser into a broad device profile without fingerprinting it."""

    user_agent = user_agent or ""
    normalized = user_agent.lower()

    if "windows phone" in normalized:
        kind, platform = "phone", "windows"
    elif "iphone" in normalized or "ipod" in normalized:
        kind, platform = "phone", "ios"
    elif "ipad" in normalized or (
        "macintosh" in normalized and "mobile" in normalized
    ):
        kind, platform = "tablet", "ios"
    elif "android" in normalized:
        kind, platform = (
            ("phone", "android") if "mobile" in normalized else ("tablet", "android")
        )
    elif "macintosh" in normalized or "mac os x" in normalized:
        kind, platform = "computer", "macos"
    elif "windows" in normalized:
        kind, platform = "computer", "windows"
    elif "linux" in normalized:
        kind, platform = "computer", "linux"
    else:
        kind, platform = "unknown", "unknown"

    if "edg/" in normalized or "edgios/" in normalized:
        browser = "edge"
    elif "crios/" in normalized or "chrome/" in normalized:
        browser = "chrome"
    elif "fxios/" in normalized or "firefox/" in normalized:
        browser = "firefox"
    elif "safari/" in normalized:
        browser = "safari"
    elif "opera/" in normalized or "opr/" in normalized:
        browser = "opera"
    else:
        browser = "unknown"

    return DeviceProfile(kind=kind, platform=platform, browser=browser)
