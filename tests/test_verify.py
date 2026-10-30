"""verify: ffmpeg-backed checks on synthetic masters (a black segment, a silent gap, a too-quiet file)."""

import shutil
import subprocess
import sys
import textwrap

import pytest

from studio import cli, verify
from studio.script import parse

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")

W, H, FPS = 320, 180, 30


def make_master(path, secs=12.0, black=None, silent=None, level=-14.0, size=(W, H)):
    """A noisy-video, tone-audio mp4. black/silent are (start, end) spans; level is the tone's dB gain."""
    video = f"testsrc2=s={size[0]}x{size[1]}:r={FPS}:d={secs}"
    vf = "null"
    if black:
        vf = f"drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='between(t,{black[0]},{black[1]})'"
    af = f"volume={level}dB"
    if silent:
        af += f",volume=enable='between(t,{silent[0]},{silent[1]})':volume=0"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", video, "-f", "lavfi",
                    "-i", f"sine=f=300:r=48000:d={secs}", "-vf", vf, "-af", af, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(path)], check=True)
    return path


def timing(secs=12.0, scenes=None):
    scenes = scenes or [{"id": "a", "start": 0.0, "duration": secs, "voStart": 0.5, "voEnd": secs - 1}]
    return {"scenes": scenes, "width": W, "height": H, "fps": FPS, "duration": secs}


@pytest.fixture
def script(write_script):
    return write_script("## a: A\nHello there.\n")


@needs_ffmpeg
def test_loudness_ok_and_too_quiet(tmp_path):
    loud = tmp_path / "loud.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=300:r=48000:d=8", "-af",
                    "loudnorm=I=-14:TP=-1.5", "-ar", "48000", str(loud)], check=True)
    assert verify.check_loudness(loud, -14, -1.5).level == "ok"
    quiet = make_master(tmp_path / "quiet.mp4", secs=8, level=-40)
    found = verify.check_loudness(quiet, -14, -1.5)
    assert found.level == "error" and "LUFS" in found.message


@needs_ffmpeg
def test_black_segment_is_an_error_but_a_scene_fade_is_not(tmp_path):
    t = timing(12.0, [{"id": "a", "start": 0.0, "duration": 6.0, "voStart": 0, "voEnd": 5},
                      {"id": "b", "start": 6.0, "duration": 6.0, "voStart": 0, "voEnd": 5}])
    mid = verify.check_video(make_master(tmp_path / "mid.mp4", black=(2.0, 4.0)), t)
    assert [f.level for f in mid if f.name == "black frames"] == ["error"]
    boundary = verify.check_video(make_master(tmp_path / "edge.mp4", black=(5.7, 6.3)), t)
    assert [f.level for f in boundary if f.name == "black frames"] == ["ok"]


@needs_ffmpeg
def test_silent_gap_is_an_error_but_a_short_pause_is_not(tmp_path, script):
    t = timing()
    gap = verify.check_silence(make_master(tmp_path / "gap.mp4", silent=(3.0, 8.0)), script, t)
    assert gap.level == "error" and "0:03" in gap.message
    short = verify.check_silence(make_master(tmp_path / "short.mp4", silent=(3.0, 4.0)), script, t)
    assert short.level == "ok"


@needs_ffmpeg
def test_silence_is_allowed_in_a_scene_without_narration(tmp_path, script):
    t = timing(12.0, [{"id": "a", "start": 0.0, "duration": 4.0, "voStart": 0.5, "voEnd": 3.0},
                      {"id": "b", "start": 4.0, "duration": 6.0, "voStart": 0, "voEnd": 0},
                      {"id": "c", "start": 10.0, "duration": 2.0, "voStart": 0.5, "voEnd": 1.5}])
    assert verify.check_silence(make_master(tmp_path / "m.mp4", silent=(4.0, 10.0)), script, t).level == "ok"


@needs_ffmpeg
def test_format_checks_size_and_duration(tmp_path):
    good = verify.check_format(make_master(tmp_path / "good.mp4"), timing())
    assert [f.level for f in good] == ["ok", "ok"]
    wrong = verify.check_format(make_master(tmp_path / "wrong.mp4", size=(160, 90)), timing(9.0))
    assert [f.level for f in wrong] == ["error", "error"]


def test_speech_compares_the_transcript_with_the_script(tmp_path, monkeypatch, script):
    monkeypatch.setattr(verify, "run", lambda *a, **k: "")
    heard = lambda *words: [{"text": w, "start": 0, "end": 1} for w in words]  # noqa: E731
    monkeypatch.setattr(verify.voice, "transcribe", lambda wav: heard("Hello", "there"))
    assert verify.check_speech(tmp_path / "m.mp4", script).level == "ok"
    monkeypatch.setattr(verify.voice, "transcribe", lambda wav: heard("Hello"))
    found = verify.check_speech(tmp_path / "m.mp4", script)
    assert found.level == "error" and "not heard: there" in found.message
    monkeypatch.setattr(verify.voice, "transcribe", lambda wav: [])
    assert verify.check_speech(tmp_path / "m.mp4", script).level == "error"


def test_speech_without_narration_is_ok(tmp_path, write_script):
    silent = write_script("## a: A\n> duration: 3\n")
    assert verify.check_speech(tmp_path / "m.mp4", silent).level == "ok"


def test_silence_limit_follows_the_script(write_script):
    s = write_script("## a: A\nOne. {pause 3} Two.\n")
    assert verify.silence_limit(s, {}) == pytest.approx(3.5)


def test_subtract_removes_allowed_spans():
    assert verify._subtract(0, 10, [(2, 4), (8, 12)]) == [(0, 2), (4, 8)]
    assert verify._subtract(3, 4, [(0, 10)]) == []


@pytest.fixture
def out_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(verify, "OUT", tmp_path)
    return tmp_path


def chapter_timing(*lengths):
    t, scenes = 0.0, []
    for i, n in enumerate(lengths):
        scenes.append({"id": f"s{i}", "title": f"T{i}", "start": t, "duration": n})
        t += n
    return {"scenes": scenes, "duration": t}


def test_deliverables(out_dir):
    t = chapter_timing(20, 20, 20)
    assert [f.level for f in verify.check_deliverables("ep", t)] == ["error", "error"]
    (out_dir / "ep.srt").write_text("1\n", encoding="utf-8")
    (out_dir / "ep.chapters.txt").write_text("0:00 T0\n0:20 T1\n0:40 T2\n", encoding="utf-8")
    assert [f.level for f in verify.check_deliverables("ep", t)] == ["ok", "ok"]
    assert verify.check_deliverables("ep", chapter_timing(20, 5))[1].level == "warn"
    (out_dir / "ep.chapters.txt").write_text("0:05 T0\n", encoding="utf-8")
    assert verify.check_deliverables("ep", t)[1].message == "the first chapter must start at 0:00"
    assert verify.check_deliverables("ep", {**t, "format": "reel"})[1].level == "error"


def test_report_counts_errors(capsys):
    n = verify.report([verify.Finding("ok", "a", "fine"), verify.Finding("warn", "b", "hmm"),
                       verify.Finding("error", "c", "bad")])
    assert n == 1
    out = capsys.readouterr().out
    assert "ERROR  c" in out and "1 error(s), 1 warning(s)" in out


def test_verify_master_needs_a_render(tmp_path, script, capsys):
    with pytest.raises(SystemExit):
        verify.verify_master(tmp_path / "ep", script, timing(), tmp_path / "missing.mp4")
    assert "studio render" in capsys.readouterr().err


# ---------------------------------------------------------------- CLI

@pytest.fixture
def episode(tmp_path, monkeypatch):
    ep = tmp_path / "episodes" / "ep"
    ep.mkdir(parents=True)
    (ep / "script.md").write_text(textwrap.dedent("## a: A\nHello there.\n"), encoding="utf-8")
    (tmp_path / "out").mkdir()
    monkeypatch.setattr(cli, "EPISODES", tmp_path / "episodes")
    monkeypatch.setattr("studio.common.EPISODES", tmp_path / "episodes")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "OUT", tmp_path / "out")
    monkeypatch.setattr(cli, "require_tools", lambda: None)
    return ep


def studio(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["studio", *argv])
    cli.main()


def stub_verify(monkeypatch, *levels):
    calls = []
    monkeypatch.setattr(cli.verify, "verify_master",
                        lambda *a, **k: calls.append(k) or [verify.Finding(lv, "x", "y") for lv in levels])
    return calls


def test_verify_command_exit_status(episode, monkeypatch):
    (episode / "timing.json").write_text('{"scenes": []}', encoding="utf-8")
    calls = stub_verify(monkeypatch, "ok", "warn")
    studio(monkeypatch, "verify", "ep", "--draft", "--no-speech")  # warnings don't fail
    assert calls == [{"speech": False, "deliverables": False}]
    stub_verify(monkeypatch, "ok", "error")
    with pytest.raises(SystemExit) as exit:
        studio(monkeypatch, "verify", "ep")
    assert exit.value.code == 1


def test_verify_command_needs_timing(episode, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        studio(monkeypatch, "verify", "ep")
    assert "studio sync ep" in capsys.readouterr().err


@pytest.mark.parametrize("flags,verified", [([], True), (["--no-verify"], False)])
def test_render_verifies_unless_skipped(episode, monkeypatch, flags, verified):
    monkeypatch.setattr(cli, "_sync", lambda slug: (episode, parse(episode / "script.md"), {}))
    monkeypatch.setattr(cli.renderer, "render_episode", lambda *a, **k: episode / "master.mp4")
    calls = stub_verify(monkeypatch, "ok")
    studio(monkeypatch, "render", "ep", *flags)
    assert bool(calls) is verified


def test_render_fails_when_verification_finds_errors(episode, monkeypatch):
    monkeypatch.setattr(cli, "_sync", lambda slug: (episode, parse(episode / "script.md"), {}))
    monkeypatch.setattr(cli.renderer, "render_episode", lambda *a, **k: episode / "master.mp4")
    stub_verify(monkeypatch, "error")
    with pytest.raises(SystemExit) as exit:
        studio(monkeypatch, "render", "ep")
    assert exit.value.code == 1
