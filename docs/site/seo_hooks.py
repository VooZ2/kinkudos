"""Small build-time SEO adjustments for the bilingual documentation."""


def on_post_page(output, page, config):
    """Set the static HTML language from the source document name."""
    is_lithuanian = page.file.src_uri == "index.lt.md" or page.file.src_uri.endswith(
        ".lt.md"
    )
    language = "lt" if is_lithuanian else "en"
    return output.replace('<html lang="en"', f'<html lang="{language}"', 1)
