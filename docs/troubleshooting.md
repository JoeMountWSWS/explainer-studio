# Troubleshooting

## Package or model downloads fail with DNS errors

With NordVPN and DNSSEC you may see "signature-expired". Flush the resolver cache and retry:

```bash
resolvectl flush-caches
```

## A render hangs or reports empty frames

The render uses Chromium's GPU capture. If it hangs, add `--no-browser-gpu` in `render_scenes()` in
`tools/studio/render.py`.

## "Only one root-level HTML file may carry `data-composition-id`"

`render` creates temporary `_render_<id>.html` shells and deletes them. If a crash leaves one behind,
delete it from the episode folder.

## The voice mispronounces a word

Add a respelling to `pronounce:` in the script (this episode) or `brand/pronunciations.yaml` (every
episode), then try it with `uv run studio voices <slug> --scene <id>`. Captions keep the original
spelling. See [Writing a script](script.md#numbers-abbreviations-and-names).

## Narration sounds flat or rushed

Kokoro ignores SSML and emotion tags. Use punctuation: commas for breaths, full stops for resets, `?`
for questions and `{pause n}` for a beat. Try a different blend with `studio voices`, or lower `speed`.

## My animation didn't move when I changed the narration

Animations must use `cue("name", fallback)` and `T.*` rather than fixed seconds. Also check that you
haven't edited between the `<studio:timing>` markers, which `sync` rewrites.

## I changed `> template:` and nothing happened

The template only applies when the scene file is created. Delete `scenes/<id>.html` and run `sync`.

## Why did `sync` re-narrate everything?

Changing any voice setting (`voice`, `speed`, `g2p`, pauses, `voice_fx`, the TTS engine) invalidates
the cache. Changing one paragraph re-synthesises only that paragraph.

## Chatterbox fails to start

Delete `~/.cache/hyperframes/chatterbox/<version>` to rebuild its environment. There is no GPU
support on the reference machine (no CUDA on the RX 580, and ROCm doesn't support it), so it runs
on the CPU.

## Windows or macOS

Not supported. The studio is developed and tested on Linux.
