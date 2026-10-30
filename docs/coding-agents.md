# Working with a coding agent

The studio is built to be driven by a coding agent such as [Claude Code](https://claude.com/claude-code).
You describe the video; the agent writes the script, runs the commands, designs the scenes, looks at
the frames and fixes what `studio check` reports. You stay in charge of the words, the voice and the
final cut.

This works because everything is plain text and every step is a command:

- `script.md` is the source of truth for the words, the scene order and the chapters.
- Each scene is one HTML file the agent can edit and re-render in seconds.
- `uv run studio check` gives the agent a pass/fail signal, and `npx hyperframes snapshot` gives it
  pictures to look at.

## What the agent reads

Open the agent in the repository root (or, for a pip install, your workspace after `studio install-skill`). It picks up three sources of guidance automatically:

| Source | What it gives the agent |
| --- | --- |
| `CLAUDE.md` → `AGENTS.md` | The conventions: script format, every front-matter setting, voice engines, scene rules, the render pipeline and known problems |
| `.claude/skills/make-explainer-video/` | The studio skill: the end-to-end workflow, described [below](#the-make-explainer-video-skill) |
| `brand/frame.md` | The house style. The agent reads it before designing a scene |

It also uses the HyperFrames skills (`hyperframes-core` and `hyperframes-animation`) for the
composition contract and motion. Install them with the HyperFrames CLI if your agent doesn't have them
(`npx hyperframes skills`).

Other agents that read `AGENTS.md` get the conventions but not the skill, which is specific to Claude
Code. Point them at `AGENTS.md` and this page.

## The `make-explainer-video` skill

The repository includes a Claude Code [skill](https://code.claude.com/docs/en/skills) at
`.claude/skills/make-explainer-video/SKILL.md`. It packages the whole workflow so you don't have to
explain it each time. Claude loads it when a request matches its description: creating, scripting,
narrating, designing, previewing, checking, rendering or thumbnailing an episode, or fixing a failing
`studio check` or render.

### Using it

Start Claude Code in the repository root. A project skill in `.claude/skills/` is available with no
installation. (With a pip install, run [`studio install-skill`](#installing-it) first.)

```bash
cd explainer-studio
claude
```

Then either ask in plain language and let Claude pick the skill up:

```text
Make a 5 minute explainer on the 1871 Paris Commune from the notes in notes/commune.md.
Use the default voice, and stop after sync so I can review the script.
```

or invoke it by name:

```text
/make-explainer-video a 45 second reel on the French pension strikes, from this article: <url>
```

### What it does

The skill walks the agent through the same steps as [Getting started](getting-started.md):

1. **Scaffold** with `studio new`, after reading `templates/script.md` and the worked example
   `episodes/demo-paris-commune/`.
2. **Write `script.md`**: one scene per section, a hook in the first 5–10 seconds, about 150–165 words
   a minute, numbers written as they are spoken, and a re-hook at each section change.
3. **Sync** to narrate and align, then read `studio status` to fix length and pacing in the script.
4. **Design each scene**: cue-timed animation, scene-prefixed ids, a source line on every figure and
   quote, and one idea on screen at a time.
5. **Review** with `studio preview`, or `npx hyperframes snapshot` frames it can view itself.
6. **Check**: `studio check` must pass with 0 errors before any render.
7. **Render** a draft, spot-check its frames, then render the final video.

It finishes by reporting the paths of the files in `out/`. It also writes a song description you can
paste into a music generator such as Suno, for an instrumental bed under the narration.

### First-time setup

For a new user the agent starts with `studio setup --check`, explains anything missing in plain language,
and asks you to run the interactive wizard yourself (`! studio setup` in Claude Code), so your API key never
passes through the agent. It then offers a guided first episode.

### What it won't do without asking

The skill tells the agent to:

- ask before switching to a paid voice engine (`tts: elevenlabs`);
- never read or print `.env`, where the ElevenLabs key lives (the project settings also deny it);
- never hand-edit generated files (`index.html`, `timing.json`) or the synced `assets/brand/` copy.

### Installing it

In a clone of the repository the skill is available with no installation. If you installed the studio
from PyPI, install the skill into your workspace (the folder holding `episodes/`):

```bash
cd my-videos
studio install-skill           # -> .claude/skills/make-explainer-video/
```

That copies `SKILL.md` and a `references/` folder (the studio guide, house-style spec and starter
script, which the skill reads in place of `AGENTS.md` and `brand/frame.md`). Start `claude` in the
workspace and ask for a video, or run `/make-explainer-video`.

| Option | Effect |
| --- | --- |
| `--user` | Install to `~/.claude/skills/` so the skill is available in every project |
| `--dir SKILLS_DIR` | Install into another skills folder, for an agent that reads skills from elsewhere |
| `--force` | Replace an existing copy that differs. Run it after upgrading the package to refresh the skill |

Without `--force` the command refuses to overwrite a changed copy, so local edits aren't lost.

## A good first session

1. Gather your source material in a file in the repository, such as `notes/<topic>.md`, or paste a
   URL. The agent can't invent facts, and the script is only as good as what you give it.
2. Ask for the script first, and **stop after `sync`**. The words are the part you most want to
   control, and changing them later re-narrates only the paragraphs you touch.
3. Read `script.md` and `uv run studio status <slug>`. Ask for edits in plain language: "tighten the
   second section", "open on the pension figure instead".
4. Let the agent design the scenes and run `studio check`.
5. Run `uv run studio preview <slug>` yourself and watch it with the narration. Ask for changes
   scene by scene, naming the scene id.
6. Ask for a draft render, then the final.

!!! tip
    Say which voice you want, or ask the agent to run `studio voices <slug>` and give you samples to
    listen to. Voice choice is a matter of taste, and changing it re-narrates everything.

## Getting good results

- **Be specific about length and audience.** "Five minutes for people who've never heard of it" gives
  the agent a word budget and a register.
- **Give it sources, and say which to trust.** Every figure, quote and photo gets a `.byline`
  credit, so the agent needs to know where each came from.
- **Put images in the right place.** Drop files in `episodes/<slug>/assets/media/` and tell the agent
  what they show. It can't see an image's meaning from the filename.
- **Review frames, not just checks.** `studio check` catches overflow and contrast problems but not
  whether a scene looks right. Ask the agent to snapshot specific times and describe what it sees.
- **Edit the script, not the generated files.** If something is wrong in the timing or `index.html`,
  the fix is in `script.md` or a scene file, then `sync`.
- **Change the house style in `brand/`.** Anything the agent changes in an episode's `assets/brand/`
  is overwritten by the next `sync`.
- **Commit after `sync`.** CI never narrates or renders, so `audio/vo/`, `timing.json` and `index.html`
  must be committed. Commit messages use `episode:` for episode content and `brand:` for the house
  style.

## When the agent gets stuck

| Symptom | What to tell the agent |
| --- | --- |
| `studio check` fails | "Run `studio check` and fix every error. Don't render until it passes." |
| A scene's animation fires at the wrong moment | "Use `cue()` and `T.*` for timing, not fixed seconds." |
| Layout looks wrong in a render but check passes | "Snapshot at these times and compare with `brand/frame.md`." |
| The narration mispronounces a word | "Add a respelling to `pronounce:` in the front matter." |
| A render hangs or has empty frames | See [Troubleshooting](troubleshooting.md) |
| It wants to change a scene's template | "Delete the scene file and re-run `sync`." Changing `> template:` on an existing scene does nothing |

## Extending the skill

The skill is one Markdown file with a short front-matter block. If you find yourself repeating an
instruction (a house rule about sourcing, a standard outro, a preferred voice), add it to
`.claude/skills/make-explainer-video/SKILL.md` and commit it, so every session gets it. Keep the
`description` accurate: it is how Claude decides when to load the skill. Put reference material that
every agent needs in `AGENTS.md` instead, and use the skill for the workflow.
