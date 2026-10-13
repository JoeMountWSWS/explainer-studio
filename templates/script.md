---
title: __TITLE__
voice: bf_emma*0.6 + bf_isabella*0.4   # Kokoro voice or weighted blend; audition with `studio voices`
speed: 0.85             # ~165 wpm with this voice
# music: brand/music/your-bed.mp3   # optional; ducked under narration automatically
# pronounce:                        # TTS-only respellings for this episode (captions keep the original)
#   Engels: Engles
---

<!--
HOW THIS FILE WORKS (delete this comment when you like)
- `## id: Chapter title` starts a scene. The id is lowercase letters/digits/hyphens and names
  scenes/<id>.html. Consecutive scenes with the same title share one YouTube chapter.
- Plain paragraphs are narration. Blank lines between paragraphs become short pauses.
- `> template: title|blank|quote|points|stat|outro` picks the starting design for a NEW scene.
- `> duration: 4` sets a minimum length (needed for a scene with no narration).
- Any other `>` line is a note about the visuals. It is never spoken.
- `{name}` marks a cue: the scene can animate exactly when the next word is spoken,
  via cue("name") in scenes/<id>.html. `{pause 1.5}` inserts a pause in seconds.
- Write numbers and abbreviations the way they should be SPOKEN, e.g. "nineteen seventeen"
  rather than "1917" when the voice gets it wrong. The screen can still show "1917".
- Pacing: about 150 words a minute. A 5-minute video is about 700-750 words.
-->

# __TITLE__

## hook: __TITLE__
> template: title
> Open on the question the video answers. No "welcome to the channel".

Start with a question, a contrast, or a fact the viewer doesn't expect. {sub} Then say, in one sentence, what this video will explain.

## context: Background
> template: blank

Set up what the viewer needs to know before the argument starts. {line} Keep it concrete: a date, a place, a figure.

## argument: The argument
> template: points

The core of the video goes here, built up point by point. {p1} The first point. {p2} The second point. {p3} And the third.

## evidence: The evidence
> template: quote

Quote the source directly, and name it. {key} Put a cue on the phrase that matters most.

## outro: Conclusion
> template: outro

Close by restating the main idea in one line, and say what to read or watch next. {next}
