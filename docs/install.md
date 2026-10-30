# Install

The studio runs on **Windows**, **Linux** and **macOS**. Windows and Linux are tested in CI (Windows
narrates and renders a reel end to end). macOS isn't tested yet, but nothing in the studio is
Linux-specific, so it should work. If it doesn't, please
[open an issue](https://github.com/JoeMountWSWS/explainer-studio/issues).

Pick your system in any tab below. Your choice is remembered on every page of these docs.

## What you need

| Tool | Why |
| --- | --- |
| [uv](https://docs.astral.sh/uv/) | Runs the studio. It fetches Python 3.12 or 3.13 for you (`kokoro-onnx` doesn't support 3.14 yet) |
| Node.js (with `npx`) | Runs the HyperFrames CLI, which is fetched on demand at the version pinned in `tools/studio/common.py` |
| ffmpeg (with `ffprobe`) | Mixes and masters the audio and joins the scenes |
| Chrome, Chromium or Edge | Needed for `studio thumbnail`. HyperFrames manages the browser it renders with |
| git | Only to install from a clone, or to keep episodes in a repository |
| An ElevenLabs API key | Optional, for cloud narration (see [Narration](narration.md#elevenlabs-cloud)) |

## 1. Install the tools

=== "Windows"

    Open **PowerShell** and run:

    ```powershell
    winget install --id Git.Git -e
    winget install --id astral-sh.uv -e
    winget install --id OpenJS.NodeJS.LTS -e
    winget install --id Gyan.FFmpeg -e
    ```

    Then **close and reopen PowerShell** so the new programs are on your PATH. Edge is already
    installed with Windows, so thumbnails work without anything extra. If `winget` isn't available,
    install the same four tools from their websites, or with
    [Chocolatey](https://chocolatey.org/): `choco install git uv nodejs-lts ffmpeg -y`.

=== "Linux"

    === "Arch"

        ```bash
        sudo pacman -S git nodejs npm ffmpeg chromium uv
        ```

    === "Debian / Ubuntu"

        ```bash
        sudo apt install git nodejs npm ffmpeg chromium
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    === "Fedora"

        ```bash
        sudo dnf install git nodejs ffmpeg chromium
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    On Fedora, ffmpeg comes from [RPM Fusion](https://rpmfusion.org/). Reopen the terminal after
    installing uv.

=== "macOS (untested)"

    With [Homebrew](https://brew.sh/):

    ```bash
    brew install git uv node ffmpeg
    brew install --cask chromium   # optional, for thumbnails; Chrome works too
    ```

    macOS isn't covered by our CI yet. If something here doesn't work, tell us.

Check what you have:

```bash
uv --version
node --version
ffmpeg -version
```

## 2. Get the studio

There are two ways in. Most people want the first.

**From PyPI** (a workspace of your own):

=== "Windows"

    ```powershell
    uv tool install explainer-studio
    mkdir my-videos
    cd my-videos
    ```

=== "Linux"

    ```bash
    uv tool install explainer-studio
    mkdir my-videos && cd my-videos
    ```

=== "macOS (untested)"

    ```bash
    uv tool install explainer-studio
    mkdir my-videos && cd my-videos
    ```

Then type `studio …` wherever the docs say `uv run studio …`.

**From a clone** (to work on the studio itself, or to use the bundled demo episode):

```bash
git clone https://github.com/JoeMountWSWS/explainer-studio.git
cd explainer-studio
uv sync
```

Every command then runs as `uv run studio …` from the repository root, or any folder below it.

## 3. Check and configure

```bash
uv run studio setup --check
```

This prints one line per tool: `ok`, `missing` or `optional`. It only fails if ffmpeg, ffprobe or `npx`
is missing, and each missing line says how to install it. Then run the wizard:

```bash
uv run studio setup
```

It tests an ElevenLabs key (without spending credits), writes `.env`, and offers to download the
narration models. You can skip the key: the default Kokoro narration is local and free.

### Setting an environment variable by hand

You rarely need to, because `studio setup` writes `.env`. If you do, for example `STUDIO_ROOT` or
`ELEVENLABS_API_KEY` for one session:

=== "Windows"

    ```powershell
    $env:ELEVENLABS_API_KEY = "your-key"
    ```

=== "Linux"

    ```bash
    export ELEVENLABS_API_KEY="your-key"
    ```

=== "macOS (untested)"

    ```bash
    export ELEVENLABS_API_KEY="your-key"
    ```

Never commit `.env`.

## Where things go on each system

| What | Where |
| --- | --- |
| Kokoro model | `~/.cache/hyperframes/tts` |
| spaCy model | `~/.cache/hyperframes/spacy` |
| Chatterbox environment | `~/.cache/hyperframes/chatterbox/<version>` |
| Claude Code skill (`install-skill --user`) | `~/.claude/skills/` |

`~` is your home folder: `C:\Users\<you>` on Windows, `/home/<you>` on Linux, `/Users/<you>` on macOS.

## What differs between systems

- **Render speed.** On Linux, HyperFrames captures frames from Chromium's GPU buffer, and a full render
  runs at about real time. On Windows and macOS it captures by screenshot, which is slower. Use
  `--draft` while you work.
- **Opening a file.** The docs say "edit `script.md`". Use any editor: `notepad`, `code`, or double-click
  it in the file explorer on Windows; `$EDITOR`, `code` or `xdg-open` on Linux; `open -e` on macOS.
- **Paths.** Use forward slashes in scripts and scene files (`assets/media/x.jpg`) on every system.

Next: [make your first video](getting-started.md).
