# Commands

Every command is `uv run studio <command> <slug>`, run from the repository root. `<slug>` is the
folder name under `episodes/`. `uv run studio --help` lists them all.

## `new`

```bash
uv run studio new <slug> ["Title"]
```

Scaffolds `episodes/<slug>/` from `templates/script.md`. The slug must be lowercase letters, digits
and hyphens. The title defaults to the slug, title-cased. Fails if the episode already exists.

## `status`

```bash
uv run studio status <slug>
```

Prints a table of scenes with template, word count, estimated and actual length, and cues, then a
total. The estimate assumes 2.5 words a second plus 1.5s per scene; actual lengths appear after a
`sync`. Scenes without a file yet are flagged.

## `sync`

```bash
uv run studio sync <slug> [--scene ID ...]
```

Narrates (using the cache), aligns words to audio, creates any missing scene files from their
templates, rewrites each scene's timing block, copies `brand/` into the episode, and writes
`index.html` and `timing.json`.

`--scene` re-narrates only the named scenes and reuses cached timings for the rest.

## `preview`

```bash
uv run studio preview <slug> [-- extra hyperframes args]
```

Runs `sync`, then opens HyperFrames Studio in the browser with the narration. Anything after the slug
is passed to `hyperframes preview`.

## `check`

```bash
uv run studio check <slug>
```

Runs `sync`, then `hyperframes check`: lint, layout and contrast audits. Exits non-zero on errors.

## `render`

```bash
uv run studio render <slug> [--draft] [--force [ID ...]]
```

Runs `sync`, renders changed scenes, assembles and masters the episode into `out/`.

| Flag | Meaning |
| --- | --- |
| `--draft` | Fast, lower-quality render to `out/<slug>-draft.mp4` |
| `--force` | Re-render every scene |
| `--force ID …` | Re-render only the named scenes |

Requires ffmpeg. See [Rendering and publishing](rendering.md).

## `thumbnail`

```bash
uv run studio thumbnail <slug>
```

Screenshots `episodes/<slug>/thumbnail/thumbnail.html` with headless Chromium to
`out/<slug>-thumbnail.jpg` (1280×720). Creates the HTML from the template on first use.

## `voices`

```bash
uv run studio voices <slug> [--scene ID] [--voices SPEC ...] [--speed N]
```

Synthesises one scene with each candidate voice, using the episode's other settings, and writes
loudness-matched samples to `out/voice-samples/`.

| Flag | Meaning |
| --- | --- |
| `--scene` | Scene to use. Defaults to the first narrated scene |
| `--voices` | Kokoro voices or blends, such as `"bf_emma*0.6 + bf_lily*0.4"`. With `tts: chatterbox`, clip paths or `default` |
| `--speed` | Override the script's speed (ignored by Chatterbox) |

With no `--voices`, Kokoro auditions six built-in blends, and Chatterbox auditions every
`brand/voices/*.wav` plus `default`.

## HyperFrames directly

The studio drives the [HyperFrames](https://www.npmjs.com/package/hyperframes) CLI at a pinned version
(`HF_VERSION` in `tools/studio/common.py`; override with `STUDIO_HF_VERSION`). You can call it yourself,
for example to take snapshots:

```bash
npx hyperframes snapshot episodes/<slug> --at 12.5,40
```
