# Narration

`sync` turns each paragraph into audio, then uses word timings to align the script's words to it.
Narration is cached per paragraph, so changing one paragraph re-synthesises only that paragraph.
Changing a voice setting re-synthesises everything.

Pick the engine with `tts:` in the front matter.

| Engine | `tts:` | Runs | Cost | Good for |
| --- | --- | --- | --- | --- |
| Kokoro-82M | `kokoro` (default) | Locally, in-process | Free | Fast, consistent drafts and finals |
| Chatterbox | `chatterbox` | Locally, on the CPU | Free | Cloning a voice from a short clip |
| ElevenLabs | `elevenlabs` | Cloud | About 1 credit per character | The most natural delivery |

Any scene can also use a [real recording](#recording-your-own-voice) instead.

## Kokoro (local)

```yaml
tts: kokoro
voice: bf_emma*0.6 + bf_isabella*0.4
speed: 0.85
```

`voice:` takes one Kokoro voice or a **weighted blend** (`a*0.6 + b*0.4`) of their style vectors.
Blends sound less synthetic than single voices. UK voices are `bf_*` and `bm_*`; US voices are `af_*`
and `am_*`. By Kokoro's own grades, `bf_emma` (B-) is the best UK voice, and the UK male voices are C
or lower.

`speed` is relative to each voice. Aim for about 150–170 words a minute. The default blend at 0.85
measures about 165; `bm_george` at 1.0 about 155.

### Audition voices

```bash
uv run studio voices my-video
uv run studio voices my-video --scene hook --speed 0.9
uv run studio voices my-video --voices "bf_emma*0.7 + bf_alice*0.3" bm_george
```

This synthesises one scene with each candidate and writes loudness-matched samples to
`out/voice-samples/`, so you can compare them by ear.

### Delivery

- Phonemes come from **misaki** (`g2p: misaki`), the G2P Kokoro was trained on, which gives proper
  RP vowels and reads "1871" as a year. `g2p: espeak` switches to espeak.
- Each sentence is a separate utterance with its own falling intonation, joined by
  `sentence_pause` (0.38s). Over-long sentences are split at commas, joined by `clause_pause`.
- `voice_fx: true` (the default) adds a gentle EQ, de-ess, compressor and faint room.

## Chatterbox (local, voice cloning)

```yaml
tts: chatterbox
voice: brand/voices/narrator.wav   # or `default`
```

`voice:` is a reference clip, with its path relative to the studio root, or `default` for the model's
built-in American voice.

The clip must be **over 5 seconds** (10–15 is best) and clean, dry, mono speech with no music, in the
accent and pace you want. Pacing comes from the clip, so `speed` is ignored.

| Setting | Default | Notes |
| --- | --- | --- |
| `chatterbox_model` | `turbo` | `turbo` (350M, English) or `standard` (500M) |
| `exaggeration` | `0.5` | `standard` only. Higher is more animated |
| `cfg_weight` | `0.5` | `standard` only. Lower is slower and more deliberate |
| `temperature` | `0.8` | Sampling temperature |
| `seed` | `0` | A fixed seed makes a re-synthesis repeat |

Things to know:

- The first run builds its own environment under `~/.cache/hyperframes/chatterbox/` and downloads
  the model (about 1–2 GB). It can't share the studio venv because it pins torch and `numpy<2`.
- It runs on the CPU, about 4–5× slower than real time. Cached chunks are reused, so only changed
  paragraphs are re-synthesised. Re-recording the clip re-synthesises everything.
- Output carries Resemble's inaudible Perth watermark.
- `uv run studio voices <slug>` auditions every `brand/voices/*.wav` plus `default`, or the clips you
  pass with `--voices`.

## ElevenLabs (cloud)

```yaml
tts: elevenlabs
voice: onwK4e9ZLuTAKqWW03F9      # an ElevenLabs voice ID
tts_model: eleven_multilingual_v2
voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.2 }
speed: 1.0                       # 0.7–1.2
```

Put the key in `ELEVENLABS_API_KEY`, either in the environment or in a `.env` file at the studio root
(it is gitignored; never commit it).

It costs about one credit per character. Chunks are cached like Kokoro's, so only new or changed
paragraphs are billed, and `sync` prints the characters it used. Each paragraph is sent with its
neighbours' text so the delivery stays continuous.

See [ElevenLabs voices](elevenlabs-voices.md) for British voice picks.

## Recording your own voice

Drop a file at `episodes/<slug>/audio/recorded/<scene-id>.wav` (or `.flac`, `.m4a`, `.mp3`) and that
scene uses it instead of TTS. The recording is aligned to the script's words the same way, so cues keep working. Read the script as written.
Mix and match: record the scenes you care about and let TTS do the rest.

## Music

```yaml
music: brand/music/bed.mp3
music_db: -24
music_fade_in: 2
```

The bed is ducked under the voice with a sidechain compressor. `music_db` sets its level before
ducking, and `music_fade_in: 0` keeps a hit on the bed's first beat. Credit the track in the video
description; `brand/music/CREDITS.md` has the line for the bundled tracks.

To make a bed instead of finding one, run `uv run studio music <slug> --prompt "…"` after `sync`.
It asks ElevenLabs Music for an instrumental track as long as the episode and prints the `music:`
line to use. See [Commands](commands.md#music).

## Timing and loudness

| Setting | Default | Meaning |
| --- | --- | --- |
| `pad_in` | `0.6` | Silence before a scene's narration starts |
| `pad_out` | `0.9` | Silence after it ends (the exit fade lives here) |
| `paragraph_gap` | `0.45` | Pause between paragraphs in a scene |
| `loudness` | `-14` | Integrated LUFS target (YouTube normalises to -14) |
| `true_peak` | `-1.5` | dBTP ceiling |

## Word timings

Word timings come from Whisper (`hyperframes transcribe`, small.en). Installing the faster, more
accurate Parakeet model switches to it automatically:

```bash
npx hyperframes models install parakeet
```
