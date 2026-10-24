# Explainer Studio

A command-line studio for narrated explainer videos in the style of [wsws.org](https://www.wsws.org).

You write a script in Markdown. The studio narrates it with text-to-speech, aligns every word to the
audio, and turns each scene into a [HyperFrames](https://www.npmjs.com/package/hyperframes) HTML
composition timed to the narration. It then renders a mastered 1920×1080 MP4 for YouTube, with
captions and chapter markers.

```
script.md ──► narration (Kokoro, local; or Chatterbox / ElevenLabs) ──► word timings (Whisper)
          ──► scenes/<id>.html (HyperFrames + GSAP, timed to cues) ──► cached per-scene renders
          ──► out/<slug>.mp4  (−14 LUFS)  +  out/<slug>.srt  +  out/<slug>.chapters.txt
```

## What you get

- **The script is the source of truth.** Words, scene order and YouTube chapter titles all come from
  one `script.md`.
- **Visuals follow the voice.** Mark a word with `{cue}` in the script and the scene animates exactly
  when it is spoken. Re-record the narration and the visuals re-time themselves.
- **Fast iteration.** Narration is cached per paragraph and renders are cached per scene, so a small
  edit re-does only what changed.
- **A house style.** Fonts, colours and page furniture come from `brand/`, shared by every episode.
- **YouTube-ready output.** Loudness-mastered audio, an `.srt` caption file and a chapter list.
- **Reels too.** The same pipeline renders 9:16 video with burned-in captions.

## Where to start

<div class="grid cards" markdown>

- **[Getting started](getting-started.md)**: install the tools and make a first video.
- **[Writing a script](script.md)**: the script format, cues and pauses.
- **[Narration](narration.md)**: choose and tune a voice.
- **[Designing scenes](scenes.md)**: templates, cues and the house style.
- **[Rendering and publishing](rendering.md)**: drafts, final renders and what to upload.
- **[Commands](commands.md)** and **[Settings](settings.md)**: the full reference.

</div>

`episodes/demo-paris-commune/` in the repository is a complete worked example (38 seconds, four
scenes). Open its `script.md` and `scenes/` next to these pages.

## Using it with a coding agent

The studio is designed to be driven by [Claude Code](https://claude.com/claude-code) or another
coding agent. [`AGENTS.md`](https://github.com/JoeMountWSWS/explainer-studio/blob/main/AGENTS.md)
(loaded through `CLAUDE.md`) gives the agent the conventions it needs, and the HyperFrames skills
cover the composition format and motion. These pages are written for people.
