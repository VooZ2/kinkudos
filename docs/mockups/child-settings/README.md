# Child Settings mockup (discussion)

Static visual mockup: **same child dashboard structure**, only the **last Settings segment** is redesigned for ages **5–14**, with per-theme cards/copy.

## Open

```bash
python -m http.server 8765 --bind 0.0.0.0
```

- Full page: `/docs/mockups/child-settings/?theme=magic_academy`
- Settings block only (screenshots): `?theme=panda_pet&focus=settings`

On a real phone (narrow viewport) the nested phone chrome drops away; theme chips stay sticky.

## Languages

Use the **LT / EN** toggle (or `?lang=lt` / `?lang=en`). Settings strings are theme-flavoured in both languages; nav labels follow existing product translations from `locale/lt/LC_MESSAGES/django.po` where available.

Copy source: [`copy.js`](copy.js).

## What stays the same

- Hero: greeting + balance orb on one row
- 4-tab tabbar (Tasks / Rewards / Goals / History — themed labels)
- Content above Settings (stub task card in the mock)

## What changes

- Settings segment only, as an **accordion** (one row open at a time)
- Visual world cards in a **2×4 grid**: 7 themes + 8th “Surprise world” (daily random)
- Camera/gallery avatar, birthday, PIN pad with 3-step checklist
