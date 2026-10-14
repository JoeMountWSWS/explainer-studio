"""studio: script -> narration -> HyperFrames scenes -> mastered MP4 + captions + chapters.

    uv run studio new <slug> "Title"      scaffold episodes/<slug>/ with a starter script
    uv run studio status <slug>           scenes, word counts, estimated vs actual length
    uv run studio sync <slug>             narrate (cached), align, stub scenes, write index.html
    uv run studio preview <slug>          open HyperFrames Studio on the episode
    uv run studio check <slug>            HyperFrames lint + layout/contrast audits
    uv run studio render <slug> [--draft] render changed scenes, assemble, master -> out/
    uv run studio thumbnail <slug>        screenshot thumbnail/thumbnail.html -> out/
    uv run studio voices <slug>           audition Kokoro blends or Chatterbox clips on one scene -> out/voice-samples/
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from . import build as builder
from . import render as renderer
from . import voice
from .common import BRAND, EPISODES, OUT, ROOT, TEMPLATES, die, episode_dir, hf, info, require_tools
from .script import Script, parse

AUDITION = [
    "bf_emma*0.6 + bf_isabella*0.4",
    "bf_emma*0.7 + bf_alice*0.3",
    "bf_emma*0.5 + bf_isabella*0.3 + bf_lily*0.2",
    "bf_isabella*0.6 + bf_emma*0.4",
    "bf_emma",
    "bm_george",
]


def cmd_new(a):
    slug = a.slug
    if not slug.replace("-", "").isalnum() or slug != slug.lower():
        die("slug must be lowercase letters, digits and hyphens, e.g. paris-commune")
    ep = EPISODES / slug
    if ep.exists():
        die(f"{ep} already exists")
    (ep / "scenes").mkdir(parents=True)
    (ep / "audio" / "recorded").mkdir(parents=True)
    (ep / "assets" / "media").mkdir(parents=True)
    title = a.title or slug.replace("-", " ").title()
    (ep / "script.md").write_text((TEMPLATES / "script.md").read_text().replace("__TITLE__", title))
    builder.ensure_project_files(ep)
    builder.sync_brand(ep)
    info(f"created episodes/{slug}/  - write the script in episodes/{slug}/script.md, then: uv run studio sync {slug}")


def cmd_status(a):
    ep = episode_dir(a.slug)
    script = parse(ep / "script.md")
    timing = json.loads((ep / "timing.json").read_text()) if (ep / "timing.json").exists() else None
    actual = {s["id"]: s for s in timing["scenes"]} if timing else {}
    total_words = 0
    info(f"{script.meta.get('title', a.slug)}   voice={script.setting('tts')}:{script.setting('voice')}\n")
    info(f"  {'scene':<18}{'template':<10}{'words':>6}{'est s':>8}{'actual s':>10}  cues")
    for sc in script.scenes:
        n = len(sc.words)
        total_words += n
        est = n / 2.5 + 1.5 if n else sc.min_duration
        act = actual.get(sc.id, {}).get("duration")
        file_flag = "" if (ep / "scenes" / f"{sc.id}.html").exists() else "  (no scene file yet)"
        info(f"  {sc.id:<18}{sc.template:<10}{n:>6}{est:>8.1f}{(f'{act:.1f}' if act else '-'):>10}  "
             f"{', '.join(sc.cues) or '-'}{file_flag}")
    est_total = total_words / 2.5 + 1.5 * len(script.scenes)
    info(f"\n  {total_words} words, estimated {est_total / 60:.1f} min"
         + (f", actual {timing['duration'] / 60:.1f} min ({timing['duration']:.1f}s)" if timing else ", not yet synced"))


def _sync(slug: str, only: set[str] | None = None):
    ep = episode_dir(slug)
    script = parse(ep / "script.md")
    info(f"narration ({script.setting('tts')}:{script.setting('voice')})")
    vo = voice.voice_all(ep, script, only)
    info("building project")
    timing = builder.build(ep, script, vo)
    info(f"  {len(timing['scenes'])} scenes, {timing['duration']:.1f}s ({timing['duration'] / 60:.1f} min)")
    return ep, script, timing


def cmd_sync(a):
    _sync(a.slug, set(a.scene) if a.scene else None)


def cmd_preview(a):
    ep, _, _ = _sync(a.slug)
    subprocess.run(hf("preview", *a.args), cwd=ep)


def cmd_check(a):
    ep, _, _ = _sync(a.slug)
    proc = subprocess.run(hf("check", *a.args), cwd=ep)
    raise SystemExit(proc.returncode)


def cmd_render(a):
    require_tools()
    ep, script, timing = _sync(a.slug)
    info("rendering")
    renderer.render_episode(ep, script, timing, a.draft, set(a.force) if a.force else None, a.force is not None)


def cmd_thumbnail(a):
    ep = episode_dir(a.slug)
    script = parse(ep / "script.md")
    builder.sync_brand(ep)
    page = ep / "thumbnail" / "thumbnail.html"
    if not page.exists():
        page.parent.mkdir(exist_ok=True)
        title = html.escape(str(script.meta.get("title", a.slug)))
        page.write_text((TEMPLATES / "thumbnail.html").read_text()
                        .replace("__HEADLINE__", title).replace("__TAG__", "Explainer"))
        info(f"created {page.relative_to(ROOT)} - edit it, then run this again")
    browser = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chrome")
    if not browser:
        die("chromium not found")
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "t.png"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=1280,720",
                        "--virtual-time-budget=3000", f"--screenshot={png}", page.as_uri()],
                       capture_output=True, timeout=120)
        if not png.exists():
            die("thumbnail screenshot failed")
        dst = OUT / f"{a.slug}-thumbnail.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-q:v", "2", str(dst)], check=True)
    info(f"out/{dst.name}")


def cmd_voices(a):
    """Synthesise one scene with each candidate voice (current settings otherwise), loudness-matched."""
    ep = episode_dir(a.slug)
    script = parse(ep / "script.md")
    scene = next((sc for sc in script.scenes if sc.id == a.scene), None) if a.scene else \
        next((sc for sc in script.scenes if sc.chunks), None)
    if not scene or not scene.chunks:
        die(f"no narrated scene '{a.scene}' in {a.slug}")
    table = voice.load_pronunciations(script)
    dst = OUT / "voice-samples"
    dst.mkdir(parents=True, exist_ok=True)
    if voice.engine_class(script) is voice.Chatterbox:
        # One worker for every clip: the model loads once and only the conditioning changes.
        specs = a.voices or [str(p.relative_to(ROOT)) for p in sorted((BRAND / "voices").glob("*.wav"))] + ["default"]
        tts = voice.Chatterbox(Script({**script.meta, "voice": "default"}, script.scenes))
        for n, spec in enumerate(specs, 1):
            ref = voice.chatterbox_ref(Script({**script.meta, "voice": spec}, script.scenes))
            tts.ref = str(ref) if ref else None
            audition(tts, scene, table, dst / f"{n}-{ref.stem if ref else 'default'}.wav")
        return
    for n, spec in enumerate(a.voices or AUDITION, 1):
        meta = {**script.meta, "tts": "kokoro", "voice": spec, **({"speed": a.speed} if a.speed else {})}
        tts = voice.Kokoro(Script(meta, script.scenes))
        name = re.sub(r"[^a-z0-9]+", "-", voice.voice_spec(spec).lower()).strip("-")
        audition(tts, scene, table, dst / f"{n}-{name}.wav")


def audition(tts, scene, table: dict, out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pieces = []
        for i, chunk in enumerate(scene.chunks):
            wav = Path(tmp) / f"{i}.wav"
            tts.synth_to(voice.respell(" ".join(chunk.words), table), wav)
            pieces += [voice.read_mono(wav), np.zeros(int(chunk.gap_after * voice.SAMPLE_RATE), np.float32)]
        raw = Path(tmp) / "all.wav"
        sf.write(str(raw), np.concatenate(pieces), voice.SAMPLE_RATE)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5",
                        "-ar", str(voice.SAMPLE_RATE), str(out)], check=True)
    info(f"  {out.relative_to(ROOT)}")


def main():
    p = argparse.ArgumentParser(prog="studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="scaffold a new episode")
    s.add_argument("slug")
    s.add_argument("title", nargs="?")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("status", help="scene table and length estimate")
    s.add_argument("slug")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("sync", help="narrate, align, stub scenes, write index.html")
    s.add_argument("slug")
    s.add_argument("--scene", nargs="*", help="only re-narrate these scenes (others reuse cached timings)")
    s.set_defaults(fn=cmd_sync)

    s = sub.add_parser("preview", help="sync, then open HyperFrames Studio")
    s.add_argument("slug")
    s.add_argument("args", nargs=argparse.REMAINDER, help="extra args for `hyperframes preview`")
    s.set_defaults(fn=cmd_preview)

    s = sub.add_parser("check", help="sync, then hyperframes check")
    s.add_argument("slug")
    s.add_argument("args", nargs=argparse.REMAINDER)
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("render", help="render changed scenes and master the episode to out/")
    s.add_argument("slug")
    s.add_argument("--draft", action="store_true", help="fast draft quality -> out/<slug>-draft.mp4")
    s.add_argument("--force", nargs="*", metavar="SCENE", help="re-render these scenes (or all, if none named)")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("thumbnail", help="render thumbnail/thumbnail.html to out/<slug>-thumbnail.jpg")
    s.add_argument("slug")
    s.set_defaults(fn=cmd_thumbnail)

    s = sub.add_parser("voices", help="audition Kokoro blends (or Chatterbox clips, with tts: chatterbox) -> out/voice-samples/")
    s.add_argument("slug")
    s.add_argument("--scene", help="scene id (default: the first narrated scene)")
    s.add_argument("--voices", nargs="+", metavar="SPEC", help="voices or blends, e.g. 'bf_emma*0.6 + bf_lily*0.4'; for Chatterbox, clip paths or 'default'")
    s.add_argument("--speed", type=float, help="override the script's speed for these samples")
    s.set_defaults(fn=cmd_voices)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
