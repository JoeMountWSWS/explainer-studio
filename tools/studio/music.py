"""Music beds: an instrumental track from the ElevenLabs Music API, sized to an episode.

    audio/music/<hash>.mp3     cached API result (48 kHz stereo); the same prompt, length and model is never re-billed
    audio/music/<name>.mp3     the bed itself (or --out), ready for `music:` in script.md

The render loops a bed shorter than the episode and trims a longer one, so the length only has to
be about right. Uses the same ELEVENLABS_API_KEY as narration.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from .common import ROOT, die, ffprobe_duration, info, run, sha
from .voice import elevenlabs_key, elevenlabs_post

URL = "https://api.elevenlabs.io/v1/music?output_format=mp3_48000_192"
MODEL = "music_v2"
MIN_S, MAX_S = 3, 600  # API limits on music_length_ms
USD_PER_SECOND = 0.0083  # third-party figure; check elevenlabs.io/pricing/api
TAIL_S = 2  # beds run slightly past the narration so the final fade has music under it


def episode_length(ep: Path) -> float:
    path = ep / "timing.json"
    if not path.exists():
        die(f"{path.relative_to(ROOT)} not found - run: uv run studio sync {ep.name}")
    return float(json.loads(path.read_text())["duration"])


def generate(ep: Path, prompt: str, length_s: int, model: str, variant: int = 0) -> Path:
    """Return the cached bed for these inputs, calling the API only on a miss. `variant` forces a fresh take."""
    length_s = min(max(length_s, MIN_S), MAX_S)
    cache = ep / "audio" / "music" / f"{sha(prompt, length_s, model, variant)[:20]}.mp3"
    if cache.exists():
        info(f"  cached: {cache.relative_to(ROOT)}")
        return cache
    info(f"  composing {length_s}s with {model} (about ${length_s * USD_PER_SECOND:.2f})")
    body = {"prompt": prompt, "music_length_ms": length_s * 1000, "model_id": model, "force_instrumental": True}
    audio = elevenlabs_post(URL, elevenlabs_key(), body, timeout=600)
    cache.parent.mkdir(parents=True, exist_ok=True)
    raw = cache.with_name(f".{cache.stem}.raw.mp3")
    raw.write_bytes(audio)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "48000", "-ac", "2", "-c:a", "libmp3lame",
         "-b:a", "192k", str(cache)])
    raw.unlink()
    return cache


def make_beds(ep: Path, prompt: str, name: str, length_s: int | None, model: str, variants: int,
              out: Path | None) -> list[Path]:
    length = length_s or math.ceil(episode_length(ep)) + TAIL_S
    dst_dir = out.parent if out else ep / "audio" / "music"
    dst_dir.mkdir(parents=True, exist_ok=True)
    stem = out.stem if out else name
    paths = []
    for i in range(variants):
        suffix = f"-{chr(ord('a') + i)}" if variants > 1 else ""
        dst = dst_dir / f"{stem}{suffix}.mp3"
        shutil.copyfile(generate(ep, prompt, length, model, i), dst)
        paths.append(dst)
        info(f"  {dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst}  ({ffprobe_duration(dst):.0f}s)")
    return paths
