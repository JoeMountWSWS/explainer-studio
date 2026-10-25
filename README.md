# Explainer Studio

[![CI](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/explainer-studio)](https://pypi.org/project/explainer-studio/)

A command-line studio for narrated explainer videos with a clean, editorial house style.
You write a script in Markdown. The studio narrates it with local TTS, aligns every word to the audio,
and turns each scene into a [HyperFrames](https://www.npmjs.com/package/hyperframes) HTML composition
that is timed to the narration. It then renders a mastered 1920×1080 MP4 for YouTube, with captions
and chapter markers.

```
script.md ──► narration (Kokoro, local; or ElevenLabs) ──► word timings (Whisper)
          ──► scenes/<id>.html (HyperFrames + GSAP, timed to cues) ──► cached per-scene renders
          ──► out/<slug>.mp4  (−14 LUFS)  +  out/<slug>.srt  +  out/<slug>.chapters.txt
```

# Installation

## Requirements

- Linux (developed on Arch with an AMD GPU; the render uses Chromium's GPU capture)
- [uv](https://docs.astral.sh/uv/), with Python 3.12 or 3.13 (`kokoro-onnx` doesn't support 3.14 yet)
- Node.js with `npx`. The HyperFrames CLI is fetched on demand at the version pinned in `tools/studio/common.py`.
- ffmpeg and Chromium
- Optional: an ElevenLabs API key in `.env` (`ELEVENLABS_API_KEY=…`) for cloud narration

The first `sync` downloads the Kokoro-82M model to `~/.cache/hyperframes/tts` and spaCy's
`en_core_web_sm` to `~/.cache/hyperframes/spacy`.

# Usage

Making a video with the studio is a loop of writing and listening. You write the script as plain
Markdown, and the studio reads it aloud, works out exactly when each word is spoken, and hands those
timings to your scenes so the visuals move in step with the voice. Change a sentence and only that
sentence is re-recorded and only the affected scenes are re-rendered, so you can refine a five-minute
video in seconds rather than starting over. Everything runs from one command, `uv run studio`, and
nothing leaves your machine unless you choose cloud narration.

## Install

With the [requirements](#requirements) in place, either install the `studio` command from PyPI or
clone the repository.

**From PyPI**, to make videos in a folder of your own:

```bash
uv tool install explainer-studio   # or run it without installing: uvx --from explainer-studio studio …
mkdir my-videos && cd my-videos
studio new my-video "My Video"
```

The folder you run `studio` in becomes the workspace. It holds `episodes/`, `out/` and `.env`, and
`studio` finds it from any subdirectory (or set `STUDIO_ROOT`). The house style (`brand/`) and scene
templates ship with the package. To customise them, copy `brand/` or `templates/` from this repository
into the workspace, and the studio uses your copy instead. Music beds and voice clips go in the
workspace's `brand/music/` and `brand/voices/`. Use `studio` wherever this README says `uv run studio`.

**From a clone**, to work on the studio itself or to use the example episodes:

```bash
git clone git@github.com:JoeMountWSWS/explainer-studio.git
cd explainer-studio
uv sync
```

Run commands from the repository root (or any folder below it). Confirm the install with
`uv run studio --help`. The first `sync` of an episode downloads the Kokoro voice model and the
spaCy English model, so it takes a little longer than later runs.

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

The full documentation is at <https://joemountwsws.github.io/explainer-studio/>. [AGENTS.md](AGENTS.md) is the reference for coding agents: every front-matter setting, voice choice, the rules for
authoring scenes, the render pipeline and known problems. Read [brand/frame.md](brand/frame.md)
before designing scenes.

## Layout

| Path | What it is |
| --- | --- |
| `tools/studio/` | The Python CLI (`uv run studio …`) |
| `brand/` | House style shared by every episode: design spec, CSS, fonts, GSAP, pronunciations |
| `templates/` | Starter script, scene patterns and thumbnail |
| `episodes/<slug>/` | One HyperFrames project per video. `script.md` is the source of truth |
| `docs/` | The documentation site (MkDocs), including notes such as British ElevenLabs voices |
| `out/` | Rendered deliverables (gitignored) |

Worked examples: `episodes/demo-paris-commune` (Kokoro, 38s) and `episodes/demo-elevenlabs`
(the same script narrated by ElevenLabs).

## Working with coding agents

The studio is designed to be driven by Claude Code or another coding agent. `AGENTS.md` (loaded
through `CLAUDE.md`) gives the agent the conventions it needs, the HyperFrames skills cover the
composition format and motion, and the `make-explainer-video` skill
(`.claude/skills/make-explainer-video/`) walks Claude through the whole workflow. Start `claude` in
the repository root and ask for a video, or run `/make-explainer-video`. See
[Working with a coding agent](https://joemountwsws.github.io/explainer-studio/coding-agents/).
