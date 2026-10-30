"""Automated QA of the finished master: loudness, black/frozen frames, silences, format, speech, deliverables."""

from __future__ import annotations

import difflib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import voice
from .common import OUT, SAMPLE_RATE, die, info, run
from .render import chapters
from .script import Script

LOUDNESS_TOL = 1.0       # LU either side of the `loudness` target
TRUE_PEAK_TOL = 0.3      # dB above the `true_peak` ceiling
BLACK_MIN = 0.5          # seconds of black before it is reported
FREEZE_MIN = 15.0        # seconds of identical frames before it is reported (a held quote or stat is normal)
FADE_WINDOW = 0.6        # black this close to a scene boundary is the exit fade, not a fault
SILENCE_DB = -50
SILENCE_SLACK = 0.5      # seconds beyond the longest planned gap
SPEECH_WARN, SPEECH_ERROR = 0.90, 0.75
SPEECH_LISTED = 10


@dataclass
class Finding:
    level: str  # ok | warn | error
    name: str
    message: str


def _ffmpeg(path: Path, *args: str) -> str:
    """Run an analysis pass over `path` and return ffmpeg's log (the filters report on stderr)."""
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), *args, "-f", "null", "-"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        die(f"ffmpeg could not read {path.name}:\n" + "\n".join(proc.stderr.strip().splitlines()[-10:]))
    return proc.stderr


# ---------------------------------------------------------------- loudness

def check_loudness(path: Path, target: float, ceiling: float) -> Finding:
    log = _ffmpeg(path, "-vn", "-af", "ebur128=peak=true")
    summary = log[log.rindex("Summary:"):] if "Summary:" in log else ""
    i = re.search(r"\bI:\s+(-?[\d.]+|-inf) LUFS", summary)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
    if not i or not tp:
        return Finding("error", "loudness", "could not measure (no audio?)")
    loud, peak = float(i.group(1)), float(tp.group(1))
    text = f"{loud:.1f} LUFS (target {target:g}), true peak {peak:.1f} dBTP (ceiling {ceiling:g})"
    if abs(loud - target) > LOUDNESS_TOL or peak > ceiling + TRUE_PEAK_TOL:
        return Finding("error", "loudness", text)
    return Finding("ok", "loudness", text)


# ---------------------------------------------------------------- video

def _boundaries(timing: dict) -> list[float]:
    return [s["start"] for s in timing["scenes"]] + [timing["duration"]]


def _hms(t: float) -> str:
    return f"{int(t) // 60}:{t % 60:04.1f}"


def check_video(path: Path, timing: dict) -> list[Finding]:
    """Black frames (error) and frozen video (warning) away from scene boundaries."""
    log = _ffmpeg(path, "-an", "-vf", f"blackdetect=d={BLACK_MIN}:pix_th=0.10,freezedetect=n=-50dB:d={FREEZE_MIN}")
    bounds = _boundaries(timing)

    def at_boundary(a: float, b: float) -> bool:
        return any(abs(a - t) <= FADE_WINDOW and abs(b - t) <= FADE_WINDOW for t in bounds)

    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]
    black = [(a, b) for a, b in black if not at_boundary(a, b)]
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
    durs = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", log)]
    frozen = [(a, a + d) for a, d in zip(starts, durs)]

    out = []
    if black:
        spans = ", ".join(f"{_hms(a)}-{_hms(b)}" for a, b in black[:5])
        out.append(Finding("error", "black frames", f"{len(black)} stretch(es) of black: {spans}"))
    else:
        out.append(Finding("ok", "black frames", "none"))
    if frozen:
        spans = ", ".join(f"{_hms(a)}-{_hms(b)}" for a, b in frozen[:5])
        out.append(Finding("warn", "frozen video", f"{len(frozen)} stretch(es) frozen for {FREEZE_MIN:g}s+: {spans}"))
    else:
        out.append(Finding("ok", "frozen video", f"nothing frozen for {FREEZE_MIN:g}s+"))
    return out


# ---------------------------------------------------------------- silence

def _subtract(a: float, b: float, holes: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pieces = [(a, b)]
    for x, y in holes:
        nxt = []
        for p, q in pieces:
            if y <= p or x >= q:
                nxt.append((p, q))
                continue
            if x > p:
                nxt.append((p, x))
            if y < q:
                nxt.append((y, q))
        pieces = nxt
    return pieces


def silence_limit(script: Script, timing: dict) -> float:
    """Longest silence the script itself plans: a {pause}, a paragraph gap, or one scene's pads, plus slack."""
    gaps = [c.gap_after for sc in script.scenes for c in sc.chunks]
    planned = max(gaps + [float(script.setting("paragraph_gap")),
                          float(script.setting("pad_in")) + float(script.setting("pad_out"))])
    return planned + SILENCE_SLACK


def check_silence(path: Path, script: Script, timing: dict) -> Finding:
    limit = silence_limit(script, timing)
    log = _ffmpeg(path, "-vn", "-af", f"silencedetect=noise={SILENCE_DB}dB:d={limit:g}")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    ends += [timing["duration"]] * (len(starts) - len(ends))  # silent to the very end
    # Scenes without narration are allowed to be quiet (their own pads still count).
    quiet = [(s["start"], s["start"] + s["duration"]) for s in timing["scenes"] if s["voEnd"] <= s["voStart"]]
    bad = []
    for a, b in zip(starts, ends):
        bad += [(p, q) for p, q in _subtract(max(a, 0.0), b, quiet) if q - p > limit]
    if bad:
        spans = ", ".join(f"{_hms(p)}-{_hms(q)} ({q - p:.1f}s)" for p, q in bad[:5])
        return Finding("error", "silence", f"quiet for longer than {limit:.1f}s: {spans}")
    return Finding("ok", "silence", f"no gap longer than {limit:.1f}s")


# ---------------------------------------------------------------- format

def check_format(path: Path, timing: dict) -> list[Finding]:
    proc = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                "-of", "json", str(path)])
    probe = json.loads(proc)
    video = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
    out = []
    if not video:
        return [Finding("error", "format", "no video stream")]
    num, den = (int(x) for x in video["r_frame_rate"].split("/"))
    fps = num / den
    want = f"{timing['width']}x{timing['height']} @ {timing['fps']} fps"
    got = f"{video['width']}x{video['height']} @ {fps:g} fps"
    ok = (video["width"], video["height"]) == (timing["width"], timing["height"]) and abs(fps - timing["fps"]) < 0.01
    out.append(Finding("ok" if ok else "error", "format", got if ok else f"{got}, expected {want}"))
    dur, frame = float(probe["format"]["duration"]), 1 / timing["fps"]
    text = f"{dur:.2f}s (timing.json says {timing['duration']:.2f}s)"
    out.append(Finding("ok" if abs(dur - timing["duration"]) <= 3 * frame else "error", "duration", text))
    if not audio:
        out.append(Finding("error", "audio stream", "missing"))
    return out


# ---------------------------------------------------------------- speech

def _words(script: Script) -> list[str]:
    return [n for sc in script.scenes for w in sc.words if (n := voice._norm(w))]


def check_speech(path: Path, script: Script) -> Finding:
    """Transcribe the mastered audio and compare it with the script: does the voice survive the music bed?"""
    want = _words(script)
    if not want:
        return Finding("ok", "speech", "no narration to check")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "master.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), str(wav)])
        heard = [n for w in voice.transcribe(wav) if (n := voice._norm(w["text"]))]
    match = difflib.SequenceMatcher(None, want, heard, autojunk=False)
    hit = [False] * len(want)
    for blk in match.get_matching_blocks():
        for k in range(blk.size):
            hit[blk.a + k] = True
    ratio = sum(hit) / len(want)
    text = f"{ratio:.0%} of {len(want)} script words heard"
    level = "error" if ratio < SPEECH_ERROR else "warn" if ratio < SPEECH_WARN else "ok"
    if level != "ok":
        missed = [w for w, h in zip(want, hit) if not h]
        text += "; not heard: " + " ".join(missed[:SPEECH_LISTED]) + (" ..." if len(missed) > SPEECH_LISTED else "")
    return Finding(level, "speech", text)


# ---------------------------------------------------------------- deliverables

def check_deliverables(slug: str, timing: dict) -> list[Finding]:
    out = []
    srt, chap = OUT / f"{slug}.srt", OUT / f"{slug}.chapters.txt"
    out.append(Finding("ok" if srt.exists() and srt.stat().st_size else "error", "captions", f"out/{srt.name}"))
    if not chap.exists() or not chap.stat().st_size:
        return out + [Finding("error", "chapters", f"out/{chap.name} missing")]
    lines = chap.read_text(encoding="utf-8").splitlines()
    if not lines[0].startswith("0:00"):
        out.append(Finding("error", "chapters", "the first chapter must start at 0:00"))
    elif timing.get("format") == "reel":
        out.append(Finding("ok", "chapters", "reel (chapters are a YouTube long-form feature)"))
    else:
        problems = chapters(timing)[1]
        out.append(Finding("warn", "chapters", "; ".join(problems)) if problems
                   else Finding("ok", "chapters", f"{len(lines)} chapters, first at 0:00, each 10s or longer"))
    return out


# ---------------------------------------------------------------- top level

def verify_master(ep: Path, script: Script, timing: dict, master: Path, speech: bool = True,
                  deliverables: bool = True) -> list[Finding]:
    if not master.exists():
        die(f"no master at {master}: run `studio render {ep.name}` first")
    findings = check_format(master, timing)
    findings.append(check_loudness(master, float(script.setting("loudness")), float(script.setting("true_peak"))))
    findings += check_video(master, timing)
    findings.append(check_silence(master, script, timing))
    if speech:
        findings.append(check_speech(master, script))
    if deliverables:
        findings += check_deliverables(ep.name, timing)
    return findings


def report(findings: list[Finding]) -> int:
    """Print one line per finding, `setup --check` style. Returns the number of errors."""
    for f in findings:
        info(f"  {f.level.replace('error', 'ERROR'):<6} {f.name:<14} {f.message}")
    errors = sum(f.level == "error" for f in findings)
    warns = sum(f.level == "warn" for f in findings)
    info(f"\n  {errors} error(s), {warns} warning(s)")
    return errors
