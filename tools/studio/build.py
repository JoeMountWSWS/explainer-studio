"""Turn script + narration into a HyperFrames project: timing, scene stubs, index.html."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from .common import BRAND, FORMATS, HF_VERSION, LICENSED_FONTS, ROOT, TEMPLATES, die, info
from .script import Script

TIMING_RE = re.compile(r"(/\* <studio:timing> \*/)(.*?)(/\* </studio:timing> \*/)", re.S)


def frames(seconds: float, fps: int) -> int:
    return int(round(seconds * fps))


def compute_timing(script: Script, vo: dict[str, dict]) -> dict:
    """Lay scenes end to end on whole frames. Scene-local times throughout, except `start`."""
    fps = int(script.setting("fps"))
    fmt = str(script.setting("format"))
    if fmt not in FORMATS:
        die(f"unknown format '{fmt}' (have: {', '.join(FORMATS)})")
    width, height = FORMATS[fmt]
    pad_in, pad_out = float(script.setting("pad_in")), float(script.setting("pad_out"))
    t_frames, scenes = 0, []
    for sc in script.scenes:
        rec = vo[sc.id]
        has_vo = rec["duration"] > 0
        lead = pad_in if has_vo else 0.0
        need = lead + rec["duration"] + (pad_out if has_vo else 0.0)
        dur_f = max(frames(need, fps), frames(sc.min_duration, fps))
        scenes.append({
            "id": sc.id,
            "title": sc.title,
            "template": sc.template,
            "start": t_frames / fps,
            "duration": dur_f / fps,
            "voStart": lead,
            "voEnd": round(lead + rec["duration"], 3),
            "cues": {k: round(v + lead, 3) for k, v in rec["cues"].items()},
            "paragraphs": [round(p + lead, 3) for p in rec["paragraphs"]],
        })
        t_frames += dur_f
    return {"fps": fps, "format": fmt, "width": width, "height": height,
            "duration": t_frames / fps, "scenes": scenes}


DINPRO_WEIGHTS = {"Light": 300, "Regular": 400, "Medium": 500, "Bold": 700, "Black": 900}


def sync_brand(ep: Path) -> None:
    """Copy the studio's shared look into the episode (edit brand/, not these copies)."""
    dst = ep / "assets" / "brand"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BRAND / "brand.css", dst / "brand.css")
    shutil.copy2(BRAND / "vendor" / "gsap.min.js", dst / "gsap.min.js")
    shutil.copytree(BRAND / "fonts", dst / "fonts", dirs_exist_ok=True)
    # Licensed fonts are optional, so their @font-face rules are only written when the files exist.
    faces = []
    for font in sorted(LICENSED_FONTS.glob("DINPro-*.ttf")):
        weight = DINPRO_WEIGHTS.get(font.stem.removeprefix("DINPro-"))
        if weight:
            shutil.copy2(font, dst / "fonts" / font.name)
            faces.append(f'@font-face {{ font-family: "DINPro"; src: url("fonts/{font.name}") format("truetype"); '
                         f"font-weight: {weight}; font-style: normal; }}")
    if faces:
        with (dst / "brand.css").open("a") as f:
            f.write("\n/* Added by `studio sync` from brand/fonts-licensed/ */\n" + "\n".join(faces) + "\n")
    shutil.copy2(BRAND / "frame.md", ep / "frame.md")


def stub_scene(ep: Path, script: Script, scene: dict, size: tuple[int, int]) -> bool:
    path = ep / "scenes" / f"{scene['id']}.html"
    if path.exists():
        return False
    tpl = TEMPLATES / "scenes" / f"{scene['template']}.html"
    if not tpl.exists():
        choices = ", ".join(p.stem for p in (TEMPLATES / "scenes").glob("*.html"))
        die(f"scene '{scene['id']}': unknown template '{scene['template']}' (have: {choices})")
    text = tpl.read_text()
    text = text.replace("__ID__", scene["id"])
    text = text.replace("__TITLE__", html.escape(scene["title"]))
    text = text.replace("__EPISODE__", html.escape(str(script.meta.get("title", "Untitled"))))
    text = text.replace('data-width="1920" data-height="1080"', f'data-width="{size[0]}" data-height="{size[1]}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    info(f"  new scene file scenes/{scene['id']}.html (from {scene['template']} template)")
    return True


def inject_timing(ep: Path, scene: dict) -> None:
    path = ep / "scenes" / f"{scene['id']}.html"
    text = path.read_text()
    data = {k: scene[k] for k in ("duration", "voStart", "voEnd", "cues", "paragraphs")}
    data["duration"] = round(data["duration"], 4)
    block = f"\n          const T = {json.dumps(data)};\n          "
    new, n = TIMING_RE.subn(lambda m: m.group(1) + block + m.group(3), text, count=1)
    if n == 0:
        info(f"  warning: scenes/{scene['id']}.html has no /* <studio:timing> */ block; cues not updated")
        return
    if new != text:
        path.write_text(new)


def _host(scene: dict, start: float, size: tuple[int, int]) -> str:
    sid = scene["id"]
    return (
        f'      <div id="scene-{sid}" data-composition-id="scene-{sid}" data-composition-src="scenes/{sid}.html"\n'
        f'           data-start="{start:.4f}" data-duration="{scene["duration"]:.4f}" data-track-index="1"\n'
        f'           data-track-kind="graphics" data-width="{size[0]}" data-height="{size[1]}"></div>'
    )


def page(title: str, duration: float, body: str, size: tuple[int, int]) -> str:
    w, h = size
    return f"""<!doctype html>
<!-- GENERATED by `studio sync` from script.md. Do not edit: changes are overwritten. -->
<html lang="en" data-resolution="{'portrait' if h > w else 'landscape'}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>{html.escape(title)}</title>
    <script src="assets/brand/gsap.min.js"></script>
    <link rel="stylesheet" href="assets/brand/brand.css" />
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: #ffffff; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration:.4f}" data-width="{w}" data-height="{h}">
{body}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def write_index(ep: Path, script: Script, timing: dict) -> None:
    size = (timing["width"], timing["height"])
    parts = [_host(s, s["start"], size) for s in timing["scenes"]]
    for s in timing["scenes"]:
        if s["voEnd"] > s["voStart"]:
            parts.append(
                f'      <audio id="vo-{s["id"]}" src="audio/vo/{s["id"]}.wav" data-start="{s["start"] + s["voStart"]:.4f}" '
                f'data-duration="{s["voEnd"] - s["voStart"]:.4f}" data-track-index="10" data-volume="1"></audio>'
            )
    music = script.setting("music")
    if music:
        ext = Path(music).suffix
        dst = ep / "assets" / f"music{ext}"
        src = next((p for p in (ep / music, ROOT / music) if p.exists()), ROOT / music)
        if not src.exists():
            die(f"music file not found: {src}")
        shutil.copy2(src, dst)
        vol = round(10 ** (float(script.setting("music_db")) / 20), 4)
        parts.append(
            f'      <audio id="music" src="assets/music{ext}" data-start="0" data-duration="{timing["duration"]:.4f}" '
            f'data-track-index="11" data-volume="{vol}"></audio>'
        )
    (ep / "index.html").write_text(page(str(script.meta.get("title", "Untitled")), timing["duration"], "\n".join(parts), size))


def render_shell(ep: Path, scene: dict, timing: dict) -> Path:
    """A temporary root page hosting one scene at t=0 (silent), so scenes render independently."""
    shell = ep / f"_render_{scene['id']}.html"
    size = (timing["width"], timing["height"])
    shell.write_text(page(scene["id"], scene["duration"], _host(scene, 0.0, size), size))
    return shell


def ensure_project_files(ep: Path) -> None:
    pkg = ep / "package.json"
    pkg.write_text(json.dumps({
        "name": ep.name,
        "private": True,
        "type": "module",
        "scripts": {
            "dev": f"npx --yes hyperframes@{HF_VERSION} preview",
            "check": f"npx --yes hyperframes@{HF_VERSION} check",
        },
    }, indent=2) + "\n")
    hfj = ep / "hyperframes.json"
    if not hfj.exists():
        hfj.write_text(json.dumps({
            "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
            "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
            "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
            "media": {"autoProxy": True},
        }, indent=2) + "\n")


def build(ep: Path, script: Script, vo: dict[str, dict]) -> dict:
    ensure_project_files(ep)
    sync_brand(ep)
    timing = compute_timing(script, vo)
    for s in timing["scenes"]:
        stub_scene(ep, script, s, (timing["width"], timing["height"]))
        inject_timing(ep, s)
    write_index(ep, script, timing)
    (ep / "timing.json").write_text(json.dumps(timing, indent=1))
    return timing
