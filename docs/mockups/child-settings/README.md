# Child Settings mockup (discussion)

Static visual mockup: **same child dashboard structure**, only the **last Settings segment** is redesigned for ages **5–14**, with per-theme cards/copy.

## Open

```bash
python -m http.server 8765 --bind 0.0.0.0
```

- Full page: `/docs/mockups/child-settings/?theme=magic_academy`
- Settings block only (screenshots): `?theme=panda_pet&focus=settings`

On a real phone (narrow viewport) the nested phone chrome drops away; theme chips stay sticky.

Uses live [`static/css/app.css`](../../../static/css/app.css).

## What stays the same

- Hero: greeting + balance orb on one row
- 4-tab tabbar (Tasks / Rewards / Goals / History — themed labels)
- Content above Settings (stub task card in the mock)

## What changes

- Settings segment only: visual world cards, camera/gallery avatar, birthday, PIN pad, themed copy
