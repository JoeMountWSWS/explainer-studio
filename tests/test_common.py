import os

import pytest

from studio import common


def test_sha_is_stable_and_type_aware(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"abc")
    assert common.sha("x", 1) == common.sha("x", 1)
    assert common.sha({"b": 1, "a": 2}) == common.sha({"a": 2, "b": 1})
    assert common.sha(f) == common.sha(b"abc")  # a Path hashes its contents
    assert common.sha("ab", "c") != common.sha("a", "bc")  # parts are separated


def test_tree_hash(tmp_path):
    assert common.tree_hash(tmp_path / "missing") == ""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f.txt").write_text("one")
    first = common.tree_hash(tmp_path)
    assert first == common.tree_hash(tmp_path)
    (tmp_path / "sub" / "f.txt").write_text("three")
    assert common.tree_hash(tmp_path) != first


def test_load_env_parses_without_overriding(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# comment\n\nexport A_KEY='quoted'\nB_KEY = \"double\"\nC_KEY=plain\nnot a pair\nKEEP=from-file\n")
    monkeypatch.setattr(common, "ROOT", tmp_path)
    for k in ("A_KEY", "B_KEY", "C_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("KEEP", "from-env")
    common.load_env()
    assert (os.environ["A_KEY"], os.environ["B_KEY"], os.environ["C_KEY"]) == ("quoted", "double", "plain")
    assert os.environ["KEEP"] == "from-env"


def test_load_env_without_file(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "ROOT", tmp_path)
    common.load_env()  # no .env: nothing to do


def test_episode_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(common, "EPISODES", tmp_path)
    (tmp_path / "ok").mkdir()
    (tmp_path / "ok" / "script.md").write_text("")
    assert common.episode_dir("ok") == tmp_path / "ok"
    with pytest.raises(SystemExit):
        common.episode_dir("missing")
    assert "no episode 'missing'" in capsys.readouterr().err


def test_require_media_flags_lfs_pointers(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(common, "ROOT", tmp_path)
    ep = tmp_path / "episodes" / "ep"
    media = ep / "assets" / "media"
    media.mkdir(parents=True)
    (media / "real.png").write_bytes(b"\x89PNG" + b"\0" * 2000)
    common.require_media(ep)  # real files pass
    for i in range(7):
        (media / f"p{i}.jpg").write_bytes(common.LFS_POINTER + b"v1\noid sha256:abc\nsize 12\n")
    with pytest.raises(SystemExit):
        common.require_media(ep)
    err = capsys.readouterr().err
    assert "7 media file(s) are Git LFS pointers" in err
    assert "and 2 more" in err
    assert 'git lfs pull --include "episodes/ep/**' in err


def test_run_returns_stdout_and_dies_on_failure(capsys):
    assert common.run(["python3", "-c", "print('hi')"]) == "hi\n"
    with pytest.raises(SystemExit):
        common.run(["python3", "-c", "import sys; print('boom', file=sys.stderr); sys.exit(3)"])
    assert "command failed (3)" in capsys.readouterr().err


def test_hf_pins_the_version():
    assert common.hf("check") == ["npx", "--yes", f"hyperframes@{common.HF_VERSION}", "check"]
    assert "HYPERFRAMES_PYTHON" in common.hf_env()


def test_require_tools(monkeypatch, capsys):
    monkeypatch.setattr(common.shutil, "which", lambda tool: None if tool == "npx" else f"/usr/bin/{tool}")
    with pytest.raises(SystemExit):
        common.require_tools()
    assert "'npx' not found" in capsys.readouterr().err
