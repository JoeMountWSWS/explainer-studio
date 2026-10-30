# Troubleshooting

Start with `uv run studio setup --check`, which reports missing tools and says how to install them.
Problems that only happen on one system are at the [end of the page](#problems-on-one-system).

## pip can't find explainer-studio

`pip install explainer-studio` fails with "No matching distribution found" and an "Ignored the following
versions that require a different python version" line when your Python is 3.14 or newer. The studio
supports Python 3.12 and 3.13 only (`kokoro-onnx` needs them). Use `uv tool install explainer-studio`, which
downloads a suitable Python for you, or run pip from a 3.12 or 3.13 environment.

## `check` says to bump the HyperFrames pin

`studio check` ends with "This project pins hyperframes@… (latest …). Bump it". That line comes from
HyperFrames itself. The pin (`HF_VERSION` in `tools/studio/common.py`) is deliberate: it is only raised after
a draft render has been compared, so ignore the hint.

## A render prints "chapter … is under 10s"

These notes are YouTube's chapter rules (at least 3 chapters, each 10s or longer). They only matter when you
upload, and the short starter script always trips them. The render itself succeeded.

## A render hangs or reports empty frames

The render uses Chromium's GPU capture on Linux. If it hangs, add `--no-browser-gpu` in
`render_scenes()` in `tools/studio/render.py`. On Windows and macOS frames are captured by screenshot
instead, so a render is slower but doesn't hit this.

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

Delete `~/.cache/hyperframes/chatterbox/<version>` to rebuild its environment (`C:\Users\<you>\.cache\...`
on Windows). It runs on the CPU, which is slow: about 4–5× slower than real time on the reference
machine, which has no CUDA GPU.

## Problems on one system

=== "Windows"

    **`'studio' is not recognized`, or `winget`-installed tools are not found.** Close and reopen
    PowerShell so the new PATH applies. With `uv tool install`, run `uv tool update-shell` once.

    **`running scripts is disabled on this system`.** PowerShell is blocking a script. Allow your own
    scripts with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

    **`npx` fails to start.** On Windows it is `npx.cmd`. The studio handles this itself, so the cause
    is usually Node.js missing from PATH. Check `node --version`.

    **ffmpeg errors that mention a drive letter or `C:`.** The studio keeps absolute paths out of ffmpeg
    filter arguments because the colon splits options. If you add your own filter, use relative paths.

    **Garbled characters in a script or scene file.** Save files as UTF-8. Windows Notepad does by
    default today; older editors may use cp1252.

    **Renders are slow.** Windows captures frames by screenshot. Use `render --draft` while you work.

    **A path is too long.** Keep the studio close to the drive root, or enable long paths in Windows.

    **Thumbnail can't find a browser.** The studio looks for Chrome, Chromium or Edge on PATH. Install
    one, or add its folder to PATH.

=== "Linux"

    **Package or model downloads fail with DNS errors.** With NordVPN and DNSSEC you may see
    "signature-expired". Flush the resolver cache and retry:

    ```bash
    resolvectl flush-caches
    ```

    **`studio thumbnail` finds no browser.** Install `chromium` or `google-chrome` so it is on PATH.

=== "macOS (untested)"

    **`brew`-installed tools are not found.** Add Homebrew to your shell's PATH (`brew shellenv`
    prints the line to use) and reopen the terminal.

    **macOS blocks a downloaded program.** Open System Settings → Privacy & Security and allow it.

    These are generic fixes. We haven't run the studio on macOS, so please
    [report](https://github.com/JoeMountWSWS/explainer-studio/issues) anything else you hit.
