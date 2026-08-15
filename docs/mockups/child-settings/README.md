# Child Settings mockup (discussion)

Static visual mockup for redesigning the child **Settings** area for ages **5–14**.

## Open locally

From the repo root:

```bash
python -m http.server 8765
```

Then open [http://127.0.0.1:8765/docs/mockups/child-settings/](http://127.0.0.1:8765/docs/mockups/child-settings/).

Uses live [`static/css/app.css`](../../../static/css/app.css) theme tokens so each world keeps its real look.

## What it shows

- **5th tab** (“Spellbook” / “Den” / “HQ” / …) instead of buried Settings
- **Per-theme copy** and control chrome (rounded panda vs square blocks vs neon Blockville)
- **Visual world cards** instead of a `<select>`
- **Camera / gallery** avatar actions
- **PIN pad** for small fingers
- Side-by-side **Now vs proposed** strip (Magic Academy)

Not wired to Django — discussion only.
