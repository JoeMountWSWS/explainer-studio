# Getting started

## Requirements

- Linux. It was developed on Arch with an AMD GPU; the render uses Chromium's GPU capture.
- [uv](https://docs.astral.sh/uv/) with Python 3.12 or 3.13. `kokoro-onnx` doesn't support 3.14 yet.
- Node.js with `npx`. The HyperFrames CLI is fetched on demand, at the version pinned in
  `tools/studio/common.py`.
- ffmpeg and Chromium.
- Optional: an ElevenLabs API key for cloud narration (see [Narration](narration.md#elevenlabs-cloud)).

## Install

```bash
git clone git@github.com:JoeMountWSWS/explainer-studio.git
cd explainer-studio
uv sync
```

The first `sync` of an episode downloads the Kokoro-82M model to `~/.cache/hyperframes/tts`.

Every command runs as `uv run studio …` from the repository root.

## Make a video

### 1. Scaffold an episode

```bash
uv run studio new my-video "My Video"
```

This creates `episodes/my-video/` with a starter `script.md`, a `scenes/` folder and the project
files HyperFrames needs.

### 2. Write the script

```bash
$EDITOR episodes/my-video/script.md
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

```
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
