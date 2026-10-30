"""Narration: TTS (Kokoro in-process, Chatterbox in a worker, or ElevenLabs) or a recorded take, then word timings by ASR + alignment.

Per scene this writes, inside the episode:
    audio/tts/<hash>.wav        cached TTS chunk (48 kHz mono); unchanged text is never re-synthesised
    audio/vo/<id>.wav           the scene's narration (chunks joined with their gaps)
    audio/vo/<id>.words.json    word timings for the *script* words (spelling as written)

To use a real recording for a scene, drop audio/recorded/<id>.(wav|flac|m4a|mp3) into the
episode. It replaces the TTS for that scene and is aligned to the script text the same way.

The engine is the script's `tts:` setting. ElevenLabs needs ELEVENLABS_API_KEY (environment or
the studio's .env); each chunk is sent with its neighbours as context so prosody carries across.
Chatterbox pins torch and numpy<2, so it runs in its own venv (built on first use) as a
subprocess worker (chatterbox_worker.py), cloning the voice from a reference clip.
"""

from __future__ import annotations

import atexit
import difflib
import functools
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

from .common import BRAND, CHATTERBOX_VERSION, ROOT, SAMPLE_RATE, die, hf, hf_env, info, load_env, run, sha
from .script import Scene, Script

KOKORO_DIR = Path.home() / ".cache" / "hyperframes" / "tts"
CHATTERBOX_DIR = Path.home() / ".cache" / "hyperframes" / "chatterbox" / CHATTERBOX_VERSION
RECORDED_EXT = (".wav", ".flac", ".m4a", ".mp3", ".ogg")
# Kokoro voice-id prefix -> phonemizer language (af_heart -> en-us, bm_george -> en-gb, ...)
LANGS = {"a": "en-us", "b": "en-gb", "e": "es", "f": "fr-fr", "h": "hi", "i": "it", "p": "pt-br", "j": "ja", "z": "zh"}


# ---------------------------------------------------------------- pronunciation

def load_pronunciations(script: Script) -> dict[str, str]:
    table: dict[str, str] = {}
    global_file = BRAND / "pronunciations.yaml"
    if global_file.exists():
        table.update(yaml.safe_load(global_file.read_text(encoding="utf-8")) or {})
    table.update(script.meta.get("pronounce") or {})
    return table


def respell(text: str, table: dict[str, str]) -> str:
    for word, say in sorted(table.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"(?<![\w-]){re.escape(word)}(?![\w-])", str(say), text)
    return text


# ---------------------------------------------------------------- TTS

# Gentle finishing for dry TTS: rumble cut, a little warmth and presence, soft de-ess and
# compression, and a faint short room so it sounds spoken into a space rather than generated.
VOICE_FX = ",".join([
    "highpass=f=70",
    "lowshelf=f=180:g=1.5",
    "equalizer=f=3200:t=q:w=1.2:g=1.2",
    "deesser=i=0.25:m=0.5:f=0.5",
    "acompressor=threshold=-20dB:ratio=2:attack=8:release=150:makeup=1.5",
    "aecho=1.0:1.0:11|19|29:0.05|0.035|0.02",
])
SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
CLAUSE_END = re.compile(r"(?<=[,;:—])\s+")
MIN_UTTERANCE = 40  # phonemes; Kokoro garbles very short inputs, so tiny sentences ride with the next


def parse_voice(spec: str) -> list[tuple[str, float]]:
    """'bf_emma*0.6 + bf_isabella*0.4' (or 'a + b', or just 'a') -> normalised (name, weight) pairs."""
    parts = []
    for term in spec.split("+"):
        name, _, weight = term.strip().partition("*")
        if not name.strip():
            die(f"bad voice '{spec}' (expected e.g. 'bf_emma*0.6 + bf_isabella*0.4')")
        try:
            parts.append((name.strip(), float(weight) if weight.strip() else 1.0))
        except ValueError:
            die(f"bad voice weight in '{spec}'")
    total = sum(w for _, w in parts)
    if total <= 0:
        die(f"voice weights in '{spec}' must add up to more than 0")
    return [(n, w / total) for n, w in parts]


def voice_spec(spec: str) -> str:
    """Canonical spelling of a voice blend, for cache keys and file names."""
    blend = parse_voice(spec)
    if len(blend) == 1:
        return blend[0][0]
    return " + ".join(f"{n}*{w:.3f}".rstrip("0").rstrip(".") for n, w in blend)


SPACY_MODEL = "en_core_web_sm-3.8.0"  # matches the spacy>=3.8,<3.9 pin in pyproject.toml
SPACY_MODEL_URL = f"https://github.com/explosion/spacy-models/releases/download/{SPACY_MODEL}/{SPACY_MODEL}-py3-none-any.whl"


def ensure_spacy_model() -> None:
    """Make en_core_web_sm importable for misaki, unpacking its wheel into the cache on first use.

    It can't be a dependency (PyPI rejects direct-URL requirements), and misaki's own fallback,
    `spacy download`, needs pip, which uv environments don't have.
    """
    import spacy.util

    if spacy.util.is_package("en_core_web_sm"):
        return
    dst = Path.home() / ".cache" / "hyperframes" / "spacy" / SPACY_MODEL
    if not dst.exists():
        info(f"  downloading spaCy model {SPACY_MODEL} (~13 MB, once)")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=dst.parent) as tmp:
            whl = Path(tmp) / "model.whl"
            urllib.request.urlretrieve(SPACY_MODEL_URL, whl)
            with zipfile.ZipFile(whl) as z:
                z.extractall(Path(tmp) / "pkg")
            (Path(tmp) / "pkg").rename(dst)
    sys.path.insert(0, str(dst))
    importlib.invalidate_caches()


def make_g2p(name: str, lang: str):
    """misaki (the G2P Kokoro was trained with) for English; None means kokoro-onnx's espeak."""
    if name == "espeak" or lang not in ("en-us", "en-gb"):
        return None
    if name != "misaki":
        die(f"unknown g2p '{name}' (choose: misaki, espeak)")
    try:
        ensure_spacy_model()
        from misaki import en, espeak
        british = lang == "en-gb"
        return en.G2P(trf=False, british=british, fallback=espeak.EspeakFallback(british=british))
    except Exception as e:  # missing package or spaCy model
        info(f"  warning: misaki unavailable ({e}); falling back to espeak phonemes")
        return None


def sentence_groups(phonemes: str) -> list[str]:
    """Split phonemes at sentence ends, merging short sentences forward."""
    groups: list[str] = []
    pending = ""
    for sent in SENTENCE_END.split(" ".join(phonemes.split())):
        pending = f"{pending} {sent}".strip()
        if len(pending) >= MIN_UTTERANCE:
            groups.append(pending)
            pending = ""
    if pending:
        if groups:
            groups[-1] += " " + pending
        else:
            groups.append(pending)
    return groups


class Kokoro:
    """Kokoro in-process: blended voice, misaki G2P, one utterance per sentence group."""

    def __init__(self, script: Script):
        self.speed = float(script.setting("speed"))
        self.sentence_pause = float(script.setting("sentence_pause"))
        self.clause_pause = float(script.setting("clause_pause"))
        self.fx = bool(script.setting("voice_fx"))
        self.chars, self.seconds = 0, 0.0
        model = KOKORO_DIR / "models" / "kokoro-v1.0.onnx"
        voices = KOKORO_DIR / "voices" / "voices-v1.0.bin"
        if not (model.exists() and voices.exists()):
            info("  downloading Kokoro model via the HyperFrames CLI (first run only)...")
            with tempfile.TemporaryDirectory() as tmp:
                run(hf("tts", "warm up", "-o", f"{tmp}/x.wav"), env=hf_env())
        import kokoro_onnx
        self.model = kokoro_onnx.Kokoro(str(model), str(voices))
        blend = parse_voice(str(script.setting("voice")))
        unknown = [n for n, _ in blend if n not in self.model.get_voices()]
        if unknown:
            die(f"unknown Kokoro voice {', '.join(unknown)} (choose from: {', '.join(self.model.get_voices())})")
        self.style = sum(w * self.model.get_voice_style(n) for n, w in blend).astype(np.float32)
        self.lang = LANGS.get(blend[0][0][:1], "en-us")
        self.g2p = make_g2p(str(script.setting("g2p")), self.lang)

    @staticmethod
    def cache_tag(script: Script) -> tuple:
        return ("kokoro-v1.0", voice_spec(str(script.setting("voice"))), float(script.setting("speed")),
                str(script.setting("g2p")), float(script.setting("sentence_pause")),
                float(script.setting("clause_pause")), bool(script.setting("voice_fx")) and VOICE_FX)

    def phonemize(self, text: str) -> str:
        if self.g2p:
            return self.g2p(text)[0]
        return self.model.tokenizer.phonemize(text, self.lang)

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        """Each sentence group is its own utterance (clean final intonation), joined by sentence_pause."""
        parts, rate = [], 24000
        for group in sentence_groups(self.phonemize(text)):
            samples, rate = self.model.create(group, voice=self.style, speed=self.speed, lang=self.lang,
                                              is_phonemes=True, trim=True, sentence_pause=self.sentence_pause,
                                              clause_pause=self.clause_pause)
            parts.append((np.asarray(samples, dtype=np.float32), self.sentence_pause))
        return join_parts(parts, rate), rate

    def synth_to(self, text: str, dst: Path, prev_text: str = "", next_text: str = "") -> None:
        finish(*self.synth(text), dst, self.fx)
        self.chars += len(text)


class ElevenLabs:
    """ElevenLabs text-to-speech over HTTPS (stdlib only)."""

    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"

    def __init__(self, script: Script):
        self.key = elevenlabs_key()
        _, self.voice, self.model, self.settings = self.cache_tag(script)
        self.chars, self.seconds = 0, 0.0

    @staticmethod
    def cache_tag(script: Script) -> tuple:
        settings = {**(script.setting("voice_settings") or {}), "speed": float(script.setting("speed"))}
        return ("elevenlabs", str(script.setting("voice")), str(script.setting("tts_model")), settings)

    def synth_to(self, text: str, dst: Path, prev_text: str = "", next_text: str = "") -> None:
        body = {"text": text, "model_id": self.model, "voice_settings": self.settings}
        if prev_text:
            body["previous_text"] = prev_text
        if next_text:
            body["next_text"] = next_text
        audio = elevenlabs_post(self.URL.format(voice=self.voice), self.key, body)
        raw = dst.with_name(f".{dst.stem}.raw.mp3")
        raw.write_bytes(audio)
        to_48k_mono(raw, dst)
        raw.unlink()
        self.chars += len(text)


class Chatterbox:
    """Chatterbox (Resemble AI) on the CPU, in its own venv: voice cloned from a reference clip."""

    WORKER = Path(__file__).with_name("chatterbox_worker.py")
    MAX_CHARS = 280  # Chatterbox drifts on long inputs, so sentences are grouped up to about this length

    def __init__(self, script: Script):
        self.model = chatterbox_model(script)
        ref = chatterbox_ref(script)
        self.ref = str(ref) if ref else None
        self.sentence_pause = float(script.setting("sentence_pause"))
        self.clause_pause = float(script.setting("clause_pause"))
        self.fx = bool(script.setting("voice_fx"))
        self.params = {k: script.setting(k) for k in ("exaggeration", "cfg_weight", "temperature", "seed")}
        self.chars, self.seconds = 0, 0.0
        python = self.ensure_env()
        info(f"  starting Chatterbox {self.model} on the CPU (first run downloads the model)...")
        self.proc = subprocess.Popen([str(python), "-I", str(self.WORKER), self.model],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8",
                                     bufsize=1, env={**os.environ, "PYTHONUTF8": "1"})
        atexit.register(self.close)
        self.request(None)  # wait for the model to load

    @staticmethod
    def ensure_env() -> Path:
        venv_bin = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
        python, stamp = CHATTERBOX_DIR.joinpath(*venv_bin), CHATTERBOX_DIR / ".installed"
        # resemble-perth (the watermarker) still imports pkg_resources, which setuptools 81 dropped.
        reqs = [f"chatterbox-tts=={CHATTERBOX_VERSION}", "soundfile", "setuptools<81"]
        if stamp.exists() and stamp.read_text(encoding="utf-8").split() == reqs:
            return python
        if not shutil.which("uv"):
            die("tts: chatterbox needs uv on PATH to build its environment")
        info(f"  installing chatterbox-tts {CHATTERBOX_VERSION} with CPU torch into {CHATTERBOX_DIR} (first run only)...")
        run(["uv", "venv", "--clear", "--python", "3.12", str(CHATTERBOX_DIR)])
        run(["uv", "pip", "install", "--python", str(python), "--torch-backend", "cpu", *reqs])
        stamp.write_text("\n".join(reqs), encoding="utf-8")
        return python

    @staticmethod
    def cache_tag(script: Script) -> tuple:
        model = chatterbox_model(script)
        ref = chatterbox_ref(script)
        params = [float(script.setting(k)) for k in ("temperature", "seed")]
        if model == "standard":
            params += [float(script.setting(k)) for k in ("exaggeration", "cfg_weight")]
        return ("chatterbox", model, clip_hash(ref) if ref else "default", CHATTERBOX_VERSION, *params,
                float(script.setting("sentence_pause")), float(script.setting("clause_pause")),
                bool(script.setting("voice_fx")) and VOICE_FX)

    def request(self, req: dict | None) -> dict:
        if req is not None:
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            die("Chatterbox worker exited (see the error above)")
        try:
            reply = json.loads(line)
        except json.JSONDecodeError:
            die(f"Chatterbox worker sent a non-JSON reply: {line[:200]!r}")
        if "error" in reply:
            die(f"Chatterbox: {reply['error']}")
        return reply

    def synth_to(self, text: str, dst: Path, prev_text: str = "", next_text: str = "") -> None:
        parts, rate = [], 24000
        with tempfile.TemporaryDirectory() as tmp:
            for i, (group, whole) in enumerate(text_groups(text, self.MAX_CHARS)):
                wav = Path(tmp) / f"{i}.wav"
                self.request({"text": group, "out": str(wav), "ref": self.ref, **self.params})
                samples, rate = sf.read(str(wav), dtype="float32")
                parts.append((trim_silence(samples, rate), self.sentence_pause if whole else self.clause_pause))
        finish(join_parts(parts, rate), rate, dst, self.fx)
        self.chars += len(text)

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def chatterbox_model(script: Script) -> str:
    model = str(script.setting("chatterbox_model")).lower()
    if model not in ("turbo", "standard"):
        die(f"unknown chatterbox_model '{model}' (choose: turbo, standard)")
    return model


def clip_hash(path: Path) -> str:
    """sha() of a reference clip, read once per sync rather than once per chunk."""
    st = path.stat()
    return _clip_hash(path, st.st_mtime_ns, st.st_size)


@functools.lru_cache(maxsize=16)
def _clip_hash(path: Path, mtime_ns: int, size: int) -> str:
    return sha(path)


def chatterbox_ref(script: Script) -> Path | None:
    """The reference clip named by `voice:` (relative to the studio root), or None for the built-in voice."""
    spec = str(script.meta.get("voice") or "default").strip()
    if spec == "default":
        return None
    path = Path(spec) if Path(spec).is_absolute() else ROOT / spec
    if not path.exists():
        die(f"Chatterbox voice clip not found: {path} (voice: is a 5-15s WAV, or 'default')")
    return path


def text_groups(text: str, max_chars: int) -> list[tuple[str, bool]]:
    """Split text into groups of up to max_chars: whole sentences where they fit, else a long sentence's
    clauses (then words). Each group comes with whether it ends a sentence, for the pause after it."""
    groups: list[tuple[str, bool]] = []
    for sent in SENTENCE_END.split(" ".join(text.split())):
        if len(sent) > max_chars:
            pieces = pack(CLAUSE_END.split(sent), max_chars)
            pieces = [w for p in pieces for w in (pack(p.split(), max_chars) if len(p) > max_chars else [p])]
            groups += [(p, False) for p in pieces[:-1]] + [(pieces[-1], True)]
        elif groups and groups[-1][1] and len(groups[-1][0]) + 1 + len(sent) <= max_chars:
            groups[-1] = (groups[-1][0] + " " + sent, True)
        else:
            groups.append((sent, True))
    return groups


def pack(pieces: list[str], max_chars: int) -> list[str]:
    """Join consecutive pieces with spaces into runs of up to max_chars."""
    runs: list[str] = []
    for piece in pieces:
        if runs and len(runs[-1]) + 1 + len(piece) <= max_chars:
            runs[-1] += " " + piece
        else:
            runs.append(piece)
    return runs


def join_parts(parts: list[tuple[np.ndarray, float]], rate: int) -> np.ndarray:
    """Concatenate (samples, pause after) parts with that much silence between them."""
    out = []
    for i, (samples, pause) in enumerate(parts):
        out.append(samples)
        if i < len(parts) - 1:
            out.append(np.zeros(int(pause * rate), dtype=np.float32))
    return np.concatenate(out)


def finish(samples: np.ndarray, rate: int, dst: Path, fx: bool) -> None:
    """The shared voice chain: resample to 48 kHz mono, with VOICE_FX if enabled."""
    raw = dst.with_name(f".{dst.stem}.raw.wav")
    sf.write(str(raw), samples, rate)
    to_48k_mono(raw, dst, VOICE_FX if fx else "")
    raw.unlink()


def trim_silence(samples: np.ndarray, rate: int, floor_db: float = -45, margin: float = 0.03) -> np.ndarray:
    """Drop leading and trailing near-silence, keeping a short margin."""
    loud = np.flatnonzero(np.abs(samples) > 10 ** (floor_db / 20))
    if not len(loud):
        return samples
    pad = int(margin * rate)
    return samples[max(0, loud[0] - pad):loud[-1] + pad]


def elevenlabs_key() -> str:
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        die("ElevenLabs needs ELEVENLABS_API_KEY (put it in .env at the studio root)")
    return key


def elevenlabs_post(url: str, key: str, body: dict, timeout: int = 120) -> bytes:
    """POST JSON to ElevenLabs and return the audio bytes, retrying rate limits, 5xx and network errors."""
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            die(f"ElevenLabs {e.code}: {_api_error(e)}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            die(f"ElevenLabs unreachable: {e.reason}")


def _api_error(e: urllib.error.HTTPError) -> str:
    try:
        detail = json.loads(e.read().decode()).get("detail")
    except Exception:
        return e.reason
    if isinstance(detail, dict):
        return detail.get("message") or detail.get("status") or str(detail)
    return str(detail)


ENGINES = {"kokoro": Kokoro, "chatterbox": Chatterbox, "elevenlabs": ElevenLabs}


def engine_class(script: Script):
    name = str(script.setting("tts")).lower()
    if name not in ENGINES:
        die(f"unknown tts engine '{name}' (choose: {', '.join(ENGINES)})")
    return ENGINES[name]


@functools.cache
def resampler() -> str:
    """soxr when this ffmpeg has it; some builds (gyan.dev "essentials" on Windows) don't."""
    return ":resampler=soxr" if "--enable-libsoxr" in run(["ffmpeg", "-hide_banner", "-buildconf"]) else ""


def to_48k_mono(src: Path, dst: Path, fx: str = "") -> None:
    chain = f"aresample={SAMPLE_RATE}{resampler()}" + (f",{fx}" if fx else "")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-af", chain, "-c:a", "pcm_s16le", str(dst)])


def read_mono(path: Path) -> np.ndarray:
    data, rate = sf.read(str(path), dtype="float32", always_2d=True)
    if rate != SAMPLE_RATE:
        die(f"{path} is {rate} Hz; expected {SAMPLE_RATE}")
    return data[:, 0]


def find_recording(ep: Path, scene_id: str) -> Path | None:
    for ext in RECORDED_EXT:
        p = ep / "audio" / "recorded" / f"{scene_id}{ext}"
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------- alignment

def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align(script_words: list[str], asr: list[dict], chunk_spans: list[tuple[int, int, float, float]]) -> list[dict]:
    """Give every script word a start/end time.

    Words that match the transcript take its timings. The rest (respelled names, numbers
    read out, ASR slips) are interpolated between their matched neighbours, bounded by the
    known start/end of the TTS chunk they belong to.
    """
    a = [_norm(w) for w in script_words]
    b = [_norm(w["text"]) for w in asr]
    times: list[tuple[float, float] | None] = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            w = asr[blk.b + k]
            times[blk.a + k] = (float(w["start"]), float(w["end"]))

    for lo, hi, c_start, c_end in chunk_spans:
        i = lo
        while i < hi:
            if times[i] is not None:
                i += 1
                continue
            j = i
            while j < hi and times[j] is None:
                j += 1
            left = times[i - 1][1] if i > lo and times[i - 1] else c_start
            right = times[j][0] if j < hi and times[j] else c_end
            right = max(right, left)
            weights = [max(len(script_words[k]), 1) for k in range(i, j)]
            total, acc = sum(weights), left
            for k, wgt in zip(range(i, j), weights):
                step = (right - left) * wgt / total
                times[k] = (acc, acc + step)
                acc += step
            i = j
    return [{"text": w, "start": round(t[0], 3), "end": round(t[1], 3)} for w, t in zip(script_words, times)]


def transcribe(wav: Path) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        run(hf("transcribe", str(wav), "-d", tmp, "--language", "en", "--json"), env=hf_env())
        return json.loads((Path(tmp) / "transcript.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- per-scene

def voice_scene(ep: Path, script: Script, scene: Scene, tts, table: dict,
                context: list[tuple[str, str]]) -> tuple[dict, object]:
    """Make audio/vo/<id>.wav and its word timings. Returns (words record, tts instance)."""
    vo_dir, tts_dir = ep / "audio" / "vo", ep / "audio" / "tts"
    vo_dir.mkdir(parents=True, exist_ok=True)
    tts_dir.mkdir(parents=True, exist_ok=True)
    out_wav, out_words = vo_dir / f"{scene.id}.wav", vo_dir / f"{scene.id}.words.json"

    if not scene.chunks:  # silent scene
        out_wav.unlink(missing_ok=True)
        rec = {"hash": "silent", "duration": 0.0, "words": [], "cues": {}, "paragraphs": []}
        out_words.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return rec, tts

    recording = find_recording(ep, scene.id)
    spans: list[tuple[int, int, float, float]] = []

    if recording:
        tmp = vo_dir / f".{scene.id}.rec.wav"
        to_48k_mono(recording, tmp)
        audio = read_mono(tmp)
        tmp.unlink()
        n = len(scene.words)
        spans = [(0, n, 0.0, len(audio) / SAMPLE_RATE)]
        source = f"recorded:{recording.name}"
    else:
        pieces, t, w0 = [], 0.0, 0
        engine = engine_class(script)
        for chunk, (prev_text, next_text) in zip(scene.chunks, context):
            say = respell(" ".join(chunk.words), table)
            # Context is left out of the key: editing a paragraph doesn't re-synthesise its neighbours.
            key = sha(say, *engine.cache_tag(script))[:20]
            cached = tts_dir / f"{key}.wav"
            if not cached.exists():
                if tts is None:
                    info(f"  loading {script.setting('tts')}...")
                    tts = engine(script)
                info(f"  tts  {scene.id}: {say[:70]}{'...' if len(say) > 70 else ''}")
                started = time.monotonic()
                tts.synth_to(say, cached, prev_text, next_text)
                tts.seconds += time.monotonic() - started
            seg = read_mono(cached)
            pieces.append(seg)
            spans.append((w0, w0 + len(chunk.words), t, t + len(seg) / SAMPLE_RATE))
            t += len(seg) / SAMPLE_RATE
            w0 += len(chunk.words)
            if chunk.gap_after > 0:
                pieces.append(np.zeros(int(round(chunk.gap_after * SAMPLE_RATE)), dtype=np.float32))
                t += chunk.gap_after
        audio = np.concatenate(pieces)
        source = "tts"

    digest = sha(audio.tobytes(), scene.words, list(scene.cues.items()))[:20]
    if out_words.exists() and out_wav.exists():
        prev = json.loads(out_words.read_text(encoding="utf-8"))
        if prev.get("hash") == digest:
            return prev, tts

    sf.write(str(out_wav), audio, SAMPLE_RATE, subtype="PCM_16")
    info(f"  align {scene.id} ({source}, {len(audio) / SAMPLE_RATE:.1f}s)")
    words = align(scene.words, transcribe(out_wav), spans)

    cues = {}
    for name, idx in scene.cues.items():
        cues[name] = words[idx]["start"] if idx < len(words) else words[-1]["end"]
    rec = {
        "hash": digest,
        "source": source,
        "duration": round(len(audio) / SAMPLE_RATE, 3),
        "words": words,
        "cues": cues,
        "paragraphs": [round(s[2], 3) for s in spans],
    }
    out_words.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec, tts


def voice_all(ep: Path, script: Script, only: set[str] | None = None) -> dict[str, dict]:
    table = load_pronunciations(script)
    # Each chunk's neighbours across the whole script, for engines that stitch prosody.
    texts = [respell(" ".join(c.words), table) for sc in script.scenes for c in sc.chunks]
    context = [(texts[i - 1] if i else "", texts[i + 1] if i + 1 < len(texts) else "") for i in range(len(texts))]
    tts = None
    records = {}
    pos = 0
    for scene in script.scenes:
        ctx, pos = context[pos:pos + len(scene.chunks)], pos + len(scene.chunks)
        if only and scene.id not in only:
            wf = ep / "audio" / "vo" / f"{scene.id}.words.json"
            if wf.exists():
                records[scene.id] = json.loads(wf.read_text(encoding="utf-8"))
                continue
        records[scene.id], tts = voice_scene(ep, script, scene, tts, table, ctx)
    if tts is not None and tts.chars:
        mins, secs = divmod(round(tts.seconds), 60)
        info(f"  {script.setting('tts')}: {tts.chars} characters synthesised in {mins}m {secs:02d}s")
    return records
