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
    proc = subprocess.run(cmd, cwd=cwd, env=full_env, text=True, capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-25:]
        die(f"command failed ({proc.returncode}): {' '.join(cmd[:6])} ...\n" + "\n".join(tail))
    if not quiet and proc.stderr.strip():
        pass
    return proc.stdout


def hf(*args: str) -> list[str]:
    """argv for the pinned HyperFrames CLI."""
    return ["npx", "--yes", f"hyperframes@{HF_VERSION}", *args]


def hf_env() -> dict:
    # Let the CLI's own tts/transcribe find kokoro-onnx in this studio's venv.
    return {"HYPERFRAMES_PYTHON": sys.executable}


def load_env() -> None:
    """Read ROOT/.env (KEY=value, optional `export`, quotes, # comments) without overriding the environment."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def ffprobe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


def episode_dir(slug: str) -> Path:
    d = EPISODES / slug
    if not (d / "script.md").exists():
        die(f"no episode '{slug}' (expected {d / 'script.md'})")
    return d


def require_tools() -> None:
    for tool in ("ffmpeg", "ffprobe", "npx"):
        if not shutil.which(tool):
            die(f"'{tool}' not found on PATH")
