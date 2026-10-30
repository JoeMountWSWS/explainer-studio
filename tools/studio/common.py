"""Paths, settings and small helpers shared by the studio commands."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _workspace() -> Path:
    """$STUDIO_ROOT, else the nearest directory at or above the cwd holding episodes/, else the cwd."""
    if env := os.environ.get("STUDIO_ROOT"):
        return Path(env).expanduser().resolve()
    cwd = Path.cwd().resolve()
    return next((d for d in (cwd, *cwd.parents) if (d / "episodes").is_dir()), cwd)


# House style bundled with the package: studio/data/ in a wheel, the source tree in a checkout.
_HERE = Path(__file__).resolve().parent
PKG_DATA = _HERE / "data" if (_HERE / "data").is_dir() else _HERE.parents[1]

# The workspace holds episodes/, out/, .env and any brand/music or brand/voices. A workspace brand/
# or templates/ (as in a repo checkout) overrides the bundled copy.
ROOT = _workspace()
BRAND = ROOT / "brand" if (ROOT / "brand" / "brand.css").exists() else PKG_DATA / "brand"
TEMPLATES = ROOT / "templates" if (ROOT / "templates" / "script.md").exists() else PKG_DATA / "templates"
# Commercial fonts (e.g. DINPro) the user holds a licence for: gitignored, never shipped in the wheel.
LICENSED_FONTS = ROOT / "brand" / "fonts-licensed"
EPISODES = ROOT / "episodes"
OUT = ROOT / "out"

# Pin the HyperFrames CLI so renders are reproducible. Bump deliberately, then run `studio check`.
HF_VERSION = os.environ.get("STUDIO_HF_VERSION", "0.8.153")
# Chatterbox TTS runs in its own uv environment (it pins torch and numpy<2); pinned for the same reason.
CHATTERBOX_VERSION = os.environ.get("STUDIO_CHATTERBOX_VERSION", "0.1.7")

# Episode defaults; any of these can be overridden in a script's front matter.
DEFAULTS = {
    "tts": "kokoro",           # TTS engine: kokoro (local), chatterbox (local, cloned) or elevenlabs (cloud; key in .env)
    # Kokoro voice or weighted blend, an ElevenLabs voice ID, or a Chatterbox reference clip (or "default")
    "voice": "bf_emma*0.6 + bf_isabella*0.4",
    "speed": 0.85,             # Kokoro voices differ: the default blend is ~165 wpm at 0.85, bm_george ~155 at 1.0
    "g2p": "misaki",           # Kokoro phonemizer: misaki (what Kokoro was trained on) or espeak
    "sentence_pause": 0.38,    # Kokoro: silence between sentences, seconds
    "clause_pause": 0.12,      # Kokoro: silence where an over-long sentence is split at a comma
    "voice_fx": True,          # Kokoro: gentle EQ/compression/room on the dry voice (voice.VOICE_FX)
    "tts_model": "eleven_multilingual_v2",  # ElevenLabs model
    "voice_settings": None,    # ElevenLabs: {stability, similarity_boost, style, use_speaker_boost}
    "chatterbox_model": "turbo",  # Chatterbox: turbo (350M, faster) or standard (500M, honours the next two)
    "exaggeration": 0.5,       # Chatterbox standard: emotional intensity (0.25-2)
    "cfg_weight": 0.5,         # Chatterbox standard: lower is slower and more deliberate
    "temperature": 0.8,        # Chatterbox: sampling temperature
    "seed": 0,                 # Chatterbox: random seed, so a re-synthesis is repeatable
    "format": "landscape",     # landscape (1920x1080, YouTube) or reel (1080x1920: Reels, TikTok, Shorts)
    "burn_captions": False,    # burn word-highlighted captions into the video (on for reels; most autoplay muted)
    "fps": 30,
    "pad_in": 0.6,             # silence before a scene's narration starts
    "pad_out": 0.9,            # silence after it ends (the exit fade lives here)
    "paragraph_gap": 0.45,     # pause between paragraphs inside a scene
    "music": None,             # path to a music bed, relative to the studio root
    "music_prompt": None,      # default prompt for `studio music` (ElevenLabs Music)
    "music_db": -24,          # music level under narration, before ducking
    "music_fade_in": 2,        # seconds; 0 keeps a hit on the bed's first beat
    "loudness": -14,           # integrated LUFS target (YouTube normalises to -14)
    "true_peak": -1.5,
}

SAMPLE_RATE = 48000
FORMATS = {"landscape": (1920, 1080), "reel": (1080, 1920)}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(msg, flush=True)


def sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, Path):
            h.update(p.read_bytes())
        elif isinstance(p, bytes):
            h.update(p)
        else:
            h.update(json.dumps(p, sort_keys=True, default=str).encode())
        h.update(b"\0")
    return h.hexdigest()


def tree_hash(folder: Path) -> str:
    """Hash every file under folder by path, size and mtime (cheap; good enough for cache keys)."""
    if not folder.exists():
        return ""
    entries = sorted(
        (str(p.relative_to(folder)), p.stat().st_size, int(p.stat().st_mtime))
        for p in folder.rglob("*")
        if p.is_file()
    )
    return sha(entries)


def run(cmd: list[str], cwd: Path | None = None, quiet: bool = False, env: dict | None = None) -> str:
    full_env = {**os.environ, **(env or {})}
    proc = subprocess.run(cmd, cwd=cwd, env=full_env, text=True, encoding="utf-8", errors="replace",
                          capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-25:]
        die(f"command failed ({proc.returncode}): {' '.join(cmd[:6])} ...\n" + "\n".join(tail))
    if not quiet and proc.stderr.strip():
        pass
    return proc.stdout


def hf(*args: str) -> list[str]:
    """argv for the pinned HyperFrames CLI. On Windows npx is npx.cmd, which subprocess only finds by full path."""
    return [shutil.which("npx") or "npx", "--yes", f"hyperframes@{HF_VERSION}", *args]


def hf_env() -> dict:
    # Let the CLI's own tts/transcribe find kokoro-onnx in this studio's venv.
    return {"HYPERFRAMES_PYTHON": sys.executable}


def load_env() -> None:
    """Read ROOT/.env (KEY=value, optional `export`, quotes, # comments) without overriding the environment."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def write_env(updates: dict[str, str]) -> Path:
    """Set KEY=value lines in ROOT/.env, keeping comments and other keys; created owner-only (0600)."""
    path = ROOT / ".env"
    lines = path.read_text().splitlines() if path.exists() else []
    pending = dict(updates)
    for i, line in enumerate(lines):
        key = line.strip().removeprefix("export ").partition("=")[0].strip()
        if "=" in line and not line.lstrip().startswith("#") and key in pending:
            lines[i] = f"{key}={pending.pop(key)}"
    lines += [f"{k}={v}" for k, v in pending.items()]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    path.chmod(0o600)
    return path


def ffprobe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


def episode_dir(slug: str) -> Path:
    d = EPISODES / slug
    if not (d / "script.md").exists():
        die(f"no episode '{slug}' (expected {d / 'script.md'})")
    return d


LFS_POINTER = b"version https://git-lfs.github.com/spec/"


def require_media(ep: Path, extra: list[Path] = ()) -> None:
    """Stop with a fix if episode media are Git LFS pointers (cloned without LFS, or not pulled yet)."""
    files = [p for d in ("audio/vo", "audio/recorded", "assets/media") for p in (ep / d).rglob("*")]
    pointers = []
    for p in [*files, *extra]:
        if p.is_file() and p.stat().st_size < 1024:
            with p.open("rb") as f:
                if f.read(len(LFS_POINTER)) == LFS_POINTER:
                    pointers.append(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)
    if pointers:
        listed = "\n  ".join(map(str, pointers[:5])) + (f"\n  … and {len(pointers) - 5} more" if len(pointers) > 5 else "")
        die(f"{len(pointers)} media file(s) are Git LFS pointers, not the real files:\n  {listed}\n"
            f"fetch them with: git lfs install && git lfs pull --include \"episodes/{ep.name}/**,brand/music/**\"")


REQUIRED_TOOLS = ("ffmpeg", "ffprobe", "npx")


def missing_tools() -> list[str]:
    return [t for t in REQUIRED_TOOLS if not shutil.which(t)]


def require_tools() -> None:
    for tool in missing_tools():
        die(f"'{tool}' not found on PATH (run `studio setup` to check your install)")
