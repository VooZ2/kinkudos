import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import get_language


RELEASE_HEADING = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>\d{4}-\d{2}-\d{2}))?$"
)
SECTION_KEYS = {
    "Added": "new",
    "Changed": "fixed",
    "Fixed": "fixed",
    "Security": "fixed",
    "Pridėta": "new",
    "Pakeista": "fixed",
    "Pataisyta": "fixed",
    "Saugumas": "fixed",
}


def _plain_text(value):
    return value.replace("`", "").strip()


@lru_cache(maxsize=2)
def _load_changelog(language):
    releases = []
    release = None
    section = None

    filename = "CHANGELOG.lt.md" if language == "lt" else "CHANGELOG.md"
    changelog_path = Path(settings.BASE_DIR) / filename
    for raw_line in changelog_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        heading = RELEASE_HEADING.match(line)
        if heading:
            version = heading.group("version")
            release = None
            section = None
            if version != "Unreleased":
                release = {
                    "version": version,
                    "date": heading.group("date"),
                    "new": [],
                    "fixed": [],
                }
                releases.append(release)
            continue

        if line.startswith("### "):
            section = SECTION_KEYS.get(line[4:])
            continue

        if release is None or section is None:
            continue
        if line.startswith("- "):
            release[section].append(_plain_text(line[2:]))
        elif line and release[section]:
            release[section][-1] += f" {_plain_text(line)}"

    return releases


def load_changelog():
    return _load_changelog(get_language())
