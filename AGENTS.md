# Explainer video studio

Command-line studio for narrated explainer videos (~5 min, 1920x1080 30fps, for YouTube),
with a clean editorial house style. Pipeline: `script.md` → local TTS narration → word-aligned timing →
one HyperFrames sub-composition per scene → cached per-scene renders → mastered MP4, captions
and chapters in `out/`.

## First-time setup (start here)

The goal is to take someone who has never used this tool from zero to a finished video, so assume they are
not technical: explain each step in plain words, one at a time, and don't dump command output on them.

1. Run `uv run studio setup --check` yourself. Each line is `ok|missing|optional  <name>  <hint>`, and it exits 1 only if
   ffmpeg, ffprobe or npx is missing. Explain what is missing and why, and offer to run the install command (ask first).
2. The interactive wizard asks about API keys and the archive remote, which you cannot answer and must never see. Ask the
   user to run it themselves by typing `! uv run studio setup`. It tests an ElevenLabs key without spending credits, writes
   `.env` (owner-only) and offers to download the narration models. Never read, print or ask them to paste `.env` or a key.
3. Re-run `studio setup --check` to confirm. No ElevenLabs key is fine: Kokoro narration is local and free, so don't
   push the paid engine.
4. Then offer a guided first episode: look at `episodes/demo-paris-commune/` together, `studio new <slug> "Title"`,
   help write `script.md` (see "Writing for this format"), `sync`, `preview`, `check`, a `--draft` render, then the final render.

## Quick start

```bash
uv run studio setup                  # first run: check tools, ask questions, write .env (`--check` = report only)
uv run studio new <slug> "Title"     # scaffold episodes/<slug>/
$EDITOR episodes/<slug>/script.md    # write the script (format below)
uv run studio sync <slug>            # narrate + align + stub scenes + write index.html
uv run studio status <slug>          # word counts, est vs actual length, cues per scene
# design each scenes/<id>.html (see "Authoring scenes")
uv run studio preview <slug>         # HyperFrames Studio in the browser (with narration)
uv run studio check <slug>           # lint + layout + contrast audits; must pass
uv run studio render <slug> --draft  # fast review copy -> out/<slug>-draft.mp4
uv run studio render <slug>          # final -> out/<slug>.mp4 + .srt + .chapters.txt
uv run studio music <slug> --prompt "..."  # ElevenLabs Music bed sized to the synced episode (after sync)
uv run studio thumbnail <slug>       # out/<slug>-thumbnail.jpg (edit thumbnail/thumbnail.html)
uv run studio archive <slug>         # copy the master, captions and thumbnail to $STUDIO_ARCHIVE (rclone)
```

`episodes/demo-paris-commune/` is a complete worked example (38s, 4 scenes).

## Layout

- `brand/`: the house style, shared by every episode. **Edit here, never in an episode's copy.**
  - `frame.md`: design spec (tokens in front matter, rules in prose). Read before designing a scene.
  - `brand.css`: fonts, colour tokens and page furniture classes (`.section-head`, `.tag`, `.headline`, `.standfirst`, `.quote`, `.byline`, `.hl`…).
  - `fonts/`: PT Serif + Source Sans 3 and JetBrains Mono, all OFL. `vendor/gsap.min.js` (no CDN at render time).
  - `pronunciations.yaml`: studio-wide TTS respellings (acronyms, names).
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
- **Content workspace.** This repo is public and holds only the tool, the house style, templates and the `demo-*` episodes. Real episodes, draft scripts, music beds (`brand/music/`) and org assets (`brand/org/`, `brand/logo/`) live in the private `JoeMountWSWS/sep-episodes`, cloned next to this one (`../sep-episodes`). It runs this checkout as an editable path dependency, keeps its media in Git LFS, and archives finished masters with `studio archive`. Never add episode content here. `require_media()` (`common.py`) stops `sync`, `preview`, `check` and `render` with a `git lfs pull` hint when a workspace's media are still LFS pointers.
- **Workspace.** `ROOT` (`tools/studio/common.py`) is `$STUDIO_ROOT`, else the nearest folder at or above the cwd that has `episodes/`, else the cwd. `BRAND` and `TEMPLATES` are the workspace's `brand/` and `templates/` when present (as in this repo), else the copies bundled in the package (`PKG_DATA`, `studio/data/` in the wheel). `brand/music/`, `brand/voices/` and `brand/fonts-licensed/` are always workspace paths.

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
- **Chatterbox** (Resemble AI, local, voice cloning): set `tts: chatterbox` and `voice: brand/voices/<name>.wav`, a reference clip (path relative to the studio root) or `default` for the model's built-in American voice. The clip must be **over 5s** (10–15s is best), clean, dry, mono speech with no music, in the accent and pace you want: pacing comes from the clip, and `speed` is ignored. `chatterbox_model: turbo` (default, 350M, English) or `standard` (500M), which also honours `exaggeration` (0.5; higher is more animated) and `cfg_weight` (0.5; lower is slower and more deliberate). Both use `temperature` (0.8) and `seed` (0, so a re-synthesis repeats). Text goes to the model in sentence groups of up to ~280 characters, joined by `sentence_pause`; a longer sentence is split at clause breaks (`, ; : —`), joined by `clause_pause`, and `voice_fx` applies as with Kokoro. The first run builds its environment and downloads the model (~1–2 GB). It runs on the CPU (~4–5× slower than real time here), but cached chunks are reused, so only changed paragraphs are re-synthesised. Re-recording the clip re-synthesises everything. Output carries Resemble's inaudible Perth watermark. `studio voices <slug>` with `tts: chatterbox` auditions every `brand/voices/*.wav` plus `default`, or the clips given with `--voices`.
- **Music** (`uv run studio music <slug> --prompt "…"`): an instrumental bed from the ElevenLabs Music API (`POST /v1/music`, `force_instrumental`), sized to `timing.json` (run `sync` first) and cached by prompt, length and model in `audio/music/`. Needs `ELEVENLABS_API_KEY` with the `music_generation` permission (a 401 naming it means the key lacks it) and a paid plan for commercial use. About $0.0083 per second (third-party figure). `--variants N` makes takes to audition, `--out brand/music/x.mp3` shares one across episodes, `--model` picks `music_v1|v2|v2_5`. Describe genre, mood, tempo and instruments; never name artists or songs. Then set `music:` and log the track in `brand/music/CREDITS.md`. Code: `tools/studio/music.py`; the HTTP/retry helper `elevenlabs_post` is shared with narration in `voice.py`.
- **Reels** (9:16 for Instagram, TikTok and Shorts): `format: reel` renders at 1080x1920, and `burn_captions: true` burns word-highlighted captions into the video (most reels autoplay muted). Scenes use `.stage-reel`; see the "Reel" section of `brand/frame.md` for safe zones. Aim for 30–60s.
- Settings that can go in the front matter, with their defaults (`tools/studio/common.py`): `format landscape` (or `reel`), `burn_captions false`, `tts kokoro` (or `chatterbox`, `elevenlabs`), `g2p misaki`, `sentence_pause 0.38`, `clause_pause 0.12`, `voice_fx true`, `chatterbox_model turbo`, `exaggeration 0.5`, `cfg_weight 0.5`, `temperature 0.8`, `seed 0`, `fps 30`, `pad_in 0.6`, `pad_out 0.9`, `paragraph_gap 0.45`, `music_prompt` (default prompt for `studio music`), `music_db -24`, `music_fade_in 2`, `loudness -14`, `true_peak -1.5`.

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
- **Kokoro-82M** TTS runs in-process from the studio venv; the model is cached in `~/.cache/hyperframes/tts`. English phonemes come from misaki plus spaCy `en_core_web_sm`, which PyPI won't accept as a direct-URL dependency, so `voice.ensure_spacy_model()` unpacks the pinned wheel into `~/.cache/hyperframes/spacy` on first use (misaki is installed without `misaki[en]`, whose extra pulls in ~5 GB of torch for the unused transformer model). **Whisper** (`hyperframes transcribe`, small.en) gives word timings, which are aligned back onto the script text. `npx hyperframes models install parakeet` is faster and more accurate, and is used automatically once installed.
- **Chatterbox** (optional local TTS, `tts: chatterbox`): pins torch and numpy<2, so it can't share the studio venv. On first use, `voice.Chatterbox` builds a separate venv at `~/.cache/hyperframes/chatterbox/<version>` (`uv pip install --torch-backend cpu`, plus `setuptools<81` for the watermarker's `pkg_resources` import) and drives `tools/studio/chatterbox_worker.py` over JSON lines on stdin/stdout. The version is pinned at `CHATTERBOX_VERSION` in `common.py` (override with `STUDIO_CHATTERBOX_VERSION`), and the weights are cached in `~/.cache/huggingface`. Delete the venv folder to rebuild it. No GPU: the RX 580 has no CUDA, and ROCm doesn't support it.
- **ElevenLabs** (optional cloud TTS, `tts: elevenlabs`): stdlib HTTPS calls from `tools/studio/voice.py`, sending each paragraph with its neighbours' text so the delivery stays continuous.
- **Tests**: `uv run pytest` (`tests/`, with coverage; settings and the `fail_under` floor in `[tool.coverage]` in `pyproject.toml`). No TTS or HyperFrames needed: the `fake_tts` fixture narrates, and `monkeypatch` points `studio.common` paths at `tmp_path`. The audio-mixing tests run real ffmpeg (installed in CI) and skip without it. Add or update tests with every CLI change. See `docs/contributing.md`.
- **CI** (`.github/workflows/ci.yml`): `uv sync --locked`, ruff (`[tool.ruff]` in `pyproject.toml`), pytest with coverage (3.12 and 3.13; table in the run summary, `coverage` artifact, a coverage comment on PRs and the README badge via py-cov-action), a CLI smoke test, and `hyperframes check` on every episode. It never narrates or renders, so commit `audio/vo/`, `timing.json` and `index.html` after `sync`.
- **Releases** (`.github/workflows/release-please.yml`, `release-please-config.json`): release-please turns Conventional Commit messages into a release PR (version in `pyproject.toml` + `uv.lock`, `CHANGELOG.md`); merging it tags, publishes the GitHub release and uploads to PyPI (trusted publishing; see `RELEASING.md`). Only `brand/` files listed under `force-include` in `pyproject.toml` ship in the wheel. Write commit messages as `feat:`, `fix:`, `perf:`, `episode:` (episode content), `brand:` (house style), `docs:`, `deps:`, or `refactor:`/`test:`/`ci:`/`chore:` (not in the changelog). Never hand-edit the version or `CHANGELOG.md`.
- ffmpeg 9, Chromium (thumbnails), uv (Python 3.12–3.13; `kokoro-onnx` needs <3.14).

## Gotchas

- Only one root-level HTML file may carry `data-composition-id`. `render` creates `_render_<id>.html` shells temporarily and deletes them; if a crash leaves one behind, delete it.
- If package or model downloads fail with DNS errors (NordVPN + DNSSEC "signature-expired"), run `resolvectl flush-caches`.
- If a render hangs or reports empty frames under GPU capture, add `--no-browser-gpu` in `render_scenes()` (`tools/studio/render.py`).
- **DINPro** (the sans: labels, tags, bylines, captions) is a licensed FontFont, not OFL. Its TTFs live in gitignored `brand/fonts-licensed/` and must never be committed or moved into `brand/fonts/` (the repo is public and `brand/fonts/` ships in the wheel). Without them everything falls back to Source Sans 3. This build's `fi`/`fl` ligatures are broken, so `brand.css` turns common ligatures off and burned-in captions insert a zero-width non-joiner.
