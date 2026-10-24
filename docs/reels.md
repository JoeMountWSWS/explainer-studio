# Reels (9:16)

The same pipeline renders vertical video for Instagram Reels, TikTok and YouTube Shorts.

```yaml
---
title: France, October 17
format: reel
burn_captions: true
---
```

- `format: reel` renders at 1080×1920 instead of 1920×1080.
- `burn_captions: true` burns word-highlighted captions into the video, because most reels autoplay
  muted. White Source Sans sits on a dark box, with the spoken word in red.

Aim for **30–60 seconds**.

## Layout

Scenes use `.stage-reel` instead of `.stage`. Platform buttons sit on the right edge, and the
caption, handle and audio line take the bottom ~480px, so keep both clear.

| Area | Position |
| --- | --- |
| Content box (`.stage-reel`) | x 72–1008, y 220–1180 |
| Caption band | y 1220–1440. Don't put content here |
| Photos | May run full-bleed behind everything, under an ink gradient so type stays legible |

Minimum sizes: headline 88px, body 52px, label 30px, byline 26px.

## Writing for reels

- One statement per screen.
- Cut every 3–6 seconds, on the narration's cues.
- Get the striking fact on screen in the first second.

`episodes/france-oct17-reel/` and `episodes/iysse-trotskyism-reel/` are worked examples.
