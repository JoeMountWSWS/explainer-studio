# Writing a script

An episode is one Markdown file, `episodes/<slug>/script.md`: a front matter block, then a series of
scenes.

```markdown
---
title: The Paris Commune
voice: bf_emma*0.6 + bf_isabella*0.4
speed: 0.85
music: brand/music/bed.mp3
pronounce: { Engels: Engles }
---
## hook: Seventy-two days
> template: title
> duration: 4
> A quoted line like this is a note about the visuals. It is never spoken.

In the spring of 1871, the working class took power in a major city. {sub} This is the story of
the Paris Commune.

A blank line starts a new paragraph, with a short pause. {pause 1.5} That was an explicit pause.
```

## Scenes

`## <id>: <chapter title>` starts a scene.

- **The id** is lowercase, starts with a letter, and uses only `a-z`, `0-9` and `-`. It names the
  scene file, `scenes/<id>.html`.
- **The title** becomes the YouTube chapter. Consecutive scenes with the same title merge into one
  chapter. YouTube needs at least 3 chapters, each 10 seconds or longer, and `render` warns when
  they aren't.

Lines starting with `>` directly under the heading are scene options:

| Line | Meaning |
| --- | --- |
| `> template: title` | The pattern for a **new** scene file: `title`, `blank`, `stat`, `quote`, `points` or `outro`. Changing it after the file exists does nothing. Delete the scene file to re-stub it |
| `> duration: 4` | A minimum length in seconds. Required for a scene with no narration |
| `> anything else` | A note about the visuals. Never spoken |

## Narration, cues and pauses

Every other paragraph is narration.

- **Paragraphs.** A blank line between paragraphs becomes a short pause (`paragraph_gap`, 0.45s).
- **Cues.** `{name}` marks the word that follows. The scene can act exactly when that word is spoken
  by calling `cue("name")`. See [Designing scenes](scenes.md#timing-to-the-narration).
- **Pauses.** `{pause 1.5}` inserts a pause of that many seconds.

Cue names are free-form. The `points` template, for instance, expects `{p1}` to `{p4}`.

## Writing for the ear

- **Open on a question, contrast or striking fact**, never "welcome to the channel". The first 5–10
  seconds decide retention. Then say what the video will explain.
- **Length.** About 150–165 words a minute, so 5 minutes is roughly 700–750 words. Leave visual
  breathing room.
- **Structure.** Three main sections beat seven. Re-hook at each section change and keep a payoff for
  the end.
- **One idea on screen at a time**, triggered by the narration. Diagrams, documents and figures
  carry the argument. Bullets are a last resort.
- **Punctuation is the delivery control.** The voice ignores SSML and emotion tags. Use commas for
  breaths, full stops for resets, `?` for questions and `{pause n}` for a beat.

## Numbers, abbreviations and names

Write numbers and abbreviations as they should be **spoken** when the voice gets them wrong ("nineteen
seventeen" rather than "1917"), or add a respelling:

- Studio-wide respellings go in `brand/pronunciations.yaml` (for example `NATO: Nay-toe`).
- Episode-specific ones go under `pronounce:` in the front matter.

Respellings only affect the voice. **Captions and on-screen text keep the script's spelling.** Test a
respelling with `uv run studio voices <slug> --scene <id>`, which uses the same voice and phonemizer
as `sync`.

## Front matter

Besides `title`, the front matter holds the voice and rendering settings. Everything has a default,
so a script only needs to set what it changes. See [Settings](settings.md) for the full list.
