"""The commands that need no TTS, browser or HyperFrames: new, status, install-skill, music (cached), archive."""

import json
import sys

import pytest

from conftest import vo_record
from studio import build, cli, music, skill


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """An empty studio workspace, using this checkout's brand/ and templates/."""
    episodes = tmp_path / "episodes"
    episodes.mkdir()
    monkeypatch.setattr(cli, "EPISODES", episodes)
    monkeypatch.setattr("studio.common.EPISODES", episodes)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(music, "ROOT", tmp_path)
    monkeypatch.setattr(build, "LICENSED_FONTS", tmp_path / "brand" / "fonts-licensed")
    return tmp_path


def studio(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["studio", *argv])
    cli.main()


def test_new_then_status(workspace, monkeypatch, capsys):
    studio(monkeypatch, "new", "paris-commune", "The Paris Commune")
    ep = workspace / "episodes" / "paris-commune"
    assert "title: The Paris Commune" in (ep / "script.md").read_text(encoding="utf-8")
    for d in ("scenes", "audio/recorded", "assets/media", "assets/brand"):
        assert (ep / d).is_dir()
    assert "created episodes/paris-commune/" in capsys.readouterr().out

    studio(monkeypatch, "status", "paris-commune")
    out = capsys.readouterr().out
    assert "The Paris Commune" in out and "not yet synced" in out and "(no scene file yet)" in out


def test_new_rejects_bad_or_existing_slug(workspace, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        studio(monkeypatch, "new", "Bad_Slug")
    assert "slug must be lowercase" in capsys.readouterr().err
    studio(monkeypatch, "new", "ok")
    with pytest.raises(SystemExit):
        studio(monkeypatch, "new", "ok")
    assert "already exists" in capsys.readouterr().err


def test_status_after_sync_shows_actual_length(workspace, monkeypatch, capsys):
    from studio.script import parse

    studio(monkeypatch, "new", "ep")
    ep = workspace / "episodes" / "ep"
    script = parse(ep / "script.md")
    vo = {sc.id: vo_record([(w, i * 0.4, i * 0.4 + 0.4) for i, w in enumerate(sc.words)]) for sc in script.scenes}
    (ep / "timing.json").write_text(json.dumps(build.compute_timing(script, vo)), encoding="utf-8")
    capsys.readouterr()
    studio(monkeypatch, "status", "ep")
    assert "actual" in capsys.readouterr().out.splitlines()[-1]


def test_sync_narrates_and_builds(workspace, monkeypatch, capsys, fake_tts):
    studio(monkeypatch, "new", "ep")
    studio(monkeypatch, "sync", "ep")
    ep = workspace / "episodes" / "ep"
    timing = json.loads((ep / "timing.json").read_text(encoding="utf-8"))
    assert fake_tts.calls and timing["duration"] > 0
    for s in timing["scenes"]:
        assert (ep / "scenes" / f"{s['id']}.html").exists()
    assert "scenes," in capsys.readouterr().out
    calls = len(fake_tts.calls)
    studio(monkeypatch, "sync", "ep", "--scene", timing["scenes"][0]["id"])
    assert len(fake_tts.calls) == calls  # nothing changed, so nothing is re-synthesised


def test_music_uses_cached_bed(workspace, monkeypatch, capsys):
    studio(monkeypatch, "new", "ep")
    ep = workspace / "episodes" / "ep"
    with pytest.raises(SystemExit):  # no timing.json yet
        studio(monkeypatch, "music", "ep", "--prompt", "calm piano")
    assert "studio sync ep" in capsys.readouterr().err

    (ep / "timing.json").write_text(json.dumps({"duration": 30.2}), encoding="utf-8")
    length = 33  # ceil(30.2) + TAIL_S
    cached = ep / "audio" / "music" / f"{music.sha('calm piano', length, music.MODEL, 0)[:20]}.mp3"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"mp3")
    monkeypatch.setattr(music, "elevenlabs_post", lambda *a, **k: pytest.fail("cache miss"))
    monkeypatch.setattr(music, "ffprobe_duration", lambda p: 33.0)
    studio(monkeypatch, "music", "ep", "--prompt", "calm piano")
    assert (ep / "audio" / "music" / "bed.mp3").read_bytes() == b"mp3"
    assert "music: episodes/ep/audio/music/bed.mp3" in capsys.readouterr().out


@pytest.mark.parametrize("args, message", [([], "give --prompt"), (["--prompt", "x", "--variants", "5"], "1-4")])
def test_music_argument_errors(workspace, monkeypatch, capsys, args, message):
    studio(monkeypatch, "new", "ep")
    with pytest.raises(SystemExit):
        studio(monkeypatch, "music", "ep", *args)
    assert message in capsys.readouterr().err


def test_music_generate_clamps_length_and_calls_api_once(tmp_path, monkeypatch):
    calls, commands = [], []
    monkeypatch.setattr(music, "ROOT", tmp_path)
    monkeypatch.setattr(music, "elevenlabs_key", lambda: "k")
    monkeypatch.setattr(music, "elevenlabs_post", lambda url, key, body, timeout: calls.append(body) or b"raw")

    def fake_run(cmd):
        commands.append(cmd)
        open(cmd[-1], "wb").write(b"encoded")

    monkeypatch.setattr(music, "run", fake_run)
    path = music.generate(tmp_path, "drums", 9999, "music_v2")
    assert calls == [{"prompt": "drums", "music_length_ms": music.MAX_S * 1000, "model_id": "music_v2",
                      "force_instrumental": True}]
    assert path.read_bytes() == b"encoded" and not list(path.parent.glob(".*.raw.mp3"))
    assert music.generate(tmp_path, "drums", 9999, "music_v2") == path and len(calls) == 1


def test_install_skill(tmp_path, monkeypatch, capsys):
    studio(monkeypatch, "install-skill", "--dir", str(tmp_path))
    target = tmp_path / skill.NAME
    for rel in ("SKILL.md", "references/agents.md", "references/frame.md", "references/script-template.md"):
        assert (target / rel).is_file()
    assert "installed the" in capsys.readouterr().out

    (target / "SKILL.md").write_text("local edits", encoding="utf-8")
    with pytest.raises(SystemExit):
        studio(monkeypatch, "install-skill", "--dir", str(tmp_path))
    assert "--force" in capsys.readouterr().err
    studio(monkeypatch, "install-skill", "--dir", str(tmp_path), "--force")
    assert (target / "SKILL.md").read_text(encoding="utf-8") != "local edits"


def test_install_skill_into_its_own_checkout_is_a_no_op(monkeypatch, capsys):
    monkeypatch.setattr(skill, "ROOT", skill.PKG_DATA)
    skill.install()
    assert "already available here" in capsys.readouterr().out


@pytest.fixture
def archive_ws(workspace, monkeypatch):
    """A workspace with episode `ep`, an out/ folder, no .env and a fake rclone that records its argv."""
    studio(monkeypatch, "new", "ep")
    out = workspace / "out"
    out.mkdir()
    monkeypatch.setattr(cli, "OUT", out)
    monkeypatch.setattr(cli, "load_env", lambda: None)
    monkeypatch.delenv("STUDIO_ARCHIVE", raising=False)
    monkeypatch.setattr(cli.shutil, "which", lambda tool: f"/usr/bin/{tool}")
    calls = []

    def fake_run(cmd, check):
        calls.append((cmd, open(cmd[cmd.index("--files-from") + 1], encoding="utf-8").read().split()))
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    return out, calls


def test_archive_copies_deliverables(archive_ws, monkeypatch, capsys):
    out, calls = archive_ws
    for name in ("ep.mp4", "ep.srt", "ep-thumbnail.jpg", "ep-draft.mp4"):
        (out / name).write_text("x", encoding="utf-8")
    monkeypatch.setenv("STUDIO_ARCHIVE", "gdrive:masters/")
    studio(monkeypatch, "archive", "ep")
    [(cmd, files)] = calls
    assert cmd[0] == "rclone" and cmd[-2:] == [str(out), "gdrive:masters/ep"]
    assert files == ["ep.mp4", "ep.srt", "ep-thumbnail.jpg"]  # no draft, no missing chapters file
    assert "archive -> gdrive:masters/ep/" in capsys.readouterr().out


def test_archive_remote_flag_overrides_env(archive_ws, monkeypatch):
    out, calls = archive_ws
    (out / "ep.mp4").write_text("x", encoding="utf-8")
    monkeypatch.setenv("STUDIO_ARCHIVE", "gdrive:masters")
    studio(monkeypatch, "archive", "ep", "--remote", "b2:other")
    assert calls[0][0][-1] == "b2:other/ep"


@pytest.mark.parametrize("setup, error", [
    ("no-remote", "set STUDIO_ARCHIVE"),
    ("no-rclone", "'rclone' not found"),
    ("no-render", "no final render at out/ep.mp4"),
])
def test_archive_errors(archive_ws, monkeypatch, capsys, setup, error):
    out, calls = archive_ws
    if setup != "no-remote":
        monkeypatch.setenv("STUDIO_ARCHIVE", "gdrive:masters")
    if setup == "no-rclone":
        monkeypatch.setattr(cli.shutil, "which", lambda tool: None)
    if setup != "no-render":
        (out / "ep.mp4").write_text("x", encoding="utf-8")
    (out / "ep.srt").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        studio(monkeypatch, "archive", "ep")
    assert error in capsys.readouterr().err and not calls


def test_find_browser_prefers_path(monkeypatch):
    monkeypatch.setattr(cli.shutil, "which", lambda tool: "/usr/bin/msedge" if tool == "msedge" else None)
    assert cli.find_browser() == "/usr/bin/msedge"


def test_find_browser_falls_back_to_hyperframes_chrome(monkeypatch, tmp_path):
    # Windows: Chrome and Edge are installed but rarely on PATH, so use the browser HyperFrames renders with.
    shell = tmp_path / "chrome-headless-shell.exe"
    shell.write_bytes(b"")
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd[-1])
        return f"{shell}\n" if cmd[-1] == "path" else "Ready to render."
    monkeypatch.setattr(cli.shutil, "which", lambda tool: None)
    monkeypatch.setattr(cli, "run", fake_run)
    assert cli.find_browser() == str(shell)
    assert calls == ["ensure", "path"]


def test_find_browser_gives_up(monkeypatch, capsys):
    monkeypatch.setattr(cli.shutil, "which", lambda tool: None)
    monkeypatch.setattr(cli, "run", lambda cmd, **kw: "")
    with pytest.raises(SystemExit):
        cli.find_browser()
    assert "no browser found" in capsys.readouterr().err
