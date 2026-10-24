# Settings

Settings go in the front matter of `script.md`. Everything is optional; defaults live in
`tools/studio/common.py`. Changing a voice setting re-synthesises the narration.

```yaml
---
title: My Video
tts: kokoro
voice: bf_emma*0.6 + bf_isabella*0.4
speed: 0.85
---
```

## Episode

| Setting | Default | Meaning |
| --- | --- | --- |
| `title` | the slug | Episode title |
| `format` | `landscape` | `landscape` (1920×1080) or `reel` (1080×1920). See [Reels](reels.md) |
| `burn_captions` | `false` | Burn word-highlighted captions into the video |
| `fps` | `30` | Frame rate |
| `pronounce` | none | TTS-only respellings, such as `{ Engels: Engles }` |

## Voice

| Setting | Default | Meaning |
| --- | --- | --- |
| `tts` | `kokoro` | `kokoro`, `chatterbox` or `elevenlabs` |
| `voice` | `bf_emma*0.6 + bf_isabella*0.4` | Kokoro voice or blend; ElevenLabs voice ID; Chatterbox clip path or `default` |
| `speed` | `0.85` | Speaking rate, relative to each voice. ElevenLabs accepts 0.7–1.2; Chatterbox ignores it |

### Kokoro

| Setting | Default | Meaning |
| --- | --- | --- |
| `g2p` | `misaki` | Phonemizer: `misaki` or `espeak` |
| `sentence_pause` | `0.38` | Seconds of silence between sentences |
| `clause_pause` | `0.12` | Seconds of silence where an over-long sentence is split at a comma |
| `voice_fx` | `true` | Gentle EQ, de-ess, compressor and faint room |

### Chatterbox

| Setting | Default | Meaning |
| --- | --- | --- |
| `chatterbox_model` | `turbo` | `turbo` (350M) or `standard` (500M) |
| `exaggeration` | `0.5` | `standard` only. Emotional intensity, 0.25–2 |
| `cfg_weight` | `0.5` | `standard` only. Lower is slower and more deliberate |
| `temperature` | `0.8` | Sampling temperature |
| `seed` | `0` | Random seed, so a re-synthesis repeats |

`sentence_pause`, `clause_pause` and `voice_fx` apply to Chatterbox as well.

### ElevenLabs

| Setting | Default | Meaning |
| --- | --- | --- |
| `tts_model` | `eleven_multilingual_v2` | ElevenLabs model |
| `voice_settings` | none | `{stability, similarity_boost, style, use_speaker_boost}` |

## Timing

| Setting | Default | Meaning |
| --- | --- | --- |
| `pad_in` | `0.6` | Silence before a scene's narration starts |
| `pad_out` | `0.9` | Silence after it ends |
| `paragraph_gap` | `0.45` | Pause between paragraphs inside a scene |

## Music and loudness

| Setting | Default | Meaning |
| --- | --- | --- |
| `music` | none | Path to a music bed, relative to the studio root |
| `music_db` | `-24` | Level under narration, before ducking |
| `music_fade_in` | `2` | Seconds. `0` keeps a hit on the bed's first beat |
| `loudness` | `-14` | Integrated LUFS target |
| `true_peak` | `-1.5` | dBTP ceiling |

## Environment

| Variable | Meaning |
| --- | --- |
| `ELEVENLABS_API_KEY` | ElevenLabs key. Also read from `.env` at the studio root |
| `STUDIO_HF_VERSION` | Override the pinned HyperFrames version |
| `STUDIO_CHATTERBOX_VERSION` | Override the pinned Chatterbox version |
