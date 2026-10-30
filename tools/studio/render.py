"""Render scenes (cached), concatenate, mix and master audio, write captions and chapters."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from .build import render_shell
from .common import (
    BRAND,
    HF_VERSION,
    LICENSED_FONTS,
    OUT,
    SAMPLE_RATE,
    die,
    ffprobe_duration,
    hf,
    info,
    run,
    sha,
    tree_hash,
)
from .script import Script

# ---------------------------------------------------------------- video

def render_scenes(ep: Path, timing: dict, quality: str, only: set[str] | None, force: bool) -> list[Path]:
    cache = ep / "build" / "scenes"
    cache.mkdir(parents=True, exist_ok=True)
    assets_key = tree_hash(ep / "assets")
    outputs = []
    for s in timing["scenes"]:
        scene_file = ep / "scenes" / f"{s['id']}.html"
        key = sha(scene_file, assets_key, s["duration"], timing["fps"], quality, HF_VERSION)[:16]
        target = cache / f"{s['id']}.{quality}.{key}.mp4"
        outputs.append(target)
        # Cached scenes are reused unless --force names them; missing ones always render.
        if target.exists() and not (force and (not only or s["id"] in only)):
            continue
        for old in cache.glob(f"{s['id']}.{quality}.*.mp4"):
            old.unlink()
        info(f"  render {s['id']} ({s['duration']:.1f}s)")
        shell = render_shell(ep, s, timing)
        try:
            run(hf("render", "-c", shell.name, "-f", str(timing["fps"]), "-q", quality,
                   "--quiet", "-o", str(target)), cwd=ep)
        finally:
            shell.unlink(missing_ok=True)
        got = ffprobe_duration(target)
        if abs(got - s["duration"]) > 1.5 / timing["fps"]:
            die(f"scene {s['id']} rendered {got:.3f}s, expected {s['duration']:.3f}s")
    return outputs


def concat(parts: list[Path], dst: Path) -> None:
    lst = dst.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst)])


# ---------------------------------------------------------------- audio

def build_vo_track(ep: Path, timing: dict, dst: Path) -> None:
    total = int(round(timing["duration"] * SAMPLE_RATE))
    track = np.zeros(total, dtype=np.float32)
    for s in timing["scenes"]:
        wav = ep / "audio" / "vo" / f"{s['id']}.wav"
        if not wav.exists():
            continue
        data, _ = sf.read(str(wav), dtype="float32")
        at = int(round((s["start"] + s["voStart"]) * SAMPLE_RATE))
        end = min(at + len(data), total)
        track[at:end] += data[: end - at]
    sf.write(str(dst), track, SAMPLE_RATE, subtype="PCM_24")


def mix(ep: Path, script: Script, timing: dict, vo: Path, dst: Path) -> dict:
    """Narration (+ optional ducked music bed), mastered to the loudness target in two passes."""
    dur = timing["duration"]
    target_i, target_tp = float(script.setting("loudness")), float(script.setting("true_peak"))
    music = next(iter(sorted((ep / "assets").glob("music.*"))), None) if script.setting("music") else None

    inputs = ["-i", str(vo)]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        gain = float(script.setting("music_db"))
        fade_in = float(script.setting("music_fade_in"))
        fade = f"afade=t=in:d={fade_in}," if fade_in > 0 else ""
        graph = (
            "[0:a]aformat=channel_layouts=mono,asplit=2[v1][vkey];"
            f"[1:a]aformat=channel_layouts=stereo,atrim=0:{dur:.3f},volume={gain}dB,"
            f"{fade}afade=t=out:st={max(dur - 4, 0):.3f}:d=4[m];"
            "[m][vkey]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[duck];"
            "[v1]pan=stereo|c0=c0|c1=c0[vs];"
            "[vs][duck]amix=inputs=2:duration=first:normalize=0[mix]"
        )
    else:
        graph = "[0:a]pan=stereo|c0=c0|c1=c0[mix]"
    pre = dst.with_name("premix.wav")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[mix]",
         "-t", f"{dur:.3f}", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s24le", str(pre)])

    ln = f"loudnorm=I={target_i}:TP={target_tp}:LRA=11"
    # Pass 1 measures (loudnorm prints its JSON on stderr); pass 2 applies a linear gain.
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af",
                           f"{ln}:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr, re.S).group(0))
    second = (f"{ln}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", second, "-ar", str(SAMPLE_RATE),
         "-c:a", "pcm_s24le", str(dst)])
    pre.unlink()
    return m


# ---------------------------------------------------------------- captions & chapters

def _ts(t: float, sep: str = ",") -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def _caption_cues(ep: Path, timing: dict, max_chars: int, max_secs: float, max_words: int = 99,
                  min_sentence: int = 12) -> list[list[dict]]:
    """Group the script's own words (correct spelling) into cues; each word carries absolute times."""
    cues = []
    for s in timing["scenes"]:
        wf = ep / "audio" / "vo" / f"{s['id']}.words.json"
        words = json.loads(wf.read_text(encoding="utf-8"))["words"] if wf.exists() else []
        offset = s["start"] + s["voStart"]
        group: list[dict] = []

        def flush():
            if group:
                cues.append(list(group))
                group.clear()

        for w in words:
            w = {"text": w["text"], "start": offset + w["start"], "end": offset + w["end"]}
            text_len = len(" ".join(x["text"] for x in group + [w]))
            if group and (text_len > 2 * max_chars or len(group) >= max_words
                          or w["end"] - group[0]["start"] > max_secs):
                flush()
            group.append(w)
            sofar = len(" ".join(x["text"] for x in group))
            if re.search(r"[.!?]['\")\]]*$", w["text"]) and sofar > min_sentence:
                flush()  # end of sentence
            elif re.search(r"[,;:—]['\")\]]*$", w["text"]) and sofar > max_chars:
                flush()  # a clause break once the cue is already a full line
        flush()
    return cues


def captions(ep: Path, timing: dict, dst: Path, max_chars: int = 42, max_secs: float = 6.0) -> int:
    """SRT from the script's own words (correct spelling) with aligned timings; 2 lines max."""
    cues = [(g[0]["start"], g[-1]["end"], [w["text"] for w in g]) for g in _caption_cues(ep, timing, max_chars, max_secs)]
    lines = []
    for i, (a, b, words) in enumerate(cues, 1):
        nxt = cues[i][0] if i < len(cues) else b + 1.0
        b = min(max(b + 0.25, a + 1.0), nxt - 0.04)  # linger a little, never overlap the next
        text = " ".join(words)
        if len(text) > max_chars:  # break into two balanced lines at a word boundary
            mid, best = len(text) / 2, None
            for k in range(1, len(words)):
                cut = len(" ".join(words[:k]))
                if best is None or abs(cut - mid) < abs(best[0] - mid):
                    best = (cut, k)
            text = " ".join(words[: best[1]]) + "\n" + " ".join(words[best[1]:])
        lines.append(f"{i}\n{_ts(a)} --> {_ts(b)}\n{text}\n")
    dst.write_text("\n".join(lines), encoding="utf-8")
    return len(cues)


def chapters(timing: dict) -> tuple[list[str], list[str]]:
    """YouTube chapter lines (consecutive scenes sharing a title merge) and any rule violations."""
    merged: list[list] = []
    for s in timing["scenes"]:
        if merged and merged[-1][1] == s["title"]:
            merged[-1][2] += s["duration"]
        else:
            merged.append([s["start"], s["title"], s["duration"]])
    out, problems = [], []
    for start, title, dur in merged:
        t = int(start)
        stamp = f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"
        out.append(f"{stamp} {title}")
        if dur < 10:
            problems.append(f"chapter '{title}' is {dur:.1f}s (YouTube needs >= 10s)")
    if len(merged) < 3:
        problems.append("YouTube needs at least 3 chapters to show them")
    return out, problems


def _ass_color(hexcolor: str) -> str:
    r, g, b = hexcolor[1:3], hexcolor[3:5], hexcolor[5:7]
    return f"&H00{b}{g}{r}".upper()


def caption_font() -> tuple[str, Path]:
    """(libass font name, fonts dir) for burned-in captions."""
    if (LICENSED_FONTS / "DINPro-Bold.ttf").exists():
        return "DINPro-Bold", LICENSED_FONTS
    return "Source Sans 3 Bold", BRAND / "fonts"


def ass_captions(ep: Path, timing: dict, dst: Path) -> int:
    """Burn-in captions in house style: white sans on a dark tag box, the spoken word in red.
    Short single-line cues (a few words), one event per word so the highlight follows the voice.
    libass can't pick weights from the variable font, so this relies on a static bold: DINPro-Bold from
    brand/fonts-licensed/ when present, else brand/fonts/SourceSans3-Bold.ttf (see caption_font())."""
    w, h = timing["width"], timing["height"]
    portrait = h > w
    size, y = (72, int(h * 0.69)) if portrait else (52, int(h * 0.86))  # reel caption band / lower third
    ink, red, white = _ass_color("#1b2129"), _ass_color("#e71e25"), _ass_color("#ffffff")
    font = caption_font()[0]
    head = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 2",
        "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        f"Style: Cap,{font},{size},{white},{white},{ink},{ink},-1,0,0,0,100,100,0,0,3,14,0,5,0,0,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    cues = _caption_cues(ep, timing, max_chars=13 if portrait else 21, max_secs=2.5, max_words=4, min_sentence=0)
    events = []
    for i, cue in enumerate(cues):
        nxt = cues[i + 1][0]["start"] if i + 1 < len(cues) else cue[-1]["end"] + 1.0
        cue_end = min(cue[-1]["end"] + 0.3, nxt)
        for k, word in enumerate(cue):
            a = cue[0]["start"] if k == 0 else word["start"]
            b = cue[k + 1]["start"] if k + 1 < len(cue) else cue_end
            text = " ".join(("{\\c" + red + "&}" + x["text"] + "{\\c" + white + "&}") if j == k else x["text"]
                            for j, x in enumerate(cue))
            if font == "DINPro-Bold":  # its fi/fl ligatures are broken; a zero-width non-joiner stops HarfBuzz forming them
                text = re.sub(r"f(?=[il])", "f‌", text)
            events.append(f"Dialogue: 0,{_ts(a, '.')[1:-1]},{_ts(b, '.')[1:-1]},Cap,,0,0,0,,{{\\pos({w // 2},{y})}}{text}")
    dst.write_text("\n".join(head + events) + "\n", encoding="utf-8")
    return len(cues)


# ---------------------------------------------------------------- top level

def render_episode(ep: Path, script: Script, timing: dict, draft: bool, only: set[str] | None, force: bool) -> Path:
    quality = "draft" if draft else "high"
    build = ep / "build"
    build.mkdir(exist_ok=True)
    parts = render_scenes(ep, timing, quality, only, force)

    info("  concatenating scenes")
    video = build / f"video.{quality}.mp4"
    concat(parts, video)

    info("  mixing and mastering audio")
    vo = build / "vo.wav"
    build_vo_track(ep, timing, vo)
    master = build / "master.wav"
    m = mix(ep, script, timing, vo, master)

    OUT.mkdir(exist_ok=True)
    name = ep.name + ("-draft" if draft else "")
    final = OUT / f"{name}.mp4"
    vcodec = ["-c:v", "copy"]
    if script.setting("burn_captions"):
        info("  burning in captions")
        ass = build / "captions.ass"
        ass_captions(ep, timing, ass)
        crf = "26" if draft else "16"
        # A relative fontsdir (ffmpeg runs in build/): the colon in a Windows drive path splits filter options.
        fonts = build / "fonts"
        shutil.copytree(caption_font()[1], fonts, dirs_exist_ok=True)
        vcodec = ["-vf", f"ass={ass.name}:fontsdir={fonts.name}", "-c:v", "libx264", "-preset", "medium",
                  "-crf", crf, "-pix_fmt", "yuv420p"]
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video.resolve()), "-i", str(master.resolve()), "-map", "0:v", "-map", "1:a",
         *vcodec, "-c:a", "aac", "-b:a", "384k", "-ar", str(SAMPLE_RATE),
         "-movflags", "+faststart", str(final.resolve())], cwd=build)

    n = captions(ep, timing, OUT / f"{ep.name}.srt")
    chap, problems = chapters(timing)
    if timing.get("format") == "reel":
        problems = []  # chapters are a YouTube long-form feature
    (OUT / f"{ep.name}.chapters.txt").write_text("\n".join(chap) + "\n", encoding="utf-8")

    info(f"\n  {final.relative_to(OUT.parent)}  {ffprobe_duration(final):.1f}s")
    info(f"  loudness in {m['input_i']} LUFS -> {script.setting('loudness')} LUFS target")
    info(f"  captions: out/{ep.name}.srt ({n} cues)    chapters: out/{ep.name}.chapters.txt")
    for p in problems:
        info(f"  note: {p}")
    return final
