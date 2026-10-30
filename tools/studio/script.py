"""Parse an episode's script.md into scenes, narration chunks and cue markers.

Format (see templates/script.md for a worked example):

    ---
    title: The Paris Commune
    voice: bm_george
    ---

    ## hook: Seventy-two days
    > template: title
    > Any other quoted line is a note for the visuals and is never spoken.

    Narration paragraph. A {cue} marker names the moment the next word is spoken.

    Another paragraph. {pause 1.2} An explicit pause, in seconds.

A scene's heading is `## <id>: <chapter title>`. The id must start with a letter and use
only a-z, 0-9 and hyphens. Consecutive scenes with the same title become one YouTube chapter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .common import DEFAULTS, die

SCENE_RE = re.compile(r"^##\s+([A-Za-z0-9][A-Za-z0-9-]*)\s*:\s*(.+?)\s*$")
MARKER_RE = re.compile(r"\{\s*([^{}]+?)\s*\}")
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass
class Chunk:
    """A run of narration synthesised in one TTS call."""
    words: list[str]          # display words, punctuation attached, as written
    gap_after: float          # silence after this chunk, seconds


@dataclass
class Scene:
    id: str
    title: str
    template: str = "blank"
    min_duration: float = 0.0
    notes: list[str] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    cues: dict[str, int] = field(default_factory=dict)  # cue name -> index into words

    @property
    def words(self) -> list[str]:
        return [w for c in self.chunks for w in c.words]

    @property
    def text(self) -> str:
        return " ".join(self.words)


@dataclass
class Script:
    meta: dict
    scenes: list[Scene]

    def setting(self, key: str):
        return self.meta.get(key, DEFAULTS.get(key))


def _parse_paragraph(text: str, scene: Scene, gap: float) -> None:
    """Split one paragraph into chunks at {pause n} markers, recording {cue} positions."""
    words: list[str] = []
    pos = 0
    for m in MARKER_RE.finditer(text):
        words += text[pos:m.start()].split()
        pos = m.end()
        token = m.group(1)
        if token.startswith("pause"):
            try:
                seconds = float(token.split()[1]) if len(token.split()) > 1 else 1.0
            except ValueError:
                die(f"scene '{scene.id}': bad pause marker {{{token}}}")
            scene.chunks.append(Chunk(words, seconds))
            words = []
        else:
            name = token.replace(" ", "-")
            if name in scene.cues:
                die(f"scene '{scene.id}': cue {{{name}}} used twice")
            scene.cues[name] = len(scene.words) + len(words)
    words += text[pos:].split()
    scene.chunks.append(Chunk(words, gap))


def parse(path: Path) -> Script:
    raw = path.read_text(encoding="utf-8-sig")  # -sig: Windows editors may add a byte-order mark
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    meta: dict = {}
    if raw.startswith("---"):
        _, front, raw = raw.split("---", 2)
        meta = yaml.safe_load(front) or {}
    gap = float(meta.get("paragraph_gap", DEFAULTS["paragraph_gap"]))

    scenes: list[Scene] = []
    para: list[str] = []

    def flush():
        if para and scenes:
            _parse_paragraph(" ".join(para), scenes[-1], gap)
        para.clear()

    for line in raw.splitlines():
        s = line.strip()
        m = SCENE_RE.match(s)
        if m:
            flush()
            sid = m.group(1)
            if not ID_RE.match(sid):
                die(f"scene id '{sid}' must start with a lowercase letter and use only a-z, 0-9, '-'")
            if any(x.id == sid for x in scenes):
                die(f"duplicate scene id '{sid}'")
            scenes.append(Scene(sid, m.group(2)))
        elif s.startswith("#"):
            flush()  # top-level title or other headings: not narration
        elif s.startswith(">"):
            flush()
            if not scenes:
                continue
            note = s.lstrip(">").strip()
            key, _, val = note.partition(":")
            if key.strip().lower() == "template" and val.strip():
                scenes[-1].template = val.strip()
            elif key.strip().lower() == "duration" and val.strip():
                scenes[-1].min_duration = float(val.strip().rstrip("s"))
            elif note:
                scenes[-1].notes.append(note)
        elif not s:
            flush()
        else:
            para.append(s)
    flush()

    for sc in scenes:
        merged: list[Chunk] = []
        for c in sc.chunks:
            if c.words:
                merged.append(c)
            elif merged:  # a pause with no words before it extends the previous gap
                merged[-1].gap_after += c.gap_after
        sc.chunks = merged
        if not sc.chunks and not sc.min_duration:
            die(f"scene '{sc.id}' has no narration; add '> duration: <seconds>' for a silent scene")
        if sc.chunks:
            sc.chunks[-1].gap_after = 0.0
    if not scenes:
        die(f"{path}: no scenes found (headings must look like '## id: Chapter title')")
    return Script(meta, scenes)
