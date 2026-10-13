---
name: Explainer house style (after wsws.org)
reference: https://www.wsws.org — typography, palette and page furniture are taken from the site
canvas:
  width: 1920
  height: 1080
  fps: 30
colors:
  paper: "#ffffff"       # ground of every scene, as on the site
  panel: "#f4f4f4"       # cards, diagram fills, sidebar-style boxes
  ink: "#231f20"         # headlines, primary text, heavy section rules (logo ink)
  ink-2: "#333333"       # body copy
  ink-soft: "#555555"    # standfirsts, bylines, captions, axis labels
  rule: "#cccccc"        # hairlines between items
  red: "#e71e25"         # logo red: the single accent; ration it
  red-wash: "#ffdfdf"    # highlight wash behind a key phrase
  tag: "#1b2129"         # dark tag box ("PERSPECTIVE") with white label text
typography:
  headline: { family: "PT Serif", weight: 700, line-height: 1.12, min-size: 72px }
  standfirst: { family: "PT Serif", style: italic, weight: 400, color: ink-soft }
  body: { family: "PT Serif", weight: 400, size: 46px, line-height: 1.4 }
  label: { family: "Source Sans 3", weight: 700, size: 26px, tracking: "0.12em", case: uppercase }
  ui: { family: "Source Sans 3", weight: 600 }
  mono: { family: "JetBrains Mono", weight: 500 }   # formulae, data, code
spacing:
  safe-title: 192px 108px   # 10% inset: key text stays inside this box
  safe-action: 96px 54px    # 5% inset: nothing visible outside this box
  unit: 8px
components:
  section-rule: "6px solid ink above an uppercase label (the site's 'TOP STORIES' head)"
  hairline: "2px solid rule"
  tag: "tag-coloured box, white uppercase Source Sans label"
  blockquote: "PT Serif, indented, 6px red rule on the left"
  corners: 0
  shadow: none
motion:
  enter: "power3.out, 0.6-0.8s, rise 30-50px + fade"
  exit: "power2.in, 0.45s fade, last 0.5s of every scene"
  emphasis: "red-wash sweeps left-to-right under a phrase, 0.5s; or the phrase turns red"
  stagger: 0.12s
---

# Explainer house style (after wsws.org)

## Overview

The videos should look like a WSWS article set in motion: a white page, serious
serif headlines, small uppercase section labels, thin rules, and one red. Plain
and authoritative, not "content-marketing". The narrator carries the argument. The
frame shows its structure (claims, evidence, quotations, dates, figures) with the
same typographic furniture a reader knows from the site.

## Page furniture (reuse these in every scene)

- **Section head**: a heavy 6px `ink` rule with an uppercase `label` beneath it
  (`.section-head` in `brand.css`). Use it to name the chapter at the top of a scene.
- **Tag**: a dark `tag` box with a white uppercase label (`.tag`), like the
  site's "PERSPECTIVE" marker. Use it for categories: *Perspective*, *History*,
  *Documents*, *Statistic*.
- **Headline**: PT Serif Bold in `ink`. Sentence case, never all caps.
- **Standfirst**: PT Serif Italic in `ink-soft` under a headline.
- **Blockquote**: PT Serif with a red left rule (`.quote`), attribution in `label`
  style. Used for documents, speeches and historical sources.
- **Byline/date line**: Source Sans, `ink-soft`, small. Use it for sources and
  citations on screen ("Source: Bureau of Labor Statistics, 2025").

## The frame

- White ground (`paper`) in every scene. Scenes cut hard, and because the ground
  never changes, a cut reads as the page turning rather than the picture jumping.
- Key text lives inside the title-safe box (10% inset). Nothing visible goes outside
  the action-safe box (5% inset). Keep the bottom 15% calm, because YouTube's
  player chrome and captions sit there.
- Minimum sizes: body 44px, headline 72px. Phones are the main screen.

## Composition rules

- **One focal point.** Red goes on the single word, figure, line or arrow the
  narration is pointing at *right now*. Everything else is ink or grey.
- **Documents and evidence over decoration.** Quotations, dates, figures, maps
  and charts carry the argument. Always show a source line for a figure or quote.
- **Charts**: flat, ink and grey with the key series in red. Hairline axes, Source
  Sans labels, no gridline clutter, no 3D.
- **Lists**: at most 4 items, numbered in red Source Sans, with hairlines between.
- No stock photos used as decoration, emoji, drop shadows, rounded "app" cards,
  gradients or glow. Photos are allowed only as evidence (archival images, news
  photos with credit), set full-width with a caption, as on the site.

## Motion

- Everything that appears is triggered by the narration. Use `cue("name")` times
  from the script (`{name}` markers), not guessed seconds.
- Enter with a short rise and fade (`power3.out`). Stagger related items by 0.12s.
- Rules draw on left-to-right (`scaleX` 0 to 1).
- Hold. After a thing appears, let it sit while the narrator talks about it.
- Exit: the scene template fades its stage over the last 0.5s. Don't fight it.
