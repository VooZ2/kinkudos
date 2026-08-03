"""Build-time SEO and localization adjustments for the documentation."""

import json
import re
from urllib.parse import urljoin, urlparse

_NAV_LABELS = {
    "lt": {
        "Start": "Pradžia",
        "What is KinKudos": "Kas yra KinKudos",
        "Is KinKudos right for your family?": "Ar KinKudos tinka šeimai?",
        "What self-hosting means": "Ką reiškia savarankiškas diegimas?",
        "Quick install": "Greitas diegimas",
        "Your first 15 minutes": "Pirmos 15 minučių",
        "Pair a child device": "Vaiko įrenginio susiejimas",
        "Parents": "Tėvams",
        "Parent dashboard": "Tėvų skydelis",
        "Tasks and approvals": "Darbai ir patvirtinimai",
        "Create and manage tasks": "Kurti ir valdyti darbus",
        "Review completed tasks": "Peržiūrėti atliktus darbus",
        "Assign tasks for today": "Paskirti darbus šiandienai",
        "Points, penalties, and corrections": "Taškai, nuobaudos ir korekcijos",
        "Rewards, goals, and lottery": "Prizai, tikslai ir loterija",
        "Create and manage rewards": "Kurti ir valdyti prizus",
        "Savings goals and suggestions": "Taupymo tikslai ir pasiūlymai",
        "Lottery tickets": "Loterijos bilietai",
        "Child space": "Vaiko aplinka",
        "Parent settings": "Tėvų nustatymai",
        "Security": "Saugumas",
        "Accounts and devices": "Paskyros ir įrenginiai",
        "PINs and sign-in protection": "PIN ir prisijungimo apsauga",
        "Notifications and installing KinKudos": "Pranešimai ir KinKudos diegimas",
        "Network access": "Tinklo prieiga",
        "Backups": "Atsarginės kopijos",
        "Installation": "Diegimas",
        "Choose a method": "Pasirinkti būdą",
        "Hostinger VPS": "Hostinger VPS",
        "Guided server installer": "Vedamas serverio installeris",
        "Docker Compose": "Docker Compose",
        "First-time web setup": "Pirmasis setup naršyklėje",
        "Updating KinKudos": "KinKudos atnaujinimas",
        "Backups and restore": "Kopijos ir atkūrimas",
        "Uninstall KinKudos": "KinKudos pašalinimas",
        "Advanced deployment": "Pažangus diegimas",
        "Administration": "Administravimas",
        "Password recovery": "Slaptažodžio atkūrimas",
        "Emergency administrator": "Avarinis administratorius",
        "SMTP configuration": "SMTP nustatymas",
        "Logs and diagnostics": "Žurnalai ir diagnostika",
        "CLI command reference": "CLI komandų atmintinė",
        "Overview": "Apžvalga",
        "Before installing": "Prieš diegiant",
        "Updates, backups, and recovery": "Atnaujinimai, kopijos ir atkūrimas",
        "Family admin": "Šeimos administravimas",
        "Troubleshooting": "Problemų sprendimas",
        "Reference": "Atmintinė",
        "Roles, data, and limits": "Vaidmenys, duomenys ir ribos",
        "Release and support policy": "Leidimų ir palaikymo politika",
    },
    "de": {
        "Start": "Schnellstart",
        "What is KinKudos": "Was ist KinKudos?",
        "Is KinKudos right for your family?": "Passt KinKudos zu Ihrer Familie?",
        "What self-hosting means": "Was Selbsthosting bedeutet",
        "Quick install": "Schnellinstallation",
        "Your first 15 minutes": "Die ersten 15 Minuten",
        "Pair a child device": "Kindergerät verbinden",
    },
    "fr": {
        "Start": "Démarrage rapide",
        "What is KinKudos": "Qu’est-ce que KinKudos ?",
        "Is KinKudos right for your family?": "KinKudos convient-il à votre famille ?",
        "What self-hosting means": "Comprendre l’auto-hébergement",
        "Quick install": "Installation rapide",
        "Your first 15 minutes": "Vos 15 premières minutes",
        "Pair a child device": "Associer un appareil enfant",
    },
}

_QUICK_START_SLUGS = {
    "what-is-kinkudos",
    "is-kinkudos-right",
    "what-self-hosting-means",
    "quick-install",
    "first-15-minutes",
    "pair-a-child-device",
    "guided-installer",
}

_UI_LABELS = {
    "de": {
        "Back to top": "Nach oben",
        "Search": "Suchen",
        "Skip to content": "Zum Inhalt springen",
        "Table of contents": "Inhalt",
    },
    "fr": {
        "Back to top": "Retour en haut",
        "Search": "Rechercher",
        "Skip to content": "Aller au contenu",
        "Table of contents": "Sommaire",
    },
    "lt": {
        "Back to top": "Grįžti į viršų",
        "Search": "Ieškoti",
        "Skip to content": "Pereiti prie turinio",
        "Table of contents": "Turinys",
    },
}

_PRIMARY_NAV_SECTION_IDS = {
    "start": "__nav_1",
    "parents": "__nav_2",
    "security": "__nav_3",
    "installation": "__nav_4",
    "administration": "__nav_5",
    "reference": "__nav_8",
}

_SECTIONS = {
    "parents": {
        "en": ("Parents", "https://docs.kinkudos.app/parents/dashboard-and-child-cards/"),
        "lt": ("Tėvams", "https://docs.kinkudos.app/parents/dashboard-and-child-cards.lt/"),
    },
    "reference": {
        "en": ("Reference", "https://docs.kinkudos.app/reference/roles-and-data/"),
        "lt": ("Atmintinė", "https://docs.kinkudos.app/reference/roles-and-data.lt/"),
    },
    "security": {
        "en": ("Security", "https://docs.kinkudos.app/security/accounts-and-devices/"),
        "lt": ("Saugumas", "https://docs.kinkudos.app/security/accounts-and-devices.lt/"),
    },
    "installation": {
        "en": ("Installation", "https://docs.kinkudos.app/installation/"),
        "lt": ("Diegimas", "https://docs.kinkudos.app/installation/index.lt/"),
    },
    "administration": {
        "en": ("Administration", "https://docs.kinkudos.app/administration/"),
        "lt": ("Administravimas", "https://docs.kinkudos.app/administration/index.lt/"),
    },
    "backups.md": {
        "en": ("Backups", "https://docs.kinkudos.app/backups/"),
        "lt": ("Atsarginės kopijos", "https://docs.kinkudos.app/backups.lt/"),
    },
    "backups": {
        "en": ("Backups", "https://docs.kinkudos.app/backups/"),
        "lt": ("Atsarginės kopijos", "https://docs.kinkudos.app/backups.lt/"),
    },
    "start": {
        "de": ("Schnellstart", "https://docs.kinkudos.app/start/what-is-kinkudos.de/"),
        "en": ("Start", "https://docs.kinkudos.app/start/what-is-kinkudos/"),
        "fr": ("Démarrage rapide", "https://docs.kinkudos.app/start/what-is-kinkudos.fr/"),
        "lt": ("Pradžia", "https://docs.kinkudos.app/start/what-is-kinkudos.lt/"),
    },
}


def _language(page):
    source = page.file.src_uri
    for language in ("lt", "de", "fr"):
        if source == f"index.{language}.md" or source.endswith(f".{language}.md"):
            return language
    return "en"


def _website_data(page, language):
    names = {
        "de": "KinKudos-Dokumentation",
        "en": "KinKudos Documentation",
        "fr": "Documentation KinKudos",
        "lt": "KinKudos dokumentacija",
    }
    name = names[language]
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{page.canonical_url}#website",
        "url": page.canonical_url,
        "name": name,
        "alternateName": "KinKudos Docs",
        "inLanguage": language,
    }


def _breadcrumb_data(page, language):
    root_url = (
        "https://docs.kinkudos.app/"
        if language == "en"
        else f"https://docs.kinkudos.app/index.{language}/"
    )
    root_names = {
        "de": "KinKudos-Dokumentation",
        "en": "KinKudos Documentation",
        "fr": "Documentation KinKudos",
        "lt": "KinKudos dokumentacija",
    }
    root_name = root_names[language]
    items = [{"@type": "ListItem", "position": 1, "name": root_name, "item": root_url}]

    section_key = page.file.src_uri.split("/", 1)[0]
    section = _SECTIONS.get(section_key, {}).get(language)
    if section and section[1] != page.canonical_url:
        items.append(
            {
                "@type": "ListItem",
                "position": len(items) + 1,
                "name": section[0],
                "item": section[1],
            }
        )
    items.append(
        {
            "@type": "ListItem",
            "position": len(items) + 1,
            "name": str(page.title),
            "item": page.canonical_url,
        }
    )
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def _add_active_class(class_names, extra_classes):
    classes = class_names.split()
    for name in extra_classes:
        if name not in classes:
            classes.append(name)
    return " ".join(classes)


def _localize_primary_navigation(output, page, language):
    """Render localized primary navigation without relying on JavaScript."""
    start = output.find('<div class="md-sidebar md-sidebar--primary"')
    end = output.find('<div class="md-sidebar md-sidebar--secondary"', start)
    if start == -1 or end == -1:
        return output

    navigation = output[start:end]
    aria_labels = {"de": "Navigation", "fr": "Navigation", "lt": "Navigacija"}
    navigation = navigation.replace(
        'aria-label="Navigation"', f'aria-label="{aria_labels[language]}"'
    )
    for english, translation in _NAV_LABELS[language].items():
        navigation = re.sub(
            rf"(?<=>)(\s*){re.escape(english)}(\s*)(?=<)",
            rf"\1{translation}\2",
            navigation,
        )

    def localize_link(match):
        path = match.group("path")
        absolute = urlparse(urljoin(page.canonical_url, path)).path
        if absolute.endswith(f".{language}/"):
            return match.group(0)
        slug = absolute.rstrip("/").rsplit("/", 1)[-1]
        if language != "lt" and slug not in _QUICK_START_SLUGS:
            return match.group(0)
        if absolute == "/":
            localized = f"/index.{language}/"
        elif language == "lt" and absolute in {"/installation/", "/administration/"}:
            localized = f"{absolute}index.lt/"
        else:
            localized = f"{absolute[:-1]}.{language}/"
        return f'href="{localized}"'

    navigation = re.sub(
        r'href="(?P<path>(?!https?://|#)[^"]+/)"',
        localize_link,
        navigation,
    )

    is_quick_start_translation = page.file.src_uri.startswith("start/") or (
        page.file.src_uri.startswith("installation/guided-installer.")
    )
    section_key = (
        "start"
        if language in {"de", "fr"} and is_quick_start_translation
        else page.file.src_uri.split("/", 1)[0]
    )
    section_id = _PRIMARY_NAV_SECTION_IDS.get(section_key)
    if section_id:
        section_pattern = re.compile(
            rf'(<li class=")(?P<classes>[^"]*md-nav__item--nested[^"]*)'
            rf'(">\s*<input class="md-nav__toggle md-toggle " type="checkbox" '
            rf'id="{re.escape(section_id)}")(?P<checked> checked)?(\s*>)'
        )

        def activate_section(match):
            classes = _add_active_class(
                match.group("classes"),
                ("md-nav__item--active", "md-nav__item--section"),
            )
            return f"{match.group(1)}{classes}{match.group(3)} checked{match.group(5)}"

        navigation = section_pattern.sub(activate_section, navigation, count=1)

    current_path = urlparse(page.canonical_url).path
    for anchor in re.finditer(r'<a href="(?P<href>[^"]+)" class="md-nav__link">', navigation):
        if urlparse(urljoin(page.canonical_url, anchor.group("href"))).path != current_path:
            continue
        item_start = navigation.rfind('<li class="', 0, anchor.start())
        if item_start == -1:
            break
        class_start = item_start + len('<li class="')
        class_end = navigation.find('"', class_start)
        if class_end == -1:
            break
        classes = _add_active_class(navigation[class_start:class_end], ("md-nav__item--active",))
        navigation = navigation[:class_start] + classes + navigation[class_end:]
        break

    return output[:start] + navigation + output[end:]


def _localize_theme_ui(output, language):
    """Translate small Material UI labels that are visible on localized pages."""
    for english, translation in _UI_LABELS[language].items():
        output = re.sub(
            rf"(?<=>)(\s*){re.escape(english)}(\s*)(?=<)",
            rf"\1{translation}\2",
            output,
        )
    search = _UI_LABELS[language]["Search"]
    output = output.replace('aria-label="Search"', f'aria-label="{search}"')
    output = output.replace('placeholder="Search"', f'placeholder="{search}"')
    return output


def on_post_page(output, page, config):
    """Set HTML language and inject matching WebSite or breadcrumb JSON-LD."""
    language = _language(page)
    output = output.replace('<html lang="en"', f'<html lang="{language}"', 1)
    if language in _NAV_LABELS:
        output = _localize_primary_navigation(output, page, language)
        output = _localize_theme_ui(output, language)

    is_homepage = page.is_homepage or page.file.src_uri in {
        "index.de.md",
        "index.fr.md",
        "index.lt.md",
    }
    data = _website_data(page, language) if is_homepage else _breadcrumb_data(page, language)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    structured_data = f'<script type="application/ld+json">{payload}</script>'
    return output.replace("</head>", f"  {structured_data}\n  </head>", 1)
