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

## `music`

```bash
uv run studio music <slug> --prompt "sombre cello and piano, slow, no percussion" [--variants N] [--out PATH]
```

Generates an instrumental music bed with [ElevenLabs Music](https://elevenlabs.io/music-api) and
prints the `music:` line to put in `script.md`. Run `sync` first: the bed is sized to the episode's
`timing.json` (length + 2 s). It uses the same `ELEVENLABS_API_KEY` as narration, but the key needs
the `music_generation` permission, and a paid plan for commercial use (film and TV excluded).
Cost is roughly $0.0083 a second, so a five-minute bed is about $2.50. Results are cached by prompt,
length and model, so a re-run is free.

| Flag | Meaning |
| --- | --- |
| `--prompt` | Genre, mood, tempo, instruments. Defaults to `music_prompt:` in the front matter. Don't name artists or songs |
| `--name` | File name in `episodes/<slug>/audio/music/` (default `bed`) |
| `--length` | Seconds (3–600). Defaults to the episode length + 2 s; a shorter bed loops |
| `--model` | `music_v1`, `music_v2` (default) or `music_v2_5` |
| `--variants` | Make 1–4 different takes, suffixed `-a`, `-b`…, to audition |
| `--out` | Write here instead, such as `brand/music/my-bed.mp3` to share across episodes |

Log the track in `brand/music/CREDITS.md` (source, prompt, date). Check
[ElevenLabs' music rights](https://elevenlabs.io/music-rights) for your plan and use before publishing.

## HyperFrames directly

The studio drives the [HyperFrames](https://www.npmjs.com/package/hyperframes) CLI at a pinned version
(`HF_VERSION` in `tools/studio/common.py`; override with `STUDIO_HF_VERSION`). You can call it yourself,
for example to take snapshots:

```bash
npx hyperframes snapshot episodes/<slug> --at 12.5,40
```
