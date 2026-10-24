---
name: make-explainer-video
description: Make a narrated explainer video (YouTube landscape or 9:16 reel) with this studio. Use when asked to create, script, narrate, design scenes for, preview, check, render or thumbnail an episode under episodes/, or to fix a failing `studio check` or render.
---

# Make an explainer video with the studio

Pipeline: `script.md` → local TTS → word timings → one HyperFrames scene per script section → cached renders → mastered MP4, `.srt` and chapters in `out/`. All commands run from the studio root as `uv run studio <cmd> <slug>`.

`AGENTS.md` is the full reference (script settings, TTS engines, gotchas). `brand/frame.md` is the design spec. Read `frame.md` before designing any scene, and load the `hyperframes-core` and `hyperframes-animation` skills for the composition contract and motion. Don't restate them from memory.

## Workflow

1. **Scaffold**: `uv run studio new <slug> "Title"` creates `episodes/<slug>/`. Read `templates/script.md` and the worked example `episodes/demo-paris-commune/`.
2. **Write `script.md`** (the only source of truth for words, scene order and chapters):
   - Front matter: `title`, `voice`, `speed`; `format: reel` and `burn_captions: true` for 9:16.
   - One `## <id>: <chapter title>` per scene, then `> template: title|blank|stat|quote|points|outro`, optional `> duration: n` (required if a scene has no narration), then narration. Other `>` lines are visual notes and are never spoken.
   - `{name}` marks a cue the visuals can hit; `{pause n}` adds a beat.
   - Open on a question, contrast or striking fact in the first 5–10s. About 150–165 wpm: 5 min ≈ 700–750 words. Three main sections beat seven, and each needs a re-hook. Aim for 30–60s for a reel.
   - Write numbers and abbreviations as they should be spoken, or add a respelling to `pronounce:`.
   - YouTube chapters need at least 3, each 10s or longer. Consecutive scenes with the same title merge.
3. **Sync**: `uv run studio sync <slug>` narrates, aligns, stubs `scenes/<id>.html` from the templates and writes `index.html` and `timing.json`. `uv run studio status <slug>` shows words, estimated and actual length, and cues per scene. Fix length and pacing in the script, then re-sync. Only changed paragraphs are re-narrated.
4. **Design each scene** in `episodes/<slug>/scenes/<id>.html`. Rules:
   - Keep the `/* <studio:timing> */` block; `sync` rewrites it. Time animation with `cue("name", fallback)` and `T.*`, never hard-coded seconds.
   - Prefix every id and class with the scene id. The root is `#root`. Keep the script in its IIFE.
   - Use `gsap.fromTo` for entrances, and no CSS `transform` on anything GSAP moves.
   - Start with `<div class="paper">`, put content in `.stage` (or `.stage-reel`), and keep the final 0.5s exit fade (not on the outro).
   - Put images in `assets/media/` and reference them as `assets/media/x.jpg`. Every figure, quote and photo gets a `.byline` source line.
   - One idea on screen at a time, triggered by the narration. Use brand classes from `brand/brand.css`, with red on a single focal element.
   - Changing `> template:` on an existing scene does nothing. Delete the scene file to re-stub it.
   - Edit `brand/` for house-style changes, never `episodes/<slug>/assets/brand/` (a synced copy).
5. **Review**: `uv run studio preview <slug>` opens HyperFrames Studio with narration. For a look without a browser, run `npx hyperframes snapshot episodes/<slug> --at 12.5,40` and view the frames.
6. **Check**: `uv run studio check <slug>` must pass with 0 errors (lint, layout, contrast) before any render.
7. **Render**: `uv run studio render <slug> --draft` for a review copy, then `uv run studio render <slug>` for `out/<slug>.mp4`, `.srt` and `.chapters.txt`. Only changed scenes re-render, and `--force [ids]` forces them. A full render takes about real time. Optionally run `uv run studio thumbnail <slug>` after editing `thumbnail/thumbnail.html`.

## Voice

Default is Kokoro (local, free). `uv run studio voices <slug>` writes loudness-matched samples to `out/voice-samples/` for choosing a voice or blend. Kokoro ignores SSML, so punctuation is the only delivery control. `tts: chatterbox` (voice cloning) and `tts: elevenlabs` (billed per character, key in `.env`; never read or print `.env`) are described in `AGENTS.md`. Ask before switching to a paid engine. Changing any voice setting re-narrates everything.

## Gotchas

- `index.html` and `timing.json` are generated; never hand-edit them.
- Add `audio/recorded/<id>.wav|flac|m4a|mp3` to replace TTS for one scene.
- A crashed render can leave `_render_*.html` in the episode; delete it.
- DNS errors on downloads: `resolvectl flush-caches`.
- Commit `audio/vo/`, `timing.json` and `index.html` after `sync`, because CI never narrates. Commit messages use `episode:` for episode content and `brand:` for the house style.

## Music

Also write a song description for a music generation service such as Suno: genre, mood, tempo, instrumentation, and "instrumental, no vocals" for a bed under narration. Match the episode's tone and length, and give it to the user alongside the script.

## Done means

`studio check` passes, a draft render has been made and its frames spot-checked, and the final render and `out/` files exist. Report the paths.
