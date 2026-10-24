"""Build this reel's music bed: the Suno track with one percussion hit on each of the three title phrases.

    uv run python episodes/iysse-trotskyism-reel/audio/make_bed.py <suno-track> [hit] [--offset s] [--scenes a,b] [--hit-db 6]

The hits land on the first frame of the given scenes (default `trotskyism`, `socialism` and
`century`), read from timing.json, so re-run this after any `studio sync` that changes the
narration. `--offset` skips the start of the track, e.g. to put its own opening impact on frame 0
(then leave `trotskyism` out of `--scenes`). Writes brand/music/iysse-trotskyism-bed.wav, which
script.md's `music:` points at.
"""
import argparse
import json
import subprocess
from pathlib import Path

EP = Path(__file__).resolve().parents[1]
ROOT = EP.parents[1]
LEAD = 0.03  # the hit leads the cut very slightly, so the transient and the picture arrive together

ap = argparse.ArgumentParser()
ap.add_argument("track", type=Path)
ap.add_argument("hit", type=Path, nargs="?", default=EP / "audio/sfx/hit.wav")
ap.add_argument("--offset", type=float, default=0.0, help="seconds to skip at the start of the track")
ap.add_argument("--scenes", default="trotskyism,socialism,century", help="scenes whose first frame gets a hit")
ap.add_argument("--hit-db", type=float, default=6.0, help="hit level relative to the track")
args = ap.parse_args()
hit_scenes = [s for s in args.scenes.split(",") if s]

timing = json.loads((EP / "timing.json").read_text())
starts, t = {}, 0.0
for s in timing["scenes"]:
    starts[s["id"]] = t
    t += s["duration"]
total = timing["duration"] + 0.5

inputs = ["-i", str(args.track)] + ["-i", str(args.hit)] * len(hit_scenes)
chains = [f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,"
          f"atrim={args.offset:.3f}:{args.offset + total:.3f},asetpts=PTS-STARTPTS[bed]"]
for i, sid in enumerate(hit_scenes, 1):
    ms = round(max(starts[sid] - LEAD, 0) * 1000)
    chains.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={args.hit_db}dB,adelay={ms}|{ms}[h{i}]")
hits = "".join(f"[h{i}]" for i in range(1, len(hit_scenes) + 1))
chains.append(f"[bed]{hits}amix=inputs={len(hit_scenes) + 1}:duration=first:normalize=0,alimiter=limit=0.89[out]")

dst = ROOT / "brand/music/iysse-trotskyism-bed.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "[out]",
                "-c:a", "pcm_s24le", str(dst)], check=True)
print(f"wrote {dst.relative_to(ROOT)} ({total:.1f}s); hits at " + ", ".join(f"{starts[s]:.2f}s" for s in hit_scenes))
