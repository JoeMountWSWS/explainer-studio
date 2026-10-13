# Explainer video studio

Command-line studio for narrated explainer videos (~5 min, 1920x1080 30fps, for YouTube),
styled after **wsws.org**. Pipeline: `script.md` → local TTS narration → word-aligned timing →
one HyperFrames sub-composition per scene → cached per-scene renders → mastered MP4, captions
and chapters in `out/`.

## Quick start

```bash
uv run studio new <slug> "Title"     # scaffold episodes/<slug>/
$EDITOR episodes/<slug>/script.md    # write the script (format below)
uv run studio sync <slug>            # narrate + align + stub scenes + write index.html
uv run studio status <slug>          # word counts, est vs actual length, cues per scene
# design each scenes/<id>.html (see "Authoring scenes")
uv run studio preview <slug>         # HyperFrames Studio in the browser (with narration)
uv run studio check <slug>           # lint + layout + contrast audits; must pass
uv run studio render <slug> --draft  # fast review copy -> out/<slug>-draft.mp4
uv run studio render <slug>          # final -> out/<slug>.mp4 + .srt + .chapters.txt
uv run studio thumbnail <slug>       # out/<slug>-thumbnail.jpg (edit thumbnail/thumbnail.html)
```

`episodes/demo-paris-commune/` is a complete worked example (38s, 4 scenes).

## Layout

- `brand/`: the house style, shared by every episode. **Edit here, never in an episode's copy.**
  - `frame.md`: design spec (tokens in front matter, rules in prose). Read before designing a scene.
  - `brand.css`: fonts, colour tokens and page furniture classes (`.section-head`, `.tag`, `.headline`, `.standfirst`, `.quote`, `.byline`, `.hl`…).
  - `fonts/`: PT Serif + Source Sans 3 (as on wsws.org) and JetBrains Mono, all OFL. `vendor/gsap.min.js` (no CDN at render time).
  - `pronunciations.yaml`: studio-wide TTS respellings (acronyms, names).
  - `music/`: optional music beds.
- `templates/scenes/*.html`: scene patterns: `title`, `blank`, `stat`, `quote`, `points`, `outro`. `templates/script.md` is the starter script and `templates/thumbnail.html` the thumbnail.
- `tools/studio/`: the Python CLI (`uv run studio …`).
- `episodes/<slug>/`: one HyperFrames project per video.
  - `script.md`: **source of truth** for words, scene order and chapter titles.
  - `scenes/<id>.html`: one sub-composition per scene. Created from a template on first sync, then yours.
  - `index.html`, `timing.json`: **generated**. Never hand-edit.
  - `audio/vo/`: generated narration plus `.words.json` timings. `audio/tts/`: TTS cache.
  - `audio/recorded/<id>.wav|flac|m4a|mp3`: optional real recording that replaces TTS for that scene.
  - `assets/brand/`: synced copy of `brand/`. `assets/media/`: episode images and footage.
  - `build/`: render cache (safe to delete).
- `out/`: deliverables.

## Script format (`episodes/<slug>/script.md`)

```markdown
---
title: The Paris Commune
voice: bf_emma*0.6 + bf_isabella*0.4   # Kokoro voice or weighted blend (UK: bf_*, bm_*; US: af_*, am_*)
speed: 0.85
music: brand/music/bed.mp3  # optional, ducked under the voice
pronounce: { Engels: Engles }
---
## hook: Seventy-two days          <- "## <id>: <chapter title>"
> template: title                  <- pattern for a NEW scene file
> duration: 4                      <- optional minimum length (required if no narration)
> Any other quoted line is a visual note, never spoken.

Narration paragraph. {sub} A cue: the scene can act exactly when the next word is spoken.
Next paragraph (blank line = short pause). {pause 1.5} An explicit pause.
```

- Scene ids: lowercase, start with a letter, `a-z0-9-`. Consecutive scenes with the same title merge into one YouTube chapter. YouTube needs at least 3 chapters, each 10s or longer; `render` warns when they aren't.
- Write numbers and abbreviations as they should be **spoken** when the voice gets them wrong, or add a respelling to `pronounce:`. Captions always use the script's spelling.
- **Kokoro voice.** `voice:` takes one voice or a weighted blend (`a*0.6 + b*0.4`) of their style vectors. Blends sound less synthetic than single voices. By Kokoro's own grades, `bf_emma` (B-) is the best UK voice and the UK male voices are C or lower. Audition with `uv run studio voices <slug> [--scene id] [--speed 0.85] [--voices "spec" ...]`, which writes loudness-matched samples to `out/voice-samples/`. Speed is relative to each voice: aim for ~150–170 wpm.
- **Kokoro delivery.** Phonemes come from **misaki** (`g2p: misaki`, the G2P Kokoro was trained on: proper RP vowels, "1871" read as a year) rather than espeak (`g2p: espeak`). Each sentence is a separate utterance, so each one gets its own falling intonation; they're joined by `sentence_pause` (0.38s). Kokoro ignores SSML and emotion tags, so punctuation is the only lever: commas for breaths, full stops for resets, `?` for questions, and `{pause n}` for a beat. `voice_fx: true` adds a gentle EQ, de-ess, compressor and faint room (`VOICE_FX` in `voice.py`). Any of these settings change re-synthesises the narration.
- **ElevenLabs** instead of Kokoro: set `tts: elevenlabs` and `voice: <ElevenLabs voice ID>`. Optional: `tts_model` (default `eleven_multilingual_v2`) and `voice_settings: {stability, similarity_boost, style}`; `speed` is passed through (0.7–1.2). The key is read from `ELEVENLABS_API_KEY`, in the environment or in `.env` at the studio root (never commit it). It costs about 1 credit per character. Chunks are cached like Kokoro's, so only new or changed paragraphs are billed, and `sync` prints the characters it used. British voice picks: `docs/elevenlabs-voices.md`.
- Settings that can go in the front matter, with their defaults (`tools/studio/common.py`): `tts kokoro`, `g2p misaki`, `sentence_pause 0.38`, `clause_pause 0.12`, `voice_fx true`, `fps 30`, `pad_in 0.6`, `pad_out 0.9`, `paragraph_gap 0.45`, `music_db -24`, `loudness -14`, `true_peak -1.5`.

## Authoring scenes (`scenes/<id>.html`)

Read `brand/frame.md` first, and use the `hyperframes-core` and `hyperframes-animation` skills for the composition contract and motion. Rules specific to this studio:

- Keep the `/* <studio:timing> */ … /* </studio:timing> */` block. `sync` rewrites it with `T = {duration, voStart, voEnd, cues, paragraphs}` (scene-local seconds). Time animation with `cue("name", fallback)` and `T.*`, never hard-coded guesses, so re-recording narration re-times the visuals.
- Prefix every id and scene-local class with the scene id (`#lesson-quote`) because all scenes share one page in preview. Style the root as `#root`. Keep the script in its IIFE.
- Use `gsap.fromTo` for entrances, and no CSS `transform` on anything GSAP moves. Start each scene with `<div class="paper">` and content in `.stage` (title-safe). Keep the final 0.5s exit fade (except the outro).
- Images and footage go in `assets/media/` and are referenced as `assets/media/x.jpg`. Show a source/credit line (`.byline`) for every figure, quote and photo.
- Changing `> template:` after a scene file exists does nothing. Delete the scene file to re-stub it.
- Before rendering, `uv run studio check <slug>` must pass with 0 errors. Spot-check frames with
  `npx hyperframes snapshot episodes/<slug> --at 12.5,40` and look at them.

## Rendering and output

- Each scene renders separately, keyed on its HTML, assets, duration and quality, so only changed scenes re-render. `--force [ids]` re-renders explicitly. Scenes are concatenated losslessly. The voice track is built from `audio/vo/` and the music bed is ducked under it (sidechain). Audio is mastered to **−14 LUFS / −1.5 dBTP** (two-pass loudnorm), AAC 48 kHz.
- `out/<slug>.srt`: upload as YouTube subtitles; captions are not burned in. `out/<slug>.chapters.txt`: paste into the description.
- Speed on this machine (RX 580, GPU beginframe capture): a full render runs at about real time, and a single-scene change takes seconds.

## Writing for this format (research notes, Oct 2026)

- The first 5–10 seconds decide retention. Open on a question, contrast or striking fact, never "welcome to the channel". Then say what the video will explain.
- ~150–165 words a minute (the default Kokoro blend at speed 0.85 measures ~165; `bm_george` at 1.0 ~155). 5 minutes ≈ 700–750 words. Leave visual breathing room.
- Three main sections beat seven. Re-hook at each section change, and keep a payoff for the end.
- One idea on screen at a time, triggered by the narration. Diagrams, documents and figures carry the argument; bullets are a last resort.
- Keep the right ~45% of the last 5–20s clear for YouTube end-screen elements (the `outro` template does this).

## Tools

- **HyperFrames** CLI pinned at `HF_VERSION` in `tools/studio/common.py` (override with `STUDIO_HF_VERSION`). To upgrade, bump it, run `studio check` on an episode, and compare a draft render.
- **Kokoro-82M** TTS runs in-process from the studio venv; the model is cached in `~/.cache/hyperframes/tts`. English phonemes come from misaki plus spaCy `en_core_web_sm` (pinned in `pyproject.toml`; installed without `misaki[en]`, whose extra pulls in ~5 GB of torch for the unused transformer model). **Whisper** (`hyperframes transcribe`, small.en) gives word timings, which are aligned back onto the script text. `npx hyperframes models install parakeet` is faster and more accurate, and is used automatically once installed.
- **ElevenLabs** (optional cloud TTS, `tts: elevenlabs`): stdlib HTTPS calls from `tools/studio/voice.py`, sending each paragraph with its neighbours' text so the delivery stays continuous.
- **CI** (`.github/workflows/ci.yml`): `uv sync --locked`, ruff (`[tool.ruff]` in `pyproject.toml`), a CLI smoke test, and `hyperframes check` on every episode. It never narrates or renders, so commit `audio/vo/`, `timing.json` and `index.html` after `sync`.
- ffmpeg 9, Chromium (thumbnails), uv (Python 3.12–3.13; `kokoro-onnx` needs <3.14).

## Gotchas

- Only one root-level HTML file may carry `data-composition-id`. `render` creates `_render_<id>.html` shells temporarily and deletes them; if a crash leaves one behind, delete it.
- If package or model downloads fail with DNS errors (NordVPN + DNSSEC "signature-expired"), run `resolvectl flush-caches`.
- If a render hangs or reports empty frames under GPU capture, add `--no-browser-gpu` in `render_scenes()` (`tools/studio/render.py`).
