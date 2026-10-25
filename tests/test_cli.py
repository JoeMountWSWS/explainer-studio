"""The commands that need no TTS, browser or HyperFrames: new, status, install-skill, music (cached)."""

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
    assert "title: The Paris Commune" in (ep / "script.md").read_text()
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
    (ep / "timing.json").write_text(json.dumps(build.compute_timing(script, vo)))
    capsys.readouterr()
    studio(monkeypatch, "status", "ep")
    assert "actual" in capsys.readouterr().out.splitlines()[-1]


def test_sync_narrates_and_builds(workspace, monkeypatch, capsys, fake_tts):
    studio(monkeypatch, "new", "ep")
    studio(monkeypatch, "sync", "ep")
    ep = workspace / "episodes" / "ep"
    timing = json.loads((ep / "timing.json").read_text())
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

    (ep / "timing.json").write_text(json.dumps({"duration": 30.2}))
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

    (target / "SKILL.md").write_text("local edits")
    with pytest.raises(SystemExit):
        studio(monkeypatch, "install-skill", "--dir", str(tmp_path))
    assert "--force" in capsys.readouterr().err
    studio(monkeypatch, "install-skill", "--dir", str(tmp_path), "--force")
    assert (target / "SKILL.md").read_text() != "local edits"


def test_install_skill_into_its_own_checkout_is_a_no_op(monkeypatch, capsys):
    monkeypatch.setattr(skill, "ROOT", skill.PKG_DATA)
    skill.install()
    assert "already available here" in capsys.readouterr().out
