import json

from conftest import DEMO, vo_record, write_vo
from studio import render


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


def test_burned_captions_use_a_relative_fontsdir(write_script, tmp_path, monkeypatch):
    # An absolute fontsdir breaks on Windows: the drive colon splits ffmpeg filter options.
    script = write_script("---\nformat: reel\nburn_captions: true\n---\n## a: A\nHi.\n")
    ep = tmp_path / "ep"
    write_vo(ep, "a", vo_record([("Hi.", 0.0, 0.5)]))
    timing = _timing(("a", "A", 3)) | {"width": 1080, "height": 1920, "format": "reel"}
    calls = []
    monkeypatch.setattr(render, "OUT", tmp_path / "out")
    monkeypatch.setattr(render, "render_scenes", lambda *a: [])
    monkeypatch.setattr(render, "concat", lambda *a: None)
    monkeypatch.setattr(render, "build_vo_track", lambda *a: None)
    monkeypatch.setattr(render, "mix", lambda *a: {"input_i": "-20"})
    monkeypatch.setattr(render, "ffprobe_duration", lambda p: 3.0)
    monkeypatch.setattr(render, "run", lambda cmd, cwd=None: calls.append((cmd, cwd)))
    render.render_episode(ep, script, timing, draft=True, only=None, force=False)
    [(cmd, cwd)] = calls
    assert cwd == ep / "build"
    assert cmd[cmd.index("-vf") + 1] == "ass=captions.ass:fontsdir=fonts"
    assert any((ep / "build" / "fonts").glob("*.ttf"))


def test_concat_list_uses_forward_slashes(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "run", lambda cmd: None)
    render.concat([tmp_path / "a.mp4"], tmp_path / "v.mp4")
    assert (tmp_path / "v.txt").read_text(encoding="utf-8") == f"file '{(tmp_path / 'a.mp4').resolve().as_posix()}'\n"
