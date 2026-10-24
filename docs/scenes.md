# Designing scenes

Each scene is one HTML file, `episodes/<slug>/scenes/<id>.html`: a HyperFrames sub-composition with
a [GSAP](https://gsap.com) timeline. `sync` creates it from the scene's `> template:` the first time,
and from then on it is yours. Read `brand/frame.md` (the house style) before designing.

!!! note
    Changing `> template:` after a scene file exists does nothing. Delete the scene file to re-stub it.

## Templates

| Template | Use it for | Cues it expects |
| --- | --- | --- |
| `title` | Opening scene: tag, headline, standfirst, byline | `sub` |
| `blank` | Chapter head and one line. A starting point for custom visuals | `line` |
| `stat` | One big counted-up number with a caption and source | `figure` |
| `quote` | A document or speech with the key phrase washed in red | `key` |
| `points` | Up to four numbered points | `p1` … `p4` |
| `outro` | The closing line, with the right ~45% kept clear for YouTube end-screen elements | `next` |

A template is only a starting point. Open the file, replace the placeholder text and rework the
layout. Cue names in the template are fallbacks if a cue is missing from the script.

## Anatomy of a scene

```html
<div id="root" data-composition-id="scene-hook" data-width="1920" data-height="1080">
  <div class="paper"></div>
  <div id="hook-stage" class="stage"> … </div>
</div>

<script>
  (() => {
    /* <studio:timing> */
    const T = { duration: 6, voStart: 0.5, voEnd: 5.5, cues: {}, paragraphs: [0.5] };
    /* </studio:timing> */
    const cue = (name, fallback = T.voStart) => T.cues[name] ?? fallback;

    const tl = gsap.timeline({ paused: true });
    tl.fromTo("#hook-title", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, 0.4);
    tl.to("#hook-stage", { opacity: 0, duration: 0.45, ease: "power2.in" }, T.duration - 0.5);
    window.__timelines["scene-hook"] = tl;
  })();
</script>
```

The rules that keep scenes working:

- **Keep the timing block.** `sync` rewrites everything between `/* <studio:timing> */` and
  `/* </studio:timing> */`. It holds `T = {duration, voStart, voEnd, cues, paragraphs}` in
  scene-local seconds.
- **Prefix ids and scene-local classes with the scene id** (`#hook-title`). All scenes share one page
  in preview. Style the root as `#root`, and keep the script inside its IIFE.
- **Start with `<div class="paper">`**, with the content in `.stage`, which is the title-safe area.
- **Use `gsap.fromTo` for entrances**, and no CSS `transform` on anything GSAP moves.
- **Keep the final 0.5s exit fade**, except in the outro.
- **Show a source** (`.byline`) for every figure, quote and photo.

## Timing to the narration

Tie each animation to a cue rather than a guessed number of seconds:

```markdown
The union had won just one demand. {key} It was the shortest strike in the mill's history.
```

```js
tl.fromTo("#quote-wash", { scaleX: 0 }, { scaleX: 1, duration: 0.5 }, cue("key", 2.0));
```

`cue("key", 2.0)` is the scene-local time at which the word after `{key}` is spoken; `2.0` is the
fallback. Re-record or re-voice the narration, run `sync`, and every animation moves with it.

Other values in `T`:

| Field | Meaning |
| --- | --- |
| `T.duration` | Scene length in seconds |
| `T.voStart`, `T.voEnd` | When the narration starts and ends in the scene |
| `T.paragraphs` | Start time of each paragraph |

## Images and footage

Put files in `episodes/<slug>/assets/media/` and reference them as `assets/media/photo.jpg`. Photos
are allowed only as evidence (archival images, news photos with credit), set full-width with a
caption. Always include a credit line.

## The house style

`brand/brand.css` provides the classes scenes are built from:

| Class | What it is |
| --- | --- |
| `.paper`, `.stage` | White ground, and the title-safe content box |
| `.section-head` + `.section-rule` + `.label` | Heavy rule with an uppercase label |
| `.tag` | Dark box with a white uppercase label (like "PERSPECTIVE") |
| `.headline` | PT Serif Bold, sentence case |
| `.standfirst` | PT Serif Italic in soft grey |
| `.body` | PT Serif body text |
| `.quote` | Blockquote with a red left rule |
| `.byline` | Small grey source and date line |
| `.hl` | Red-wash highlight behind a key phrase |
| `.hairline`, `.panel` | Thin rule; light-grey box |
| `.red`, `.soft`, `.italic`, `.sans`, `.mono` | Utility modifiers |

The principles, in short: white ground, one red, one focal point. Red goes on the single word,
figure or arrow the narration is pointing at right now. Documents and evidence beat decoration. No
stock photos, emoji, drop shadows, gradients or rounded app cards. Minimum sizes are 44px for body
text and 72px for headlines, because phones are the main screen.

`brand/frame.md` is the full spec: tokens, components and motion. Edit the house style **in
`brand/`**, never in an episode's `assets/brand/` copy, which `sync` overwrites.

For motion and the composition contract, see the `hyperframes-core` and `hyperframes-animation`
skills.

## Checking your work

```bash
uv run studio check my-video                                   # must pass with 0 errors
npx hyperframes snapshot episodes/my-video --at 12.5,40        # PNGs at those times
```

Look at the snapshots. The audits catch overflow and contrast problems, but not whether it looks right.
