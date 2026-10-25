# Organisation assets

Logos, graphics and photos of the WSWS, ICFI, SEP, IYSSE and related publishers, collected
from wsws.org (and mehring.com) on 2026-10-25 for reuse in explainer videos.
`manifest.json` lists every file with a description, its source URL and the licence the image
carries in wsws.org's own page data (`"license": "wsws"` for nearly all of them).

`studio sync` does not copy this folder into episodes, and it isn't shipped in the wheel. To use
a file, copy it into the episode and reference it from a scene:

```bash
cp brand/org/sep/logos/sep-roundel.png episodes/<slug>/assets/media/
# <img src="assets/media/sep-roundel.png">
```

## Layout

| Folder | Contents |
| --- | --- |
| `wsws/logos/` | Masthead wordmark (red mark / all black, 1600–1840 px wide), older stacked block logo, Socialism AI icon (SVG) |
| `wsws/icons/` | WS/WS monogram: **vector SVG** plus 180/192/512 px PNGs and favicon |
| `wsws/graphics/` | Default share card, diagonal-hatch tile used under section heads |
| `sep/logos/` | SEP red roundel (256 px) |
| `sep/us/congress-2026/` | Ninth National Congress (Aug 2026) title card, 6 resolution cards, 6 report cards |
| `sep/us/campaign-2024/` | Kishore/White 2024 campaign meeting cards |
| `sep/us/events/`, `photos/` | May Day 2026 rally card, rally photo |
| `sep/australia/` | 7th/8th congress cards, Victorian election card, video thumbnails, campaign/meeting photos |
| `iysse/logos/` | IYSSE logo, 320 px and 1280 px |
| `iysse/graphics/` | Dec 2022 rally card, "Thirty years of war" timeline card |
| `sgp/logos/` | Sozialistische Gleichheitspartei square logo (256 px, from wsws.org/de) |
| `mehring/logos/`, `covers/` | Mehring Books logos, three David North book covers |

The ICFI has no separate logo on wsws.org: its pages use the WSWS masthead.

## Cautions

- **Composite cards carry news photos.** The congress and campaign cards are WSWS-made, but some
  include agency or wire photos (for example Trump and Musk, ICE protests). Fine as the party's own
  graphic; don't crop the photo out and reuse it on its own.
- **Low resolution for 1080p.** `sep-roundel.png` and `sgp-logo-square.png` are 256 px and
  `iysse-logo.png` is 320 px. Use `iysse-logo-large.png`, or redraw in SVG/CSS (the roundel is a red
  circle with white bold "SEP").
- Three files are tagged `fair-use` on wsws.org although they're the organisation's own work (the large
  IYSSE logo, the 2022 rally card, the Frankfurt School cover).
- Left out as not ours: AP photos, the 1619 Project cover, archival Lenin and Trotsky photos, and the
  agency/Wikimedia photos on the ICFI history and WSWS chronology pages.

## Dead or hijacked domains (do not link or scrape)

- `iysse.com` redirects to a gambling site.
- `socialequality.org.uk` is now an SEO spam blog.
- `sgp.de` belongs to "SGP Beratung Kommunikation Design", an unrelated agency.

Credit line for scenes: `.byline` "Image: WSWS" (or the photographer, where one is known).
