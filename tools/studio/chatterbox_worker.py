"""Chatterbox TTS worker, run by voice.Chatterbox in its own uv environment (torch, numpy<2).

Not part of the studio package's imports: Chatterbox pins torch and numpy<2, which can't share
the studio venv. Usage:

    python chatterbox_worker.py turbo|standard

Then one JSON request per stdin line:
    {"text", "out", "ref" (path or null for the built-in voice), "exaggeration", "cfg_weight", "temperature", "seed"}
and one JSON reply per stdout line: {"ok": true, "sr": 24000} or {"error": "..."}.
Everything else the libraries print goes to stderr.
"""

import json
import os
import sys
import traceback

# Keep library chatter off the reply channel: replies go to a private copy of fd 1, and fd 1 itself
# (what native code and child processes write to) is pointed at stderr.
replies = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
os.dup2(2, 1)
sys.stdout = sys.stderr


def reply(obj: dict) -> None:
    replies.write(json.dumps(obj) + "\n")
    replies.flush()


def quiet(bar: type) -> type:
    """A tqdm subclass that never draws."""

    class Quiet(bar):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **{**kwargs, "disable": True})

    return Quiet


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else "turbo"
    import soundfile as sf
    import torch

    torch.set_num_threads(os.cpu_count() or 4)
    if kind == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS as Model
    elif kind == "standard":
        from chatterbox.tts import ChatterboxTTS as Model
    else:
        reply({"error": f"unknown chatterbox_model '{kind}' (choose: turbo, standard)"})
        return
    model = Model.from_pretrained(device="cpu")
    # Mute per-step progress bars during generation (left on above for the first-run download).
    # A subclass, not a partial, so class attributes (tqdm.write, isinstance) keep working.
    for mod in list(sys.modules.values()):
        bar = getattr(mod, "tqdm", None) if (getattr(mod, "__name__", "") or "").startswith("chatterbox") else None
        if isinstance(bar, type):
            mod.tqdm = quiet(bar)
    builtin, current = model.conds, None
    reply({"ok": True, "ready": kind, "sr": model.sr})

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            ref = req.get("ref")
            exaggeration = float(req.get("exaggeration", 0.5))
            if ref != current:
                # Conditioning on a clip is the slow part; do it once per voice, not per sentence.
                # Keyed on the clip alone: standard's generate() re-applies exaggeration on every call,
                # and Turbo has no emotion input (hp.emotion_adv is False), so it takes no exaggeration.
                if ref and kind == "standard":
                    model.prepare_conditionals(ref, exaggeration=exaggeration)
                elif ref:
                    model.prepare_conditionals(ref)
                else:
                    model.conds = builtin
                current = ref
            torch.manual_seed(int(req.get("seed", 0)))
            kwargs = {"temperature": float(req.get("temperature", 0.8))}
            if kind == "standard":
                kwargs.update(exaggeration=exaggeration, cfg_weight=float(req.get("cfg_weight", 0.5)))
            with torch.inference_mode():
                wav = model.generate(req["text"], **kwargs)
            sf.write(req["out"], wav.squeeze(0).cpu().numpy(), model.sr)
            reply({"ok": True, "sr": model.sr})
        except Exception as e:
            traceback.print_exc()
            reply({"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    main()
