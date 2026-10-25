"""Shared fixtures. Tests run from the repository root, so studio.common resolves ROOT to this checkout."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
import pytest

from studio import voice
from studio.common import ROOT
from studio.script import parse

DEMO = ROOT / "episodes" / "demo-paris-commune"


class FakeTTS:
    """Stands in for Kokoro: 0.1s of tone per word at 48 kHz, recording what it is asked to say."""
    calls: list[str] = []

    def __init__(self, script):
        self.chars, self.seconds = 0, 0.0

    @staticmethod
    def cache_tag(script):
        return ("fake", script.setting("voice"))

    def synth_to(self, text, dst, prev_text="", next_text=""):
        FakeTTS.calls.append(text)
        self.chars += len(text)
        voice.sf.write(str(dst), np.full(len(text.split()) * 4800, 0.1, np.float32), voice.SAMPLE_RATE)


@pytest.fixture
def fake_tts(monkeypatch):
    """Narrate with FakeTTS and align without a transcript (words spread evenly over each chunk)."""
    FakeTTS.calls = []
    monkeypatch.setitem(voice.ENGINES, "kokoro", FakeTTS)
    monkeypatch.setattr(voice, "transcribe", lambda wav: [])
    monkeypatch.setattr(voice, "BRAND", ROOT / "no-brand")  # no studio-wide respellings
    return FakeTTS


@pytest.fixture
def write_script(tmp_path):
    """Write a dedented script.md into a fresh episode folder and parse it."""
    def _write(text: str, slug: str = "ep"):
        ep = tmp_path / slug
        ep.mkdir(parents=True, exist_ok=True)
        (ep / "script.md").write_text(textwrap.dedent(text).lstrip())
        return parse(ep / "script.md")
    return _write


def vo_record(words: list[tuple[str, float, float]], cues: dict | None = None, paragraphs=(0.0,)) -> dict:
    """A words.json-shaped narration record, as voice.voice_scene() returns."""
    return {
        "hash": "test",
        "source": "tts",
        "duration": words[-1][2] if words else 0.0,
        "words": [{"text": t, "start": a, "end": b} for t, a, b in words],
        "cues": cues or {},
        "paragraphs": list(paragraphs) if words else [],
    }


def write_vo(ep: Path, scene_id: str, rec: dict) -> None:
    vo = ep / "audio" / "vo"
    vo.mkdir(parents=True, exist_ok=True)
    (vo / f"{scene_id}.words.json").write_text(json.dumps(rec))
