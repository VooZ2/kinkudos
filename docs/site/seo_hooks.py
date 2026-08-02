"""Build-time SEO adjustments for the bilingual documentation."""

import json

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


def on_post_page(output, page, config):
    """Set HTML language and inject matching WebSite or breadcrumb JSON-LD."""
    language = _language(page)
    output = output.replace('<html lang="en"', f'<html lang="{language}"', 1)

    is_homepage = page.is_homepage or page.file.src_uri == "index.lt.md"
    data = _website_data(page, language) if is_homepage else _breadcrumb_data(page, language)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    structured_data = f'<script type="application/ld+json">{payload}</script>'
    return output.replace("</head>", f"  {structured_data}\n  </head>", 1)
