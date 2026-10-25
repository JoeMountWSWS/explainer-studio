import io
import json
import urllib.error

import numpy as np
import pytest

from studio import voice
from studio.script import Script


def test_respell_whole_words_longest_first():
    table = {"IYSSE": "eye why ess ess ee", "SEP": "S E P", "SEP members": "ess ee pee members"}
    assert voice.respell("The SEP and the IYSSE.", table) == "The S E P and the eye why ess ess ee."
    assert voice.respell("SEP members met", table) == "ess ee pee members met"
    assert voice.respell("SEPTEMBER and SEP-led", table) == "SEPTEMBER and SEP-led"  # not inside words


def test_load_pronunciations_script_overrides_brand(tmp_path, monkeypatch):
    (tmp_path / "pronunciations.yaml").write_text("Engels: Engles\nWSWS: W S W S\n")
    monkeypatch.setattr(voice, "BRAND", tmp_path)
    table = voice.load_pronunciations(Script({"pronounce": {"Engels": "Eng-gels"}}, []))
    assert table == {"Engels": "Eng-gels", "WSWS": "W S W S"}


def test_parse_voice_normalises_weights():
    assert voice.parse_voice("bf_emma") == [("bf_emma", 1.0)]
    assert voice.parse_voice("a*3 + b*1") == [("a", 0.75), ("b", 0.25)]
    assert voice.parse_voice("a + b") == [("a", 0.5), ("b", 0.5)]


@pytest.mark.parametrize("spec", ["a + ", "a*x", "a*0 + b*0"])
def test_parse_voice_errors(spec):
    with pytest.raises(SystemExit):
        voice.parse_voice(spec)


def test_voice_spec_is_canonical():
    assert voice.voice_spec(" bf_emma ") == "bf_emma"
    assert voice.voice_spec("bf_emma*6 + bf_isabella*4") == "bf_emma*0.6 + bf_isabella*0.4"
    assert voice.voice_spec("a + b + c") == "a*0.333 + b*0.333 + c*0.333"


def test_sentence_groups_merge_short_sentences_forward():
    long = "x" * 45
    assert voice.sentence_groups(f"Hi. {long}. Ok.") == [f"Hi. {long}. Ok."]
    assert voice.sentence_groups(f"{long}. {long}.") == [f"{long}.", f"{long}."]
    assert voice.sentence_groups("Short.") == ["Short."]


def test_text_groups_packs_sentences_then_clauses_then_words():
    assert voice.text_groups("One. Two. Three.", 10) == [("One. Two.", True), ("Three.", True)]
    assert voice.text_groups("alpha beta, gamma delta.", 12) == [("alpha beta,", False), ("gamma delta.", True)]
    assert voice.text_groups("aaaa bbbb cccc dddd.", 9) == [("aaaa bbbb", False), ("cccc", False), ("dddd.", True)]


def test_pack():
    assert voice.pack(["ab", "cd", "efgh"], 5) == ["ab cd", "efgh"]
    assert voice.pack([], 5) == []


def test_join_parts_inserts_silence_between_parts_only():
    out = voice.join_parts([(np.ones(3, np.float32), 0.5), (np.ones(2, np.float32), 9.0)], rate=4)
    assert out.tolist() == [1, 1, 1, 0, 0, 1, 1]


def test_trim_silence_keeps_margin():
    rate = 100
    samples = np.concatenate([np.zeros(50), np.full(10, 0.5), np.zeros(50)]).astype(np.float32)
    trimmed = voice.trim_silence(samples, rate, margin=0.03)
    assert trimmed[:3].tolist() == [0, 0, 0] and trimmed[3] == 0.5
    assert np.count_nonzero(trimmed) == 10 and len(trimmed) < 20
    silent = np.zeros(20, np.float32)
    assert voice.trim_silence(silent, rate) is silent


def test_align_uses_transcript_and_interpolates_the_rest():
    script_words = ["The", "IYSSE", "met", "in", "1871."]
    asr = [
        {"text": "the", "start": 0.0, "end": 0.2},
        {"text": "eye", "start": 0.2, "end": 0.4},  # respelled acronym: no match
        {"text": "why", "start": 0.4, "end": 0.6},
        {"text": "met", "start": 0.6, "end": 0.9},
    ]
    words = voice.align(script_words, asr, [(0, 5, 0.0, 2.0)])
    assert [w["text"] for w in words] == script_words
    assert words[0] == {"text": "The", "start": 0.0, "end": 0.2}
    assert words[1] == {"text": "IYSSE", "start": 0.2, "end": 0.6}  # between its matched neighbours
    assert words[2] == {"text": "met", "start": 0.6, "end": 0.9}
    # "in 1871." are unmatched up to the chunk end, split by length (2 : 5 characters)
    assert words[3]["start"] == 0.9 and words[4]["end"] == 2.0
    assert words[3]["end"] == pytest.approx(0.9 + 1.1 * 2 / 7, abs=1e-3)


def test_align_with_no_transcript_spreads_over_each_chunk():
    words = voice.align(["a", "b", "c"], [], [(0, 2, 0.0, 1.0), (2, 3, 1.5, 2.5)])
    assert [(w["start"], w["end"]) for w in words] == [(0.0, 0.5), (0.5, 1.0), (1.5, 2.5)]


@pytest.mark.parametrize("name, cls", [("kokoro", voice.Kokoro), ("ElevenLabs", voice.ElevenLabs),
                                       ("chatterbox", voice.Chatterbox)])
def test_engine_class(name, cls):
    assert voice.engine_class(Script({"tts": name}, [])) is cls


def test_engine_class_unknown():
    with pytest.raises(SystemExit):
        voice.engine_class(Script({"tts": "festival"}, []))


def test_chatterbox_model():
    assert voice.chatterbox_model(Script({}, [])) == "turbo"
    assert voice.chatterbox_model(Script({"chatterbox_model": "Standard"}, [])) == "standard"
    with pytest.raises(SystemExit):
        voice.chatterbox_model(Script({"chatterbox_model": "huge"}, []))


def test_chatterbox_ref(tmp_path, monkeypatch):
    monkeypatch.setattr(voice, "ROOT", tmp_path)
    assert voice.chatterbox_ref(Script({}, [])) is None
    assert voice.chatterbox_ref(Script({"voice": "default"}, [])) is None
    (tmp_path / "clip.wav").write_bytes(b"RIFF")
    assert voice.chatterbox_ref(Script({"voice": "clip.wav"}, [])) == tmp_path / "clip.wav"
    assert voice.clip_hash(tmp_path / "clip.wav") == voice.clip_hash(tmp_path / "clip.wav")
    with pytest.raises(SystemExit):
        voice.chatterbox_ref(Script({"voice": "missing.wav"}, []))


def test_find_recording_prefers_listed_extension_order(tmp_path):
    rec = tmp_path / "audio" / "recorded"
    rec.mkdir(parents=True)
    assert voice.find_recording(tmp_path, "hook") is None
    (rec / "hook.mp3").write_bytes(b"")
    (rec / "hook.flac").write_bytes(b"")
    assert voice.find_recording(tmp_path, "hook") == rec / "hook.flac"


def test_elevenlabs_key(monkeypatch, tmp_path):
    monkeypatch.setattr(voice, "load_env", lambda: None)
    monkeypatch.setenv("ELEVENLABS_API_KEY", " sk_123 ")
    assert voice.elevenlabs_key() == "sk_123"
    monkeypatch.delenv("ELEVENLABS_API_KEY")
    with pytest.raises(SystemExit):
        voice.elevenlabs_key()


def _http_error(code: int, body: dict | None = None) -> urllib.error.HTTPError:
    fp = io.BytesIO(json.dumps(body).encode()) if body is not None else io.BytesIO(b"not json")
    return urllib.error.HTTPError("https://api", code, "Reason", {}, fp)


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_elevenlabs_post_retries_rate_limits_and_network_errors(monkeypatch):
    outcomes = [_http_error(429), urllib.error.URLError("dns"), _Resp(b"audio")]
    sent = []

    def urlopen(req, timeout):
        sent.append(req)
        result = outcomes.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    sleeps = []
    monkeypatch.setattr(voice.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(voice.time, "sleep", sleeps.append)
    assert voice.elevenlabs_post("https://api", "k", {"text": "hi"}) == b"audio"
    assert sleeps == [2, 4]
    assert sent[0].get_header("Xi-api-key") == "k"
    assert json.loads(sent[0].data) == {"text": "hi"}


@pytest.mark.parametrize("error, message", [
    (_http_error(401, {"detail": {"status": "missing_permissions", "message": "needs music_generation"}}),
     "ElevenLabs 401: needs music_generation"),
    (_http_error(400, {"detail": "bad voice"}), "ElevenLabs 400: bad voice"),
    (_http_error(403), "ElevenLabs 403: Reason"),
])
def test_elevenlabs_post_reports_client_errors(monkeypatch, capsys, error, message):
    def urlopen(req, timeout):
        raise error

    monkeypatch.setattr(voice.urllib.request, "urlopen", urlopen)
    with pytest.raises(SystemExit):
        voice.elevenlabs_post("https://api", "k", {})
    assert message in capsys.readouterr().err


def test_elevenlabs_post_gives_up_after_retries(monkeypatch, capsys):
    def urlopen(req, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(voice.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(voice.time, "sleep", lambda s: None)
    with pytest.raises(SystemExit):
        voice.elevenlabs_post("https://api", "k", {})
    assert "unreachable: offline" in capsys.readouterr().err


def test_voice_all_synthesises_caches_and_aligns(write_script, tmp_path, fake_tts, capsys):
    script = write_script("""
        ---
        pronounce: {SEP: S E P}
        ---
        ## a: A
        The SEP {cue} met. {pause 0.5} Then left.

        Second paragraph.

        ## card: Card
        > duration: 2
    """)
    ep = tmp_path / "ep"
    records = voice.voice_all(ep, script)
    assert fake_tts.calls == ["The S E P met.", "Then left.", "Second paragraph."]
    a = records["a"]
    # 5 + 2 + 2 words at 0.1s each (the respelled SEP is three), plus the 0.5s pause and 0.45s paragraph gap
    assert a["duration"] == pytest.approx(0.5 + 0.5 + 0.2 + 0.45 + 0.2)
    assert a["paragraphs"] == [0.0, 1.0, 1.65]
    assert [w["text"] for w in a["words"]] == ["The", "SEP", "met.", "Then", "left.", "Second", "paragraph."]
    assert a["cues"]["cue"] == a["words"][2]["start"]
    assert records["card"] == {"hash": "silent", "duration": 0.0, "words": [], "cues": {}, "paragraphs": []}
    assert (ep / "audio" / "vo" / "a.wav").exists() and not (ep / "audio" / "vo" / "card.wav").exists()
    assert "characters synthesised" in capsys.readouterr().out

    # Unchanged text re-uses the TTS cache and the previous alignment.
    assert voice.voice_all(ep, script) == records
    assert len(fake_tts.calls) == 3
    # Only re-narrating one scene re-uses the others' saved timings.
    assert voice.voice_all(ep, script, only={"card"})["a"] == records["a"]


def test_read_mono_rejects_other_rates(tmp_path):
    voice.sf.write(str(tmp_path / "x.wav"), np.zeros(10, np.float32), 22050)
    with pytest.raises(SystemExit):
        voice.read_mono(tmp_path / "x.wav")
