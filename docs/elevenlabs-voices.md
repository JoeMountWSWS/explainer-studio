# ElevenLabs voices (British English)

Notes from 13 October 2026. These picks come from ElevenLabs' descriptions and labels and from
third-party reviews. **No one has listened to them for this studio yet**, so A/B them on a real
paragraph before committing an episode to one.

## Using a voice

In the episode's `script.md` front matter:

```yaml
tts: elevenlabs
voice: onwK4e9ZLuTAKqWW03F9   # Daniel
```

The key is read from `ELEVENLABS_API_KEY` (environment or `.env`). See `AGENTS.md` for
`tts_model`, `voice_settings` and `speed`. The same key also drives `studio music`, which needs the
`music_generation` permission enabled on it.

## Built-in British voices (IDs confirmed via `GET /v1/voices`)

| Voice | ID | ElevenLabs' description | Fit for these videos |
|---|---|---|---|
| **Daniel** (male) | `onwK4e9ZLuTAKqWW03F9` | "Steady broadcaster", "professional broadcast or news story" | **First choice.** Measured news-reader delivery suits editorial and news-style explainers. |
| **Lily** (female) | `pFZP5JQG7iQjIQuC4Bku` | "Velvety… news and narrations with warmth and clarity" | **Best female option.** Serious but warm. |
| **George** (male) | `JBFqnCBsd6RMkjVDRZzb` | "Warm, captivating storyteller" | Good for history pieces; may be too gentle for polemic. |
| **Alice** (female) | `Xb7hH8MSUJpSbSDYk0k2` | "Clear, engaging educator", for e-learning | Clear but brighter and friendlier, more like a tutorial. |

## Voice library candidates (unverified)

The IDs below come from third-party listings, which mix up names and IDs. Check each one on the
ElevenLabs voice library page before using it.

- **Frederick Surrey**: calm, well-spoken British narrator, listed for history and science
  documentaries. The strongest documentary match. ID not found.
- **Alex – Calm and Professional**: polished London accent, man in his 40s. Listed ID:
  `f8zQcd23TbdYnsgvJ3ER`.

`episodes/demo-elevenlabs/` uses `NFG5qt843uXKj4pFvR7C`, a library voice that wasn't identified.

## Caveats

- The API key in `.env` lacks the `voices_read` permission, so the full voice library couldn't be
  searched by accent or use case. With that permission, `GET /v1/shared-voices?language=en&accent=british&use_cases=informative_educational`
  lists library voices (add `sort=cloned_by_count` to sort by popularity).
- ElevenLabs is removing its older "Default" voices (Rachel, Adam, Josh and others) on
  31 December 2026, and only accounts created before March 2026 can use them now. The four
  built-in voices above are not on that list. Don't build an episode around a Default voice.

## Sources

- [ElevenLabs: Professional Narrator voices](https://elevenlabs.io/voice-library/professional-narrator-voices)
- [ElevenLabs: What are Default voices?](https://elevenlabs.io/docs/help-center/product/voices/my-voices/what-are-default-voices)
- [json2video: ElevenLabs voices with IDs](https://json2video.com/ai-voices/elevenlabs/)
- [AI Voice Review: Best ElevenLabs Voices 2026](https://aivoicereview.com/blog/best-elevenlabs-voices-2026)
- [Cognitive Future: Best ElevenLabs Voices](https://cognitivefuture.ai/best-elevenlabs-voices/)
- [ElevenLabs Magazine: Default voices expiring Dec 2026](https://elevenlabsmagazine.com/elevenlabs-default-voices-expiring-december-2026-migration-guide/)
