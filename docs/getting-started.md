# Getting started

## Requirements

- Windows, Linux or macOS (macOS is untested).
- [uv](https://docs.astral.sh/uv/), which fetches Python 3.12 or 3.13.
- Node.js with `npx`, and ffmpeg.
- Optional: an ElevenLabs API key for cloud narration (see [Narration](narration.md#elevenlabs-cloud)).

The [Install](install.md) page has the commands for each system. Not sure what you have? Run
`studio setup --check` for a one-line-per-tool report, or `studio setup` to be walked through API keys
and the archive remote.

## Install

Follow [Install](install.md) first. This section covers the choices it leaves open.

### From PyPI

```bash
uv tool install explainer-studio   # or: pip install explainer-studio
mkdir my-videos && cd my-videos
```

The package is on [PyPI](https://pypi.org/project/explainer-studio/). `uv tool install` puts
`studio` on your PATH in its own isolated environment, and `uvx --from explainer-studio studio …`
runs it without installing. With `pip`, install into a virtual environment (or use `pipx install
explainer-studio`) so its dependencies stay separate from your system Python.

The folder you run `studio` in is the workspace: it holds `episodes/`, `out/` and `.env`. `studio`
finds it from any folder below it, or you can point at it with `STUDIO_ROOT`. The house style and
scene templates ship with the package. To customise them, copy `brand/` or `templates/` from the
repository into the workspace, and the studio uses your copy instead. Music beds and voice clips go
in the workspace's `brand/music/` and `brand/voices/`.

With an installed tool, type `studio …` wherever these docs say `uv run studio …`.

To keep your episodes in their own (for instance private) repository while working on the studio
itself, clone the studio next to the workspace and add it as an editable path dependency in the
workspace's `pyproject.toml`:

```toml
[project]
name = "my-videos"
version = "0"
requires-python = ">=3.12,<3.14"
dependencies = ["explainer-studio"]

[tool.uv]
package = false

[tool.uv.sources]
explainer-studio = { path = "../explainer-studio", editable = true }
```

`uv run studio …` in the workspace then uses the clone's code, `brand/` and `templates/`, so a
house-style change applies to every episode at once. Episode media are large: keep them in
[Git LFS](https://git-lfs.com/) in that repository.

### From a clone

```bash
git clone https://github.com/JoeMountWSWS/explainer-studio.git
cd explainer-studio
uv sync
```

Every command runs as `uv run studio …` from the repository root, or from any folder below it.

To drive the studio with Claude Code from a PyPI install, run `studio install-skill` in your workspace
(see [Working with a coding agent](coding-agents.md#installing-it)).

The first `sync` of an episode downloads the Kokoro-82M model to `~/.cache/hyperframes/tts` and
spaCy's `en_core_web_sm` to `~/.cache/hyperframes/spacy` (`~` is your home folder on every system).

## Make a video

These steps are the manual workflow. To have a coding agent do them for you, see
[Working with a coding agent](coding-agents.md).

### 1. Scaffold an episode

```bash
uv run studio new my-video "My Video"
```

This creates `episodes/my-video/` with a starter `script.md`, a `scenes/` folder and the project
files HyperFrames needs.

### 2. Write the script

Open `episodes/my-video/script.md` in any text editor. For example:

=== "Windows"

    ```powershell
    notepad episodes\my-video\script.md
    ```

=== "Linux"

    ```bash
    $EDITOR episodes/my-video/script.md
    ```

=== "macOS (untested)"

    ```bash
    open -e episodes/my-video/script.md
    ```

The starter script has five scenes and a comment explaining the format. Replace the placeholder
text with your own. See [Writing a script](script.md).

### 3. Sync

```bash
uv run studio sync my-video
```

`sync` narrates each paragraph, aligns the words to the audio, creates a scene file for every new
scene from its template, and writes `index.html` and `timing.json`. Then check the shape of the
video:

```bash
uv run studio status my-video
```

```text
  scene             template   words   est s  actual s  cues
  hook              title         41    17.9      18.2  sub
  ...
  720 words, estimated 5.2 min, actual 5.0 min (301.4s)
```

### 4. Design the scenes

Each `episodes/my-video/scenes/<id>.html` is yours to edit. Change the text, add figures, quotes and
images, and tie the animation to your `{cues}`. See [Designing scenes](scenes.md).

Preview as you go:

```bash
uv run studio preview my-video
```

This opens HyperFrames Studio in the browser, with the narration playing.

### 5. Check

```bash
uv run studio check my-video
```

This runs the HyperFrames lint, layout and contrast audits. It must report 0 errors before you
render.

### 6. Render

```bash
uv run studio render my-video --draft   # fast review copy -> out/my-video-draft.mp4
uv run studio render my-video           # final -> out/my-video.mp4, .srt, .chapters.txt
uv run studio thumbnail my-video        # out/my-video-thumbnail.jpg
```

See [Rendering and publishing](rendering.md) for what to upload.

## Where files live

| Path | What it is |
| --- | --- |
| `episodes/<slug>/script.md` | **Source of truth** for words, scene order and chapter titles |
| `episodes/<slug>/scenes/<id>.html` | One sub-composition per scene. Created from a template on first sync, then yours |
| `episodes/<slug>/index.html`, `timing.json` | **Generated.** Never hand-edit |
| `episodes/<slug>/audio/vo/` | Generated narration and `.words.json` timings |
| `episodes/<slug>/audio/recorded/` | Optional real recordings that replace TTS |
| `episodes/<slug>/assets/media/` | Your images and footage |
| `episodes/<slug>/build/` | Render cache. Safe to delete |
| `brand/` | The house style. Edit here, never in an episode's synced copy |
| `templates/` | Starter script, scene patterns and thumbnail |
| `out/` | Deliverables |

!!! tip
    Commit `audio/vo/`, `timing.json` and `index.html` after `sync`. CI never narrates or renders, so
    it relies on the committed copies.
