import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from conftest import DEMO, vo_record, write_vo
from studio import render
from studio.script import parse


def test_ts():
    assert render._ts(0) == "00:00:00,000"
    assert render._ts(3725.0456) == "01:02:05,046"
    assert render._ts(1.5, ".") == "00:00:01.500"


def _timing(*scenes):
    """scenes: (id, title, duration); laid end to end."""
    out, t = [], 0.0
    for sid, title, dur in scenes:
        out.append({"id": sid, "title": title, "start": t, "duration": dur, "voStart": 0.5})
        t += dur
    return {"scenes": out, "width": 1920, "height": 1080, "duration": t}


def test_chapters_merge_consecutive_titles():
    lines, problems = render.chapters(_timing(("a", "Intro", 6), ("b", "Intro", 6), ("c", "Middle", 30),
                                              ("d", "End", 12)))
    assert lines == ["0:00 Intro", "0:12 Middle", "0:42 End"]
    assert problems == []


def test_chapters_report_youtube_rules():
    lines, problems = render.chapters(_timing(("a", "Intro", 4), ("b", "Rest", 3700)))
    assert lines == ["0:00 Intro", "0:04 Rest"]
    assert problems == ["chapter 'Intro' is 4.0s (YouTube needs >= 10s)", "YouTube needs at least 3 chapters to show them"]
    lines, _ = render.chapters(_timing(("a", "A", 3700), ("b", "B", 20)))
    assert lines[1] == "1:01:40 B"


def _episode(tmp_path):
    ep = tmp_path / "ep"
    write_vo(ep, "a", vo_record([
        ("The", 0.0, 0.2), ("Commune", 0.2, 0.7), ("lasted", 0.7, 1.0), ("seventy-two", 1.0, 1.6),
        ("days,", 1.6, 2.0), ("from", 2.0, 2.2), ("March", 2.2, 2.6), ("to", 2.6, 2.7), ("May.", 2.7, 3.2),
        ("Then", 3.6, 3.9), ("it", 3.9, 4.0), ("fell.", 4.0, 4.5),
    ]))
    return ep, _timing(("a", "Only", 10), ("b", "Missing", 2))  # scene b has no words.json


def test_captions_srt(tmp_path):
    ep, timing = _episode(tmp_path)
    n = render.captions(ep, timing, tmp_path / "out.srt", max_chars=20)
    srt = (tmp_path / "out.srt").read_text(encoding="utf-8")
    assert n == 3
    assert srt.split("\n\n") == [
        "1\n00:00:00,500 --> 00:00:02,460\nThe Commune lasted\nseventy-two days,",  # clause break; ends before the next
        "2\n00:00:02,500 --> 00:00:03,950\nfrom March to May.",  # lingers 0.25s past "May."
        "3\n00:00:04,100 --> 00:00:05,250\nThen it fell.\n",
    ]


def test_ass_captions_highlight_each_word(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "LICENSED_FONTS", tmp_path / "none")
    ep, timing = _episode(tmp_path)
    n = render.ass_captions(ep, timing, tmp_path / "out.ass")
    ass = (tmp_path / "out.ass").read_text(encoding="utf-8")
    events = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    assert n >= 3 and len(events) == 12  # one event per word
    assert "Source Sans 3 Bold" in ass and "PlayResY: 1080" in ass
    assert events[0].startswith("Dialogue: 0,0:00:00.50,") and "{\\c&H00251EE7&}The{" in events[0]


def test_ass_captions_dinpro_breaks_ligatures(tmp_path, monkeypatch):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "DINPro-Bold.ttf").write_bytes(b"")
    monkeypatch.setattr(render, "LICENSED_FONTS", fonts)
    ep = tmp_path / "ep"
    write_vo(ep, "a", vo_record([("final", 0.0, 0.5), ("flag.", 0.5, 1.0)]))
    render.ass_captions(ep, _timing(("a", "A", 3)) | {"width": 1080, "height": 1920}, tmp_path / "out.ass")
    ass = (tmp_path / "out.ass").read_text(encoding="utf-8")
    assert "DINPro-Bold" in ass and "f‌inal" in ass and "f‌lag." in ass
    assert "PlayResY: 1920" in ass


def test_ass_color_is_bgr():
    assert render._ass_color("#e71e25") == "&H00251EE7"


def test_demo_captions(tmp_path):
    timing = json.loads((DEMO / "timing.json").read_text(encoding="utf-8"))
    n = render.captions(DEMO, timing, tmp_path / "demo.srt")
    blocks = (tmp_path / "demo.srt").read_text(encoding="utf-8").strip().split("\n\n")
    assert n == len(blocks) > 0
    for block in blocks:
        assert all(len(line) <= 42 for line in block.splitlines()[2:])
        assert len(block.splitlines()) <= 4  # index, time, at most two lines


# ---------------------------------------------------------------- render_scenes (cache)

@pytest.fixture
def scene_cache(tmp_path, monkeypatch):
    """Two scene files, with HyperFrames and ffprobe stubbed: `rendered` lists each scene id rendered."""
    ep = tmp_path / "ep"
    (ep / "scenes").mkdir(parents=True)
    (ep / "assets").mkdir()
    for sid in "ab":
        (ep / "scenes" / f"{sid}.html").write_text(f"<div>{sid}</div>", encoding="utf-8")
    timing = {"fps": 30, "width": 1920, "height": 1080,
              "scenes": [{"id": "a", "duration": 3.0}, {"id": "b", "duration": 2.0}]}
    rendered, shells = [], []

    def shell(ep, s, timing):
        p = ep / f"_render_{s['id']}.html"
        p.write_text("shell", encoding="utf-8")
        shells.append(p)
        return p

    def fake_run(cmd, cwd=None, **kw):
        out = Path(cmd[cmd.index("-o") + 1])
        rendered.append(out.name.split(".")[0])
        out.write_bytes(b"mp4")

    monkeypatch.setattr(render, "render_shell", shell)
    monkeypatch.setattr(render, "run", fake_run)
    monkeypatch.setattr(render, "ffprobe_duration",
                        lambda p: next(s["duration"] for s in timing["scenes"] if p.name.startswith(s["id"] + ".")))
    return ep, timing, rendered, shells


def test_render_scenes_renders_once_then_reuses_the_cache(scene_cache):
    ep, timing, rendered, shells = scene_cache
    first = render.render_scenes(ep, timing, "draft", None, False)
    assert rendered == ["a", "b"]
    assert [p.name.split(".")[:2] for p in first] == [["a", "draft"], ["b", "draft"]]
    assert all(p.exists() for p in first) and not any(s.exists() for s in shells)
    assert render.render_scenes(ep, timing, "draft", None, False) == first
    assert rendered == ["a", "b"]
    # Draft and high quality are cached separately.
    render.render_scenes(ep, timing, "high", None, False)
    assert rendered == ["a", "b", "a", "b"]


def test_render_scenes_force(scene_cache):
    ep, timing, rendered, _ = scene_cache
    render.render_scenes(ep, timing, "draft", None, False)
    render.render_scenes(ep, timing, "draft", {"a"}, True)
    assert rendered == ["a", "b", "a"]
    render.render_scenes(ep, timing, "draft", None, True)
    assert rendered == ["a", "b", "a", "a", "b"]


@pytest.mark.parametrize("change", ["html", "asset", "duration", "size"])
def test_render_scenes_rerenders_a_changed_scene_and_drops_its_old_file(scene_cache, change):
    ep, timing, rendered, _ = scene_cache
    render.render_scenes(ep, timing, "draft", None, False)
    if change == "html":
        (ep / "scenes" / "a.html").write_text("<div>a, edited</div>", encoding="utf-8")
    elif change == "asset":
        (ep / "assets" / "photo.jpg").write_bytes(b"jpg")
    elif change == "duration":
        timing["scenes"][0]["duration"] = 3.5
    else:  # format: reel re-uses the same scene files at another frame size
        timing.update(width=1080, height=1920)
    rendered.clear()
    render.render_scenes(ep, timing, "draft", None, False)
    assert rendered == (["a"] if change in ("html", "duration") else ["a", "b"])
    assert len(list((ep / "build" / "scenes").glob("a.draft.*.mp4"))) == 1


def test_render_scenes_removes_the_shell_when_render_fails(scene_cache, monkeypatch):
    ep, timing, _, shells = scene_cache
    monkeypatch.setattr(render, "run", lambda *a, **k: render.die("boom"))
    with pytest.raises(SystemExit):
        render.render_scenes(ep, timing, "draft", None, False)
    assert shells and not any(s.exists() for s in shells)


def test_render_scenes_rejects_a_wrong_length(scene_cache, monkeypatch, capsys):
    ep, timing, _, _ = scene_cache
    monkeypatch.setattr(render, "ffprobe_duration", lambda p: 2.9)  # 3 frames short of 3.0s
    with pytest.raises(SystemExit):
        render.render_scenes(ep, timing, "draft", None, False)
    assert "scene a rendered 2.900s, expected 3.000s" in capsys.readouterr().err


# ---------------------------------------------------------------- audio

def test_build_vo_track_places_each_scene_at_its_narration_start(tmp_path):
    ep, sr = tmp_path / "ep", render.SAMPLE_RATE
    vo = ep / "audio" / "vo"
    vo.mkdir(parents=True)
    sf.write(str(vo / "a.wav"), np.full(sr // 2, 0.25, np.float32), sr)
    sf.write(str(vo / "c.wav"), np.full(sr, 0.5, np.float32), sr)  # runs past the end
    timing = {"duration": 4.0, "scenes": [
        {"id": "a", "start": 0.0, "voStart": 0.5},
        {"id": "b", "start": 1.5, "voStart": 0.5},  # silent: no wav
        {"id": "c", "start": 3.0, "voStart": 0.5},
    ]}
    render.build_vo_track(ep, timing, tmp_path / "vo.wav")
    track, rate = sf.read(str(tmp_path / "vo.wav"), dtype="float32")
    assert rate == sr and len(track) == 4 * sr and sf.info(str(tmp_path / "vo.wav")).subtype == "PCM_24"
    assert np.allclose(track[: sr // 2], 0) and np.allclose(track[sr // 2: sr], 0.25, atol=1e-4)
    assert np.allclose(track[sr: int(3.5 * sr)], 0)
    assert np.allclose(track[int(3.5 * sr):], 0.5, atol=1e-4)


needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _loudness(path: Path) -> float:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                           "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    return float(json.JSONDecoder().raw_decode(proc.stderr[proc.stderr.rindex("{"):])[0]["input_i"])


def _tone(path: Path, secs: float, freq: float, level: float, channels: int = 1) -> None:
    t = np.arange(int(secs * render.SAMPLE_RATE)) / render.SAMPLE_RATE
    wave = (level * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), np.stack([wave] * channels, axis=1), render.SAMPLE_RATE)


@needs_ffmpeg
@pytest.mark.parametrize("front", ["", "music: bed.wav\n", "music: bed.wav\nmusic_fade_in: 0\n"])
def test_mix_masters_to_the_loudness_target(write_script, tmp_path, front):
    script = write_script(f"---\n{front}---\n## a: A\nHello.\n")
    ep = tmp_path / "ep"
    if front:
        (ep / "assets").mkdir()
        _tone(ep / "assets" / "music.wav", 2.0, 220, 0.3, channels=2)  # shorter than the episode: it loops
    _tone(tmp_path / "vo.wav", 6.0, 440, 0.05)
    m = render.mix(ep, script, {"duration": 6.0}, tmp_path / "vo.wav", tmp_path / "master.wav")
    out = sf.info(str(tmp_path / "master.wav"))
    assert out.channels == 2 and out.samplerate == render.SAMPLE_RATE
    assert out.duration == pytest.approx(6.0, abs=0.01)
    assert float(m["input_i"]) < -20  # measured before mastering
    assert _loudness(tmp_path / "master.wav") == pytest.approx(-14, abs=1)
    assert not (tmp_path / "premix.wav").exists()


def test_mix_reports_a_failed_measurement(write_script, tmp_path, monkeypatch, capsys):
    script = write_script("## a: A\nHello.\n")
    monkeypatch.setattr(render, "run", lambda *a, **k: "")
    monkeypatch.setattr(render.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "premix.wav: Invalid data"))
    with pytest.raises(SystemExit):
        render.mix(tmp_path / "ep", script, {"duration": 1.0}, tmp_path / "vo.wav", tmp_path / "master.wav")
    assert "Invalid data" in capsys.readouterr().err


# ---------------------------------------------------------------- render_episode

@pytest.fixture
def assembly(tmp_path, monkeypatch):
    """render_episode with the scene renderer, audio and ffmpeg stubbed; returns (go, ffmpeg argv log)."""
    calls = []
    monkeypatch.setattr(render, "OUT", tmp_path / "out")
    monkeypatch.setattr(render, "LICENSED_FONTS", tmp_path / "none")
    monkeypatch.setattr(render, "render_scenes", lambda *a: [])
    monkeypatch.setattr(render, "concat", lambda parts, dst: None)
    monkeypatch.setattr(render, "build_vo_track", lambda ep, timing, dst: None)
    monkeypatch.setattr(render, "mix", lambda *a: {"input_i": "-20.5"})
    monkeypatch.setattr(render, "ffprobe_duration", lambda p: 12.0)

    def fake_run(cmd, cwd=None, **kw):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"mp4")
    monkeypatch.setattr(render, "run", fake_run)

    def go(front: str = "", draft: bool = False, fmt: str = "landscape"):
        ep, timing = _episode(tmp_path)
        timing["format"] = fmt
        (tmp_path / "script.md").write_text(f"---\n{front}---\n## a: A\nHello.\n", encoding="utf-8")
        return render.render_episode(ep, parse(tmp_path / "script.md"), timing, draft, None, False)
    return go, calls


def test_render_episode_copies_the_video_and_writes_captions_and_chapters(assembly, tmp_path, capsys):
    go, calls = assembly
    final = go(draft=True)
    assert final == tmp_path / "out" / "ep-draft.mp4" and final.exists()
    assert calls[-1][calls[-1].index("-c:v") + 1] == "copy"
    assert (tmp_path / "out" / "ep.srt").read_text(encoding="utf-8").startswith("1\n00:00:00,500")
    assert (tmp_path / "out" / "ep.chapters.txt").read_text(encoding="utf-8") == "0:00 Only\n0:10 Missing\n"
    out = capsys.readouterr().out
    assert "loudness in -20.5 LUFS -> -14 LUFS target" in out
    assert "note: " in out  # too few chapters for YouTube


def test_render_episode_burns_captions_into_reels(assembly, tmp_path, capsys):
    go, calls = assembly
    final = go("burn_captions: true\n", fmt="reel")
    assert final.name == "ep.mp4"
    argv = calls[-1]
    assert argv[argv.index("-c:v") + 1] == "libx264" and argv[argv.index("-crf") + 1] == "16"
    # A relative fontsdir (ffmpeg runs in build/): the colon of a Windows drive path would split the options.
    assert argv[argv.index("-vf") + 1] == "ass=captions.ass:fontsdir=fonts"
    assert any((tmp_path / "ep" / "build" / "fonts").glob("*.ttf"))
    assert (tmp_path / "ep" / "build" / "captions.ass").exists()
    assert "note: " not in capsys.readouterr().out  # chapters are a long-form feature


def test_concat_list_uses_forward_slashes(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "run", lambda cmd: None)
    render.concat([tmp_path / "a.mp4"], tmp_path / "v.mp4")
    assert (tmp_path / "v.txt").read_text(encoding="utf-8") == f"file '{(tmp_path / 'a.mp4').resolve().as_posix()}'\n"
