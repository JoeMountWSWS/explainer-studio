# Explainer Studio

[![CI](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/JoeMountWSWS/explainer-studio/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/JoeMountWSWS/explainer-studio/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)
[![PyPI](https://img.shields.io/pypi/v/explainer-studio)](https://pypi.org/project/explainer-studio/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://joemountwsws.github.io/explainer-studio/)

A command-line studio for narrated explainer videos with a clean, editorial house style.
You write a script in Markdown. The studio narrates it with local TTS, aligns every word to the audio,
and turns each scene into a [HyperFrames](https://www.npmjs.com/package/hyperframes) HTML composition
that is timed to the narration. It then renders a mastered 1920×1080 MP4 for YouTube, with captions
and chapter markers. It runs on Windows, Linux and macOS (macOS is untested).

```
script.md ──► narration (Kokoro, local; or ElevenLabs) ──► word timings (Whisper)
          ──► scenes/<id>.html (HyperFrames + GSAP, timed to cues) ──► cached per-scene renders
          ──► out/<slug>.mp4  (−14 LUFS)  +  out/<slug>.srt  +  out/<slug>.chapters.txt
```

# Installation

## Requirements

- Windows, Linux or macOS (macOS is untested). Per-system install commands: [Install](https://joemountwsws.github.io/explainer-studio/install/)
- [uv](https://docs.astral.sh/uv/), with Python 3.12 or 3.13 (`kokoro-onnx` doesn't support 3.14 yet)
- Node.js with `npx`. The HyperFrames CLI is fetched on demand at the version pinned in `tools/studio/common.py`.
- ffmpeg, and Chrome, Chromium or Edge for thumbnails
- Optional: an ElevenLabs API key in `.env` (`ELEVENLABS_API_KEY=…`) for cloud narration

Run `uv run studio setup` (or `studio setup` once installed) to check these and create your `.env` interactively.

The first `sync` downloads the Kokoro-82M model to `~/.cache/hyperframes/tts` and spaCy's
`en_core_web_sm` to `~/.cache/hyperframes/spacy`.

## Install the studio

With the [requirements](#requirements) in place, either install the `studio` command from PyPI or
clone the repository.

**From PyPI**, to make videos in a folder of your own:

```bash
pip install explainer-studio       # or: uv tool install explainer-studio
mkdir my-videos && cd my-videos
studio new my-video "My Video"
```

The package is on [PyPI](https://pypi.org/project/explainer-studio/). `uv tool install` puts
`studio` on your PATH in its own isolated environment, and `uvx --from explainer-studio studio …`
runs it without installing. With `pip`, install into a virtual environment (or use `pipx install
explainer-studio`) so its dependencies stay separate from your system Python.

The folder you run `studio` in becomes the workspace. It holds `episodes/`, `out/` and `.env`, and
`studio` finds it from any subdirectory (or set `STUDIO_ROOT`). The house style (`brand/`) and scene
templates ship with the package. To customise them, copy `brand/` or `templates/` from this repository
into the workspace, and the studio uses your copy instead. Music beds and voice clips go in the
workspace's `brand/music/` and `brand/voices/`. Use `studio` wherever this README says `uv run studio`.

**From a clone**, to work on the studio itself or to use the example episodes:

```bash
git clone https://github.com/JoeMountWSWS/explainer-studio.git
cd explainer-studio
uv sync
```

Run commands from the repository root (or any folder below it). Confirm the install with
`uv run studio --help`. The first `sync` of an episode downloads the Kokoro voice model and the
spaCy English model, so it takes a little longer than later runs.

### Install the agent skill

To have Claude Code drive the studio, install the `make-explainer-video` skill into your workspace:

```bash
cd my-videos
studio install-skill           # -> .claude/skills/make-explainer-video/
studio install-skill --user    # or for every project: ~/.claude/skills/
```

It installs the skill plus the references it reads (the studio guide, house-style spec and starter
script). Start `claude` in the workspace and ask for a video, or run `/make-explainer-video`. Re-run
the command with `--force` after upgrading the package to refresh it. From a clone the skill is
already available with no installation. See
[Working with a coding agent](https://joemountwsws.github.io/explainer-studio/coding-agents/).

# Usage

Making a video with the studio is a loop of writing and listening. You write the script as plain
Markdown, and the studio reads it aloud, works out exactly when each word is spoken, and hands those
timings to your scenes so the visuals move in step with the voice. Change a sentence and only that
sentence is re-recorded and only the affected scenes are re-rendered, so you can refine a five-minute
video in seconds rather than starting over. Everything runs from one command, `uv run studio`, and
nothing leaves your machine unless you choose cloud narration.

## Quick start

```bash
uv run studio new my-video "My Video"   # scaffold episodes/my-video/
# open episodes/my-video/script.md in any editor and write the script
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
(`.claude/skills/make-explainer-video/`, or `studio install-skill` for a pip install) walks Claude
through the whole workflow. Start `claude` in the repository root or your workspace and ask for a
video, or run `/make-explainer-video`. See
[Working with a coding agent](https://joemountwsws.github.io/explainer-studio/coding-agents/).
