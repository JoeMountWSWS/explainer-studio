"""`studio setup`: check the install, ask a few questions, and write .env."""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import NamedTuple

from . import common, voice
from .common import LICENSED_FONTS, ROOT, die, hf, hf_env, info, load_env, missing_tools, run

ELEVENLABS_USER_URL = "https://api.elevenlabs.io/v1/user"
CHROMIUMS = ("chromium", "google-chrome", "chrome")

HINTS = {
    "ffmpeg": "install ffmpeg (e.g. `sudo pacman -S ffmpeg`, `sudo apt install ffmpeg`, `brew install ffmpeg`)",
    "ffprobe": "ships with ffmpeg",
    "npx": "install Node.js, which includes npx (https://nodejs.org)",
    "uv": "install uv (https://docs.astral.sh/uv/)",
    "chromium": "needed for `studio thumbnail`; install Chromium or Chrome",
    "rclone": "needed for `studio archive`; install rclone, then run `rclone config`",
    "git-lfs": "needed to fetch a media workspace; install git-lfs, then `git lfs install`",
    "dinpro-fonts": "licensed sans font, optional; without it Source Sans 3 is used (see brand/fonts-licensed/README.md)",
    "workspace": "optional; a private content workspace for real episodes (see docs/getting-started.md)",
}


class Item(NamedTuple):
    status: str  # ok | missing | optional
    name: str
    detail: str


def mask(key: str) -> str:
    return f"{key[:3]}…{key[-4:]}" if len(key) > 10 else "…"


def has_chromium() -> bool:
    return any(shutil.which(c) for c in CHROMIUMS)


def check_items() -> list[Item]:
    """One line per prerequisite. Only ffmpeg, ffprobe and npx are required."""
    missing = set(missing_tools())
    items = [Item("missing" if t in missing else "ok", t, HINTS[t] if t in missing else "found")
             for t in common.REQUIRED_TOOLS]
    optional = {
        "uv": bool(shutil.which("uv")),
        "chromium": has_chromium(),
        "rclone": bool(shutil.which("rclone")),
        "git-lfs": bool(shutil.which("git-lfs")),
        "dinpro-fonts": any(LICENSED_FONTS.glob("DINPro-*.ttf")),
        "workspace": (ROOT / "episodes").is_dir(),
    }
    items += [Item("ok" if found else "optional", name, "found" if found else HINTS[name])
              for name, found in optional.items()]
    return items


def print_report(items: list[Item]) -> int:
    for it in items:
        info(f"{it.status:<8} {it.name:<13} {it.detail}")
    bad = [it.name for it in items if it.status == "missing"]
    info(f"summary: {'missing required: ' + ', '.join(bad) if bad else 'all required tools found'}"
         f"; .env {'present' if (ROOT / '.env').exists() else 'not created'}")
    return len(bad)


def verify_elevenlabs(key: str) -> tuple[bool | None, str]:
    """(True, ok) accepted, (False, why) rejected, (None, why) couldn't tell. Spends no credits."""
    req = urllib.request.Request(ELEVENLABS_USER_URL, headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=15):
            return True, "accepted"
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if e.code == 401 and "missing_permissions" in body:
            return True, "accepted, but it is a restricted key (fine, as long as it can do text-to-speech/music)"
        if e.code == 401:
            return False, "rejected (401): check the key"
        return None, f"could not verify (HTTP {e.code})"
    except (urllib.error.URLError, OSError) as e:
        return None, f"could not verify (offline? {e})"


def confirm(question: str, default: bool = False) -> bool:
    ans = input(f"{question} [{'Y/n' if default else 'y/N'}] ").strip().lower()
    return default if not ans else ans.startswith("y")


def ask(question: str, current: str = "") -> str:
    shown = f" [{current}]" if current else ""
    return input(f"{question}{shown}: ").strip() or current


def ask_key(current: str) -> str:
    shown = f" (Enter keeps {mask(current)})" if current else " (Enter to skip)"
    return getpass.getpass(f"ElevenLabs API key{shown}: ").strip() or current


def check_remote(remote: str) -> str | None:
    """None if rclone knows the remote (or can't be asked), else a message."""
    if not shutil.which("rclone"):
        return None
    out = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True).stdout.split()
    name = remote.split(":", 1)[0] + ":"
    return None if name in out else f"rclone has no remote called '{name}': run `rclone config` to add it"


def download_models() -> None:
    kokoro = voice.KOKORO_DIR / "models" / "kokoro-v1.0.onnx"
    if kokoro.exists():
        info("  Kokoro model already downloaded")
    else:
        info("  downloading the Kokoro model (~300 MB)…")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            run(hf("tts", "warm up", "-o", f"{tmp}/x.wav"), env=hf_env())
    voice.ensure_spacy_model()
    info("  spaCy model ready")


def cmd_setup(a):
    load_env()
    interactive = sys.stdin.isatty() and not a.check
    info(f"studio setup ({ROOT})\n")
    bad = print_report(check_items())
    if not interactive:
        sys.exit(1 if bad else 0)
    if bad:
        info("\nInstall the missing required tools above, then run `studio setup` again.")
        sys.exit(1)

    info("\nNarration: Kokoro is local and free (default). ElevenLabs is optional, cloud-based and billed per character.")
    updates: dict[str, str] = {}
    current = os.environ.get("ELEVENLABS_API_KEY", "")
    if current or confirm("Set up an ElevenLabs key (narration and music beds)?"):
        key = ask_key(current)
        if key and key != current and not a.no_verify:
            ok, why = verify_elevenlabs(key)
            info(f"  {why}")
            if ok is False and not confirm("  Save it anyway?"):
                key = current
        if key:
            updates["ELEVENLABS_API_KEY"] = key

    archive = os.environ.get("STUDIO_ARCHIVE", "")
    if archive or confirm("Archive finished videos to cloud storage with rclone?"):
        remote = ask("rclone path, e.g. gdrive:explainer-masters", archive).rstrip("/")
        if remote:
            warn = check_remote(remote)
            if warn:
                info(f"  {warn}")
            updates["STUDIO_ARCHIVE"] = remote

    if updates:
        gi = ROOT / ".gitignore"
        if (ROOT / ".git").exists() and (not gi.exists() or ".env" not in gi.read_text().split()):
            die(".env is not in .gitignore: add it first so your keys can't be committed")
        path = common.write_env(updates)
        info(f"\nSaved {', '.join(updates)} to {path} (owner-only). Keys are never printed back.")
    else:
        info("\nNothing to save.")

    if not a.no_download and confirm("Download the narration models now (~300 MB, saves waiting on the first `sync`)?"):
        download_models()

    info("\nAll set. Next:\n  studio new my-video \"My Video\"   then edit episodes/my-video/script.md\n"
         "  studio sync my-video             narrate and time the scenes\n"
         "A finished example to study: episodes/demo-paris-commune/")
