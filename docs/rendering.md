# Rendering and publishing

```bash
uv run studio render my-video --draft   # fast review copy -> out/my-video-draft.mp4
uv run studio render my-video           # final -> out/my-video.mp4 + .srt + .chapters.txt
uv run studio thumbnail my-video        # out/my-video-thumbnail.jpg
```

`render` runs `sync` first, so the narration and timings are always current.

## How it works

1. Each scene renders on its own.
2. The scene clips are concatenated losslessly.
3. The voice track is built from `audio/vo/`, and the music bed is ducked under it (sidechain).
4. Audio is mastered to **−14 LUFS / −1.5 dBTP** with a two-pass loudnorm, AAC at 48 kHz.

## Caching

Each scene render is keyed on its HTML, assets, duration and quality, so only changed scenes are
re-rendered. A single-scene change takes seconds; a full render runs at about real time on the
reference machine (RX 580, GPU capture).

```bash
uv run studio render my-video --force            # re-render every scene
uv run studio render my-video --force hook outro # re-render only these scenes
```

The cache lives in `episodes/<slug>/build/` and is safe to delete.

## Before you render

- `uv run studio check <slug>` passes with 0 errors.
- You have looked at frames from `npx hyperframes snapshot`.
- `studio render` warns if the chapters don't meet YouTube's rules: at least 3 chapters, each at
  least 10 seconds.

## Outputs

| File | Use |
| --- | --- |
| `out/<slug>.mp4` | The video: 1920×1080, 30 fps |
| `out/<slug>.srt` | Upload as YouTube subtitles. Captions are not burned in for landscape videos |
| `out/<slug>.chapters.txt` | Paste into the video description |
| `out/<slug>-thumbnail.jpg` | The thumbnail |
| `out/<slug>-draft.mp4` | Draft-quality review copy |

## Thumbnail

`studio thumbnail` renders `episodes/<slug>/thumbnail/thumbnail.html` with headless Chromium. The
first run creates that file from `templates/thumbnail.html`, using the episode title; edit it, then
run the command again.

## Publishing to YouTube

1. Upload `out/<slug>.mp4` and the thumbnail.
2. Paste `out/<slug>.chapters.txt` into the description.
3. Upload `out/<slug>.srt` under Subtitles.
4. If you used a music bed, add its credit to the description.

The last 5–20 seconds keep the right ~45% of the frame clear for YouTube end-screen elements (the
`outro` template does this).
