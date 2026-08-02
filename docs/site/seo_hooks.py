"""Build-time SEO adjustments for the bilingual documentation."""

import json
import re
from urllib.parse import urljoin, urlparse

_LT_NAV_LABELS = {
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
    "Server": "Serveris",
    "Overview": "Apžvalga",
    "Before installing": "Prieš diegiant",
    "Updates, backups, and recovery": "Atnaujinimai, kopijos ir atkūrimas",
    "Family admin": "Šeimos administravimas",
    "Help": "Pagalba",
    "Reference": "Atmintinė",
    "Roles, data, and limits": "Vaidmenys, duomenys ir ribos",
    "Release and support policy": "Leidimų ir palaikymo politika",
}

_PRIMARY_NAV_SECTION_IDS = {
    "start": "__nav_1",
    "parents": "__nav_2",
    "security": "__nav_3",
    "server": "__nav_4",
    "reference": "__nav_7",
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
    "server": {
        "en": ("Server", "https://docs.kinkudos.app/deployment-and-maintenance/"),
        "lt": ("Serveris", "https://docs.kinkudos.app/deployment-and-maintenance.lt/"),
    },
    "start": {
        "en": ("Start", "https://docs.kinkudos.app/start/what-is-kinkudos/"),
        "lt": ("Pradžia", "https://docs.kinkudos.app/start/what-is-kinkudos.lt/"),
    },
}


def _language(page):
    source = page.file.src_uri
    return "lt" if source == "index.lt.md" or source.endswith(".lt.md") else "en"


def _website_data(page, language):
    name = "KinKudos dokumentacija" if language == "lt" else "KinKudos Documentation"
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
        "https://docs.kinkudos.app/index.lt/"
        if language == "lt"
        else "https://docs.kinkudos.app/"
    )
    root_name = "KinKudos dokumentacija" if language == "lt" else "KinKudos Documentation"
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


def _localize_primary_navigation(output, page):
    """Render Lithuanian primary navigation without relying on JavaScript."""
    start = output.find('<div class="md-sidebar md-sidebar--primary"')
    end = output.find('<div class="md-sidebar md-sidebar--secondary"', start)
    if start == -1 or end == -1:
        return output

    navigation = output[start:end]
    navigation = navigation.replace('aria-label="Navigation"', 'aria-label="Navigacija"')
    for english, lithuanian in _LT_NAV_LABELS.items():
        navigation = re.sub(
            rf"(?<=>)(\s*){re.escape(english)}(\s*)(?=<)",
            rf"\1{lithuanian}\2",
            navigation,
        )

    navigation = re.sub(
        r'href="(?P<path>(?!https?://|#)[^"]+/)"',
        lambda match: (
            match.group(0)
            if match.group("path").endswith(".lt/")
            else f'href="{match.group("path")[:-1]}.lt/"'
        ),
        navigation,
    )

    section_key = page.file.src_uri.split("/", 1)[0]
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
            return (
                f'{match.group(1)}{classes}{match.group(3)} checked{match.group(5)}'
            )

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
        classes = _add_active_class(
            navigation[class_start:class_end], ("md-nav__item--active",)
        )
        navigation = navigation[:class_start] + classes + navigation[class_end:]
        break

    return output[:start] + navigation + output[end:]


def on_post_page(output, page, config):
    """Set HTML language and inject matching WebSite or breadcrumb JSON-LD."""
    language = _language(page)
    output = output.replace('<html lang="en"', f'<html lang="{language}"', 1)
    if language == "lt":
        output = _localize_primary_navigation(output, page)

    is_homepage = page.is_homepage or page.file.src_uri == "index.lt.md"
    data = _website_data(page, language) if is_homepage else _breadcrumb_data(page, language)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    structured_data = f'<script type="application/ld+json">{payload}</script>'
    return output.replace("</head>", f"  {structured_data}\n  </head>", 1)
