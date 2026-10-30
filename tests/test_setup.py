"""`studio setup`: the prerequisite report, the .env writer and the interactive flow."""

import io
import stat
import sys
import urllib.error

import pytest

from studio import cli, common, setup


class Tty(io.StringIO):
    def isatty(self):
        return True


@pytest.fixture
def ws(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "LICENSED_FONTS", tmp_path / "fonts")
    monkeypatch.setattr(setup.shutil, "which", lambda t: f"/usr/bin/{t}")
    for k in ("ELEVENLABS_API_KEY", "STUDIO_ARCHIVE"):
        monkeypatch.delenv(k, raising=False)
    return tmp_path


def run_setup(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["studio", "setup", *argv])
    cli.main()


def answers(monkeypatch, *lines, key=""):
    it = iter(lines)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))
    monkeypatch.setattr(setup.getpass, "getpass", lambda prompt="": key)
    monkeypatch.setattr(sys, "stdin", Tty())


def test_write_env_keeps_comments_and_other_keys(ws):
    (ws / ".env").write_text("# mine\nOTHER=1\nexport ELEVENLABS_API_KEY=old\n")
    path = common.write_env({"ELEVENLABS_API_KEY": "new", "STUDIO_ARCHIVE": "gd:x"})
    assert path.read_text() == "# mine\nOTHER=1\nELEVENLABS_API_KEY=new\nSTUDIO_ARCHIVE=gd:x\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_env_creates_owner_only_file(ws):
    path = common.write_env({"A": "b"})
    assert path.read_text() == "A=b\n" and stat.S_IMODE(path.stat().st_mode) == 0o600


def test_check_reports_ok_and_exits_zero(ws, monkeypatch, capsys):
    with pytest.raises(SystemExit) as e:
        run_setup(monkeypatch, "--check")
    out = capsys.readouterr().out
    assert e.value.code == 0
    assert "ok       ffmpeg" in out and "optional dinpro-fonts" in out
    assert "summary: all required tools found; .env not created" in out


def test_check_exits_one_when_a_required_tool_is_missing(ws, monkeypatch, capsys):
    monkeypatch.setattr(setup.shutil, "which", lambda t: None if t == "ffmpeg" else "/x")
    monkeypatch.setattr(common.shutil, "which", lambda t: None if t == "ffmpeg" else "/x")
    with pytest.raises(SystemExit) as e:
        run_setup(monkeypatch, "--check")
    out = capsys.readouterr().out
    assert e.value.code == 1
    assert "missing  ffmpeg" in out and "missing required: ffmpeg" in out


def test_non_tty_falls_back_to_check(ws, monkeypatch, capsys):
    with pytest.raises(SystemExit) as e:
        run_setup(monkeypatch)  # pytest's stdin is not a TTY
    assert e.value.code == 0
    assert "summary:" in capsys.readouterr().out


def test_interactive_saves_key_and_archive_without_echoing_the_key(ws, monkeypatch, capsys):
    monkeypatch.setattr(setup, "verify_elevenlabs", lambda k: (True, "accepted"))
    monkeypatch.setattr(setup, "check_remote", lambda r: None)
    answers(monkeypatch, "y", "y", "gdrive:masters/", key="sk-secret-key-1234")
    run_setup(monkeypatch, "--no-download")
    out = capsys.readouterr().out
    assert common.ROOT.joinpath(".env").read_text() == "ELEVENLABS_API_KEY=sk-secret-key-1234\nSTUDIO_ARCHIVE=gdrive:masters\n"
    assert "sk-secret-key-1234" not in out and "studio sync my-video" in out


def test_interactive_skip_everything(ws, monkeypatch, capsys):
    answers(monkeypatch, "", "", "")
    run_setup(monkeypatch)
    assert not (ws / ".env").exists()
    assert "Nothing to save" in capsys.readouterr().out


def test_existing_key_is_kept_on_enter(ws, monkeypatch):
    (ws / ".env").write_text("ELEVENLABS_API_KEY=keepme-1234567\n")
    answers(monkeypatch, "", "", key="")
    run_setup(monkeypatch, "--no-download")
    assert (ws / ".env").read_text() == "ELEVENLABS_API_KEY=keepme-1234567\n"


def test_rejected_key_is_dropped_unless_confirmed(ws, monkeypatch):
    monkeypatch.setattr(setup, "verify_elevenlabs", lambda k: (False, "rejected (401): check the key"))
    answers(monkeypatch, "y", "n", "n", key="bad-key-0123456")
    run_setup(monkeypatch, "--no-download")
    assert not (ws / ".env").exists()


def test_refuses_to_write_env_when_not_gitignored(ws, monkeypatch):
    (ws / ".git").mkdir()
    monkeypatch.setattr(setup, "verify_elevenlabs", lambda k: (True, "ok"))
    answers(monkeypatch, "y", "n", key="sk-abcdefghijk")
    with pytest.raises(SystemExit):
        run_setup(monkeypatch, "--no-download")
    assert not (ws / ".env").exists()


def test_mask():
    assert setup.mask("sk-abcdefghijkl") == "sk-…ijkl" and setup.mask("short") == "…"


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def http_error(code, body=b""):
    return urllib.error.HTTPError("u", code, "m", {}, io.BytesIO(body))


@pytest.mark.parametrize("raised,expected", [
    (None, True),
    (http_error(401, b'{"detail":{"status":"missing_permissions"}}'), True),
    (http_error(401, b'{"detail":"invalid_api_key"}'), False),
    (http_error(500), None),
    (urllib.error.URLError("dns"), None),
])
def test_verify_elevenlabs(monkeypatch, raised, expected):
    def fake_open(req, timeout):
        if raised:
            raise raised
        return FakeResponse()
    monkeypatch.setattr(setup.urllib.request, "urlopen", fake_open)
    assert setup.verify_elevenlabs("k")[0] is expected


def test_check_remote(monkeypatch):
    class Done:
        stdout = "gdrive:\nb2:\n"
    monkeypatch.setattr(setup.shutil, "which", lambda t: "/usr/bin/rclone")
    monkeypatch.setattr(setup.subprocess, "run", lambda *a, **k: Done())
    assert setup.check_remote("gdrive:masters") is None
    assert "no remote called 's3:'" in setup.check_remote("s3:bucket")
    monkeypatch.setattr(setup.shutil, "which", lambda t: None)
    assert setup.check_remote("s3:bucket") is None
