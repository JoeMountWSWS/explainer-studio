# Explainer Studio

[![CI](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml)

A command-line studio for narrated explainer videos in the style of [wsws.org](https://www.wsws.org).
You write a script in Markdown. The studio narrates it with local TTS, aligns every word to the audio,
and turns each scene into a [HyperFrames](https://www.npmjs.com/package/hyperframes) HTML composition
that is timed to the narration. It then renders a mastered 1920×1080 MP4 for YouTube, with captions
and chapter markers.

```
script.md ──► narration (Kokoro, local; or ElevenLabs) ──► word timings (Whisper)
          ──► scenes/<id>.html (HyperFrames + GSAP, timed to cues) ──► cached per-scene renders
          ──► out/<slug>.mp4  (−14 LUFS)  +  out/<slug>.srt  +  out/<slug>.chapters.txt
```

## Requirements

- Linux (developed on Arch with an AMD GPU; the render uses Chromium's GPU capture)
- [uv](https://docs.astral.sh/uv/), with Python 3.12 or 3.13 (`kokoro-onnx` doesn't support 3.14 yet)
- Node.js with `npx`. The HyperFrames CLI is fetched on demand at the version pinned in `tools/studio/common.py`.
- ffmpeg and Chromium
- Optional: an ElevenLabs API key in `.env` (`ELEVENLABS_API_KEY=…`) for cloud narration

```bash
uv sync
```

The first `sync` downloads the Kokoro-82M model to `~/.cache/hyperframes/tts`.

## Quick start

```bash
uv run studio new my-video "My Video"   # scaffold episodes/my-video/
$EDITOR episodes/my-video/script.md     # write the script
uv run studio sync my-video             # narrate, align, stub scene files, write index.html
uv run studio status my-video           # words, estimated vs actual length, cues per scene
# design each episodes/my-video/scenes/<id>.html
uv run studio preview my-video          # HyperFrames Studio in the browser, with narration
uv run studio check my-video            # lint, layout and contrast audits (must pass)
uv run studio render my-video --draft   # quick review copy -> out/my-video-draft.mp4
uv run studio render my-video           # final -> out/my-video.mp4 + .srt + .chapters.txt
uv run studio thumbnail my-video        # out/my-video-thumbnail.jpg
uv run studio voices my-video           # audition Kokoro voice blends -> out/voice-samples/
```

Only scenes that have changed are re-rendered. Changing a paragraph of narration re-synthesises
that paragraph and nothing else, and re-times the visuals that depend on it.

## Writing a script

```markdown
---
title: The Paris Commune
voice: bf_emma*0.6 + bf_isabella*0.4
speed: 0.85
---
## hook: Seventy-two days
> template: title

In the spring of 1871, the working class took power in a major city. {sub} This is the story of the Paris Commune.
```

Each `## id: Chapter title` heading is a scene and a YouTube chapter. `> template:` chooses the
starting pattern for the scene file (`title`, `stat`, `quote`, `points`, `outro`, `blank`). Other `>`
lines are visual notes and are never spoken. `{name}` marks a cue that the scene can animate on,
and `{pause 1.5}` inserts a pause.

[AGENTS.md](AGENTS.md) is the full reference: every front-matter setting, voice choice, the rules for
authoring scenes, the render pipeline and known problems. Read [brand/frame.md](brand/frame.md)
before designing scenes.

## Layout

| Path | What it is |
| --- | --- |
| `tools/studio/` | The Python CLI (`uv run studio …`) |
| `brand/` | House style shared by every episode: design spec, CSS, fonts, GSAP, pronunciations |
| `templates/` | Starter script, scene patterns and thumbnail |
| `episodes/<slug>/` | One HyperFrames project per video. `script.md` is the source of truth |
| `docs/` | Notes, such as British ElevenLabs voices |
| `out/` | Rendered deliverables (gitignored) |

Worked examples: `episodes/demo-paris-commune` (Kokoro, 38s) and `episodes/demo-elevenlabs`
(the same script narrated by ElevenLabs).

## Working with coding agents

The studio is designed to be driven by Claude Code or another coding agent. `AGENTS.md` (loaded
through `CLAUDE.md`) gives the agent the conventions it needs, and the HyperFrames skills cover the
composition format and motion.

## CI

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs on every push to
`main` and on every pull request:

- `uv sync --locked`, `ruff check`, and a CLI smoke test (`status` on every episode, plus `new`)
- `hyperframes check` on every episode, at the pinned HyperFrames version

CI doesn't narrate or render. It checks the narration, timings and scenes that are committed.

## Licence

The studio software is released under the [MIT licence](LICENSE). Editorial content (everything
under `episodes/` and `scripts/`) is © World Socialist Web Site, all rights reserved. Fonts (SIL OFL
1.1), GSAP (GreenSock Standard License) and third-party photographs keep their own terms. See
[LICENSE](LICENSE) for the details.
