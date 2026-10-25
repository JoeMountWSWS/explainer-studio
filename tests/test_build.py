import json

import pytest

from conftest import DEMO, vo_record
from studio import build
from studio.script import parse

SCRIPT = """
    ---
    title: Test & Episode
    fps: 30
    ---
    ## hook: Hook
    > template: title
    One {two} two three.

    ## card: Card
    > duration: 2
"""


def test_frames():
    assert build.frames(1.0, 30) == 30
    assert build.frames(1.0166, 30) == 30
    assert build.frames(1.02, 30) == 31


def test_compute_timing_lays_scenes_on_whole_frames(write_script):
    script = write_script(SCRIPT)
    vo = {
        "hook": vo_record([("One", 0.0, 0.3), ("two", 0.3, 0.6), ("three.", 0.6, 1.01)], cues={"two": 0.3}),
        "card": vo_record([]),
    }
    timing = build.compute_timing(script, vo)
    assert (timing["width"], timing["height"], timing["fps"], timing["format"]) == (1920, 1080, 30, "landscape")
    hook, card = timing["scenes"]
    # pad_in 0.6 + 1.01s narration + pad_out 0.9 = 2.51s -> 75 frames
    assert hook == {
        "id": "hook", "title": "Hook", "template": "title", "start": 0.0, "duration": 2.5,
        "voStart": 0.6, "voEnd": 1.61, "cues": {"two": 0.9}, "paragraphs": [0.6],
    }
    assert card["start"] == 2.5 and card["duration"] == 2.0 and card["voStart"] == 0.0
    assert timing["duration"] == 4.5


def test_compute_timing_reel_and_bad_format(write_script):
    script = write_script("---\nformat: reel\n---\n## a: A\nHi.\n")
    vo = {"a": vo_record([("Hi.", 0.0, 0.5)])}
    assert (build.compute_timing(script, vo)["width"], build.compute_timing(script, vo)["height"]) == (1080, 1920)
    script.meta["format"] = "square"
    with pytest.raises(SystemExit):
        build.compute_timing(script, vo)


def test_build_writes_a_complete_project(write_script, tmp_path, monkeypatch):
    monkeypatch.setattr(build, "LICENSED_FONTS", tmp_path / "no-fonts")
    script = write_script(SCRIPT)
    ep = tmp_path / "ep"
    vo = {"hook": vo_record([("One", 0.0, 0.3), ("two", 0.3, 0.6), ("three.", 0.6, 1.0)], cues={"two": 0.3}),
          "card": vo_record([])}
    timing = build.build(ep, script, vo)

    assert json.loads((ep / "timing.json").read_text()) == timing
    assert json.loads((ep / "package.json").read_text())["scripts"]["check"].endswith(f"@{build.HF_VERSION} check")
    assert (ep / "hyperframes.json").exists()
    for f in ("brand.css", "gsap.min.js"):
        assert (ep / "assets" / "brand" / f).exists()
    assert (ep / "frame.md").exists()

    hook = (ep / "scenes" / "hook.html").read_text()
    assert "__ID__" not in hook and "hook" in hook
    assert '"cues": {"two": 0.9}' in hook  # timing injected into the stub

    index = (ep / "index.html").read_text()
    assert "<title>Test &amp; Episode</title>" in index
    assert 'data-composition-src="scenes/card.html"' in index
    assert 'id="vo-hook"' in index and 'id="vo-card"' not in index  # silent scenes get no audio
    assert 'data-resolution="landscape"' in index

    # A second build keeps the edited scene file and only refreshes its timing block.
    (ep / "scenes" / "hook.html").write_text(hook.replace("<div", "<div data-edited", 1))
    vo["hook"]["cues"] = {"two": 0.5}
    build.build(ep, script, vo)
    hook = (ep / "scenes" / "hook.html").read_text()
    assert "data-edited" in hook and '"cues": {"two": 1.1}' in hook


def test_stub_scene_unknown_template(write_script, tmp_path, capsys):
    script = write_script("## a: A\n> template: nope\nHi.\n")
    with pytest.raises(SystemExit):
        build.stub_scene(tmp_path, script, {"id": "a", "title": "A", "template": "nope"}, (1920, 1080))
    assert "unknown template 'nope'" in capsys.readouterr().err


def test_inject_timing_warns_without_block(tmp_path, capsys):
    (tmp_path / "scenes").mkdir()
    (tmp_path / "scenes" / "a.html").write_text("<div></div>")
    scene = {"id": "a", "duration": 1, "voStart": 0, "voEnd": 1, "cues": {}, "paragraphs": []}
    build.inject_timing(tmp_path, scene)
    assert "no /* <studio:timing> */ block" in capsys.readouterr().out


def test_write_index_copies_music_bed(write_script, tmp_path, monkeypatch):
    script = write_script("---\nmusic: bed.mp3\nmusic_db: -20\n---\n## a: A\nHi.\n")
    ep = tmp_path / "ep"
    (ep / "bed.mp3").write_bytes(b"ID3")
    (ep / "assets").mkdir()
    timing = build.compute_timing(script, {"a": vo_record([("Hi.", 0.0, 0.5)])})
    build.write_index(ep, script, timing)
    assert (ep / "assets" / "music.mp3").read_bytes() == b"ID3"
    assert 'src="assets/music.mp3"' in (ep / "index.html").read_text()
    assert 'data-volume="0.1"' in (ep / "index.html").read_text()

    script.meta["music"] = "missing.mp3"
    monkeypatch.setattr(build, "ROOT", tmp_path)
    with pytest.raises(SystemExit):
        build.write_index(ep, script, timing)


def test_sync_brand_adds_licensed_font_faces(tmp_path, monkeypatch):
    fonts = tmp_path / "fonts-licensed"
    fonts.mkdir()
    for name in ("DINPro-Bold.ttf", "DINPro-Light.ttf", "DINPro-Unknown.ttf"):
        (fonts / name).write_bytes(b"ttf")
    monkeypatch.setattr(build, "LICENSED_FONTS", fonts)
    ep = tmp_path / "ep"
    build.sync_brand(ep)
    css = (ep / "assets" / "brand" / "brand.css").read_text()
    assert 'url("fonts/DINPro-Bold.ttf") format("truetype"); font-weight: 700' in css
    assert "font-weight: 300" in css and "DINPro-Unknown" not in css
    assert (ep / "assets" / "brand" / "fonts" / "DINPro-Bold.ttf").exists()


def test_render_shell_hosts_one_scene_at_zero(tmp_path):
    timing = {"width": 1080, "height": 1920}
    scene = {"id": "hook", "duration": 3.0}
    shell = build.render_shell(tmp_path, scene, timing)
    text = shell.read_text()
    assert shell.name == "_render_hook.html"
    assert 'data-start="0.0000"' in text and 'data-resolution="portrait"' in text


def test_demo_episode_timing_is_reproducible():
    """The committed demo timing.json must follow from its script and narration records."""
    script = parse(DEMO / "script.md")
    vo = {sc.id: json.loads((DEMO / "audio" / "vo" / f"{sc.id}.words.json").read_text()) for sc in script.scenes}
    assert build.compute_timing(script, vo) == json.loads((DEMO / "timing.json").read_text())
