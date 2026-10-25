"""Install the `make-explainer-video` agent skill into a workspace or the user's skills folder."""

from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

from .common import PKG_DATA, ROOT, die, info

NAME = "make-explainer-video"

# Where each file of the skill comes from, relative to PKG_DATA (the wheel's studio/data/, or the
# repository root in a checkout). The house-style spec and starter script sit at the same path in both.
_WHEEL = {"SKILL.md": f"skills/{NAME}/SKILL.md", "references/agents.md": f"skills/{NAME}/references/agents.md"}
_CHECKOUT = {"SKILL.md": f".claude/skills/{NAME}/SKILL.md", "references/agents.md": "AGENTS.md"}
_SHARED = {"references/frame.md": "brand/frame.md", "references/script-template.md": "templates/script.md"}


def sources() -> dict[str, Path]:
    own = _WHEEL if (PKG_DATA / _WHEEL["SKILL.md"]).is_file() else _CHECKOUT
    paths = {rel: PKG_DATA / src for rel, src in {**own, **_SHARED}.items()}
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        die(f"skill files missing from this install: {', '.join(missing)}")
    return paths


def target_dir(user: bool, dest: str | None) -> Path:
    if dest:
        return Path(dest).expanduser().resolve() / NAME
    return (Path.home() if user else ROOT) / ".claude" / "skills" / NAME


def install(user: bool = False, dest: str | None = None, force: bool = False) -> None:
    src = sources()
    target = target_dir(user, dest)
    if (target / "SKILL.md").exists() and (target / "SKILL.md").samefile(src["SKILL.md"]):
        info(f"{target} is this repository's own copy: the skill is already available here")
        return
    stale = [rel for rel, s in src.items() if (target / rel).exists() and not filecmp.cmp(s, target / rel, shallow=False)]
    if stale and not force:
        die(f"{target} already has a different copy ({', '.join(stale)}). Re-run with --force to replace it")
    for rel, s in src.items():
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, out)
    info(f"installed the {NAME} skill to {target}")
    info(f"start Claude Code in {ROOT if not user else 'your workspace'} and ask for a video, or run /{NAME}")
