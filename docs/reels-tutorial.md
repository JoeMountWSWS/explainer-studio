# Make your first social media reel: a beginner's tutorial

This guide takes you from "I have a computer" to "I have a finished vertical video for Instagram,
TikTok or YouTube Shorts". You don't need to be a programmer. You will copy and paste a few commands,
write a short script in plain English, and let an AI assistant do the technical work.

**What you will end up with:** a 30–60 second vertical video (1080×1920) with a computer-generated
voice reading your script, animated text and images timed to the words, and captions burned in.

**How long it takes:** about an hour for the one-off setup, then 20–40 minutes per reel once you
know the routine.

---

## 1. How it works, in plain words

The studio is a set of tools that turns a **script** into a **video**:

1. You write what the narrator should say, split into short scenes.
2. A text-to-speech voice reads it aloud (it runs on your own computer, free).
3. The studio works out exactly when each word is spoken.
4. Each scene is a small designed "page" (headline, quote, big number…) that appears on cue.
5. The studio records every scene and joins them into one MP4 file.

You will talk to **Claude Code**, an AI assistant that works inside your project folder (in a terminal
window, or in the Code tab of the Claude Desktop app). You tell it what
reel you want in everyday language, and it writes the files and runs the commands. You review the
result and ask for changes, the way you would with a human video editor.

> **A "terminal"** is a window where you type commands instead of clicking. It looks intimidating,
> but you will only paste in a handful of lines from this guide.

---

## 2. What you need

### A computer

The studio runs on **Windows 10 or 11**, **Linux** and **macOS** (macOS is untested). The tutorial
shows Windows commands first, with a tab for the others wherever they differ.

You need about 8 GB of memory and 10 GB of free disk space (the voice model and the video files add
up). No special graphics card is needed. On Windows and macOS the studio draws each frame by
screenshot, which is slower than on Linux, so expect a 45-second reel to take a few minutes to render.

### A Claude account (this is the part people ask about)

Claude Code is **not part of the free Claude chat plan**. To use it you need one of:

| Option | Good for |
| --- | --- |
| **Claude Pro or Max** subscription (claude.com/pricing) | Most people. A flat monthly price, simplest to set up |
| **Anthropic Console** account with API credit (console.anthropic.com) | Pay-as-you-go, no subscription |
| A team or company account | If your organisation already pays for Claude |

Plans and prices change, so check the pricing page for what is current. Making a reel uses a modest
amount of Claude's allowance, so the entry-level paid plan is enough to start.

**Don't have one yet?** Go to claude.ai, sign up with your email, and choose a paid plan. Then come
back here.

### Optional extras (you can skip these at first)

- **ElevenLabs account**: a more natural, human-sounding narrator. It costs a small amount per
  video. The free built-in voice (Kokoro) is good enough to start with.
- **Your own photos and footage**: for pictures in the reel. Make sure you have the right to use them,
  and always credit the source.

---

## 3. One-off setup

You only do this section once. It has three parts: install the tools, download the studio, then
choose how you want to talk to Claude.

### Step 1: Install the tools

=== "Windows"

    1. Click the Start button, type **PowerShell** and open **Windows PowerShell**. (You don't need
       to run it as administrator.)
    2. Paste these lines, one at a time, pressing Enter after each. Say yes if Windows asks you to
       agree to the source terms:

       ```powershell
       winget install --id Git.Git -e
       winget install --id astral-sh.uv -e
       winget install --id OpenJS.NodeJS.LTS -e
       winget install --id Gyan.FFmpeg -e
       ```

    3. **Close PowerShell and open it again**, so the new commands are found.

=== "Linux"

    ```bash
    sudo apt install -y git ffmpeg nodejs npm curl chromium
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    Then close the terminal and open it again. On other distributions, see [Install](install.md).

=== "macOS (untested)"

    ```bash
    brew install git uv node ffmpeg
    ```

    Then close the terminal and open it again.

(What these are: `git` downloads the studio, `ffmpeg` processes video and sound, `node` runs the
animation engine, and `uv` runs the studio itself. Windows already has Edge, which the studio uses for
thumbnails.)

> **A "terminal"**, on Windows, is the PowerShell window. **Paste** into it with a right-click, or
> `Ctrl+V`.

### Step 2: Download the studio

=== "Windows"

    ```powershell
    cd ~\Documents
    git clone https://github.com/JoeMountWSWS/explainer-studio.git
    cd explainer-studio
    uv sync
    ```

=== "Linux"

    ```bash
    cd ~/Documents
    git clone https://github.com/JoeMountWSWS/explainer-studio.git
    cd explainer-studio
    uv sync
    ```

=== "macOS (untested)"

    ```bash
    cd ~/Documents
    git clone https://github.com/JoeMountWSWS/explainer-studio.git
    cd explainer-studio
    uv sync
    ```

`uv sync` downloads the studio's own software. It takes a few minutes the first time.

> **Working on a team with a separate episodes repository?** Real episodes can live in their own
> repository, set up beside the studio (see [Getting started](getting-started.md#from-pypi)). Ask
> whoever runs your team for access, then `cd` into that folder instead and follow the same steps.

### Step 3: Choose how you will talk to Claude

You have two choices.

#### Option A: Claude Code in the terminal

=== "Windows"

    In PowerShell:

    ```powershell
    irm https://claude.ai/install.ps1 | iex
    ```

=== "Linux"

    ```bash
    curl -fsSL https://claude.ai/install.sh | bash
    ```

=== "macOS (untested)"

    ```bash
    curl -fsSL https://claude.ai/install.sh | bash
    ```

If those commands have changed, the [Claude Code setup guide](https://docs.claude.com/en/docs/claude-code/setup)
has the current ones. Close and reopen the terminal, check it worked with `claude --version`, then
go to the studio folder and start it (on Windows, `cd ~\Documents\explainer-studio`):

```bash
cd ~/Documents/explainer-studio
claude
```

The first time, it opens a browser window so you can sign in with the Claude account from section 2.
Approve it and return to the terminal. If it asks whether you trust the files in this folder, choose
yes. To leave, type `/exit`. To start again later, open the terminal, `cd` to the folder, and run
`claude`.

#### Option B: the Claude Desktop app, in Code mode

The **Claude Desktop** app (download from claude.ai/download) has a **Code** tab, which is Claude
Code with a normal window instead of a terminal: a chat panel, buttons to approve actions, and a
model picker.

1. Install Claude Desktop and sign in with your Claude account.
2. Click the **Code** tab.
3. Choose the studio folder you downloaded in Step 2. On Windows the Code tab needs **Git for
   Windows**, which you installed above.

This studio hasn't been tested with the Desktop app, and the app may change between versions. If you
hit trouble, go back to Option A. Everything from section 4 onward works the same in both. Where
this guide says "type at the Claude Code prompt", Option B means "type in the chat box". Where it
says `/model`, use the model picker if the app has one.

### Step 4: Check the studio's tools

Open Claude Code (either option) in the studio folder and say:

```text
Check that this machine has everything the studio needs (ffmpeg, node, a
browser for rendering, and the voice models). Run `uv run studio setup --check`,
and install or fix anything that's missing. Tell me what you did.
```

Claude knows the studio and will fix typical problems, such as a missing tool. It will ask your
permission before each command. Read the request and approve.

---

## 4. Your first reel

### Step 1: Decide on one idea

A reel has about 30–60 seconds, which is roughly **80–150 spoken words**. Pick **one** fact, argument
or story. If you can't say it in one sentence, it's two reels.

A good shape:

1. **Hook** (first 3 seconds): a striking fact, a question, or a contrast. Never "Hi, welcome to…".
2. **Two or three beats**: one short statement each.
3. **Payoff**: the point, a quote, or a call to action.

### Step 2: Ask an AI assistant for a concept and script

Before you open Claude Code, you can use any AI chat assistant to work up the idea. Describe your topic and ask for
a reel concept and a draft script. For example:

```text
I want a 45-second vertical reel (Instagram / TikTok / Shorts) about the Paris
Commune of 1871. Suggest a concept: the hook for the first 3 seconds, 4 or 5
short beats, and a closing line. Then write the narration script, about 110
words, in short spoken sentences. Suggest one quotation I could show on screen,
with its source.
```

Tips:

- Ask for the **hook first**, then the full script. Keep asking until the opening line grabs you.
- Ask for **short sentences** and **numbers written as they are spoken**.
- Ask for the **source** of every quotation and statistic, and **check them yourself**. Don't publish
  a claim you haven't verified.
- Edit the result in your own words. The script should sound like you, not like a chatbot.

Copy the final concept and script into a text file or note. You'll paste them into Claude Code in
Step 4.

### Step 3: Choose a strong model and turn on Plan Mode

Now open Claude Code in the studio folder (in the terminal: `cd` to it, then
`claude`; or the Code tab in Claude Desktop). Two settings give the best result.

**Choose the most capable model.** Type:

```text
/model
```

and pick the most capable model your plan offers. (If the list is short, see section 2.) Claude Code remembers the choice for next time. In the Desktop app, use the model
picker near the chat box instead.

**Turn on Plan Mode.** Press `Shift+Tab` until the bottom of the screen says **plan mode**. (You may
need to press it twice.) In Plan Mode Claude can read files and think, but it **can't change anything
or run commands until you approve its plan**. That keeps you in control: you see what it intends to
do before it does it. In the Desktop app, pick **Plan** from the mode selector beside the chat box
(the name may differ slightly between versions).

### Step 4: Ask Claude to generate the reel from the spec

Paste in your concept and script from Step 2, and ask Claude to build the reel from the studio's
reel spec. For example:

```text
Make a vertical reel from the concept and script below. Follow the reel spec
in docs/reels.md and brand/frame.md: format reel, burned-in captions, content
inside the safe zones, one statement per screen, a cut every 3 to 6 seconds on
the narration cues, and the striking fact on screen in the first second.
Use about 4 or 5 scenes. Don't change my wording without telling me. Show me
your plan before you narrate or render anything.

[paste the concept and script here]
```

Things to include in your request:

- **"Follow the reel spec"** and where it lives (`docs/reels.md`, `brand/frame.md`). Claude reads
  them and applies the right sizes, layout and style.
- **Your script**, pasted in. Say whether to keep your wording exactly.
- **The length** ("about 45 seconds").
- **Any images or quotes** you want, with their sources.

Claude will research the project, then present a **plan**: the episode name, the scenes, what each
will show, and the commands it will run. Read it. If something is wrong, reply in plain words ("make
the hook shorter", "cut scene 3") and it will revise the plan.

When you're happy, choose the option to **approve the plan**. Claude leaves Plan Mode and starts
work: it creates the project folder under `episodes/` and writes the script file. If it asks
permission to run a command, read the request and approve it. From here you can switch back to Plan
Mode any time with `Shift+Tab` if you want it to propose before acting.

### Step 5: Read and edit the script

The script is a plain text file, `episodes/<name>/script.md`. A reel script looks like this:

```markdown
---
title: Seventy-two days
format: reel
burn_captions: true
---
## hook: Seventy-two days
> template: title
In eighteen seventy-one, ordinary workers ran Paris for seventy-two days.

## quote: In their own words
> template: quote
{quote} They called it the first government of the working class.

## close: What it left behind
> template: outro
Its defeat taught the next generation what to do differently.
```

How to read it:

- `format: reel` and `burn_captions: true` at the top make it vertical with captions.
- Each `## name: Title` line starts a **scene**.
- Lines beginning with `>` are **notes to the designer**, never spoken.
- Everything else is **narration**, the words the voice will say.
- Curly brackets such as `{quote}` are **cues**: moments in the speech where something on screen
  should happen.

You don't have to type any of this yourself. Tell Claude what to change:

- "Make the hook shorter and punchier."
- "Cut the second scene. It repeats the first."
- "End with a question for the viewer."

### Step 6: Check pronunciation

Computer voices stumble over names and abbreviations. When you listen later, tell Claude what sounded
wrong ("It says 'Engels' like 'angels'") and it will add a respelling.

Write numbers and acronyms the way they should be *spoken* if the voice gets them wrong.

### Step 7: Narrate and time it

When you're happy with the words:

```text
Looks good. Run sync to narrate it, then show me the status.
```

Claude runs the narration step. The first time, it downloads voice models (about 1–2 GB) and takes a
few minutes. After that, it only re-narrates paragraphs you've changed.

The status table shows how long each scene is. If the total is over 60 seconds, ask Claude to trim.

### Step 8: Design the scenes

Ask Claude to design each scene, one at a time or all together:

```text
Now design the scenes in the house style. Keep everything inside the safe areas for a reel.
```

Then **look at the result**. Either:

- ask Claude to **take snapshots** ("Show me a frame from each scene"), or
- open the **live preview** yourself. Type `! uv run studio preview <name>` at the prompt (the `!`
  runs the command for you). A browser tab opens where you can play the video with narration. Press
  `Ctrl+C` in the terminal when you're done.

Give feedback in plain language, exactly as you would to a designer:

- "The headline is too small on a phone."
- "Show the number 72 big, and only turn it red when she says 'days'."
- "Add a photo of the barricade, full-screen behind the text, credit it as Wikimedia Commons."
- "Too much text at once. Show one line at a time."

### Step 9: Add images or footage (optional)

Put your files in the episode's `assets/media/` folder (Claude can tell you the exact path), then
say: "Use `barricade.jpg` behind scene 2."

Always give a **credit line** for every photo, quote and figure. The studio's house style expects it.
Only use material you have the right to use.

### Step 10: Add music (optional)

If you have an ElevenLabs key, ask Claude: "Generate a quiet, instrumental piano bed and add it under
the voice." The studio lowers the music automatically whenever the voice speaks. You can also supply
your own music file, as long as you have the licence for it.

### Step 11: Check, then render

```text
Run the check and fix anything it reports. Then render a draft.
```

- **check** is an automatic proofreader: it finds text running off the screen, unreadable colours and
  broken files. It must report **0 errors** before the final render.
- **A draft render** is a quick, lower-quality copy for reviewing. It's saved in the `out/` folder as
  `<name>-draft.mp4`.

Watch the draft on your computer, ideally **on your phone too**. To find the file, open the `out` folder in the studio folder (on Windows, type `explorer out`; on macOS, `open out`; on Linux, `xdg-open out`), then email it to yourself, use a cloud drive, or plug in your phone. Phone screens are where
the problems show: text under your thumb, captions hidden by the app's buttons.

When you're happy:

```text
Render the final version.
```

You'll find the finished video at `out/<name>.mp4`, with a captions file `out/<name>.srt` beside it.

### Step 12: Upload

Upload the MP4 from your phone or computer to Instagram, TikTok or YouTube Shorts as you would any
video. Because the captions are already burned into the picture, you don't need to add them again.
Write your own post caption and hashtags in the app.

---

## 5. The safe-zone rule (why your text isn't hidden)

Each platform lays buttons over the video: like and share buttons down the right side, your caption
and username along the bottom. The studio already keeps content inside a "safe box" for this. The
rough layout, from the top of the screen:

| Area | What goes there |
| --- | --- |
| Top ~220px | Left empty |
| Middle (to about y 1180) | **Your content**: headlines, quotes, numbers |
| About y 1220–1440 | **Captions** (the highlighted spoken words) |
| Bottom ~480px | Left clear for the platform's own caption and buttons |

If something looks cramped, say so and let Claude fix it. You don't need to calculate anything.

---

## 6. Tips for reels that work

- **Win the first second.** Put the most striking fact on screen immediately.
- **One idea per screen.** If you have two points, use two scenes.
- **Change something every 3–6 seconds**: a new line, image or number, in time with the voice.
- **Keep sentences short.** They sound better in a synthetic voice and read better as captions.
- **Make it work with the sound off.** Most people watch muted, and the burned-in captions are your
  voice.
- **Be specific.** "A 40% cut" beats "a big cut".
- **Credit your sources** on screen.

---

## 7. Everyday commands (cheat sheet)

You can ask Claude to run any of these for you, or run them yourself by typing `!` first. `<name>` is
your episode's folder name.

| What you want | Command |
| --- | --- |
| Start a new reel project | `uv run studio new <name> "Title"` |
| Narrate and time the script | `uv run studio sync <name>` |
| See lengths and word counts | `uv run studio status <name>` |
| Watch it in the browser | `uv run studio preview <name>` |
| Run the proofreader | `uv run studio check <name>` |
| Quick draft video | `uv run studio render <name> --draft` |
| Final video | `uv run studio render <name>` |
| Try other narrator voices | `uv run studio voices <name>` |

Useful things to type in Claude Code itself:

| Type | What it does |
| --- | --- |
| `/exit` | Leave Claude Code |
| `/clear` | Start a fresh conversation (your files are kept) |
| `/help` | Show help |
| `Esc` | Interrupt Claude if it is going the wrong way |

---

## 8. If something goes wrong

| Problem | What to try |
| --- | --- |
| `claude`, `uv` or `studio` is "not recognized" / "command not found" | Close and reopen the terminal. If it persists, repeat the install step |
| PowerShell says "running scripts is disabled" | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again |
| Claude Code says you need a plan | Claude Code needs a paid plan or API credit (see section 2) |
| Downloads fail with DNS errors | Pause any VPN and try again. On Linux with "signature-expired" errors, run `resolvectl flush-caches` |
| `check` reports errors | Tell Claude "fix the check errors". It reads the report and edits the scenes |
| The voice mispronounces a word | Tell Claude the word and how it should sound |
| Captions or text hidden behind app buttons | Tell Claude "keep this inside the reel safe area" |
| The render seems stuck | Wait a couple of minutes. Scenes render one at a time. If it is still stuck, ask Claude to look at the render logs |
| Preview doesn't open a browser | Copy the `http://localhost:…` address it prints and paste it into your browser |
| Render hangs, or frames come out empty | Tell Claude: "the render hangs, try without browser GPU capture". |
| Unsure what to do | Ask Claude: "Where are we, and what's the next step?" |

More detail lives in [Troubleshooting](troubleshooting.md).

You can't easily break anything. The script is the source of truth, and the video can always be
regenerated from it. If you're worried about losing work, ask Claude to "commit this to git", which
saves a snapshot you can return to.

---

## 9. Where to learn more

- [Reels (9:16)](reels.md): the technical reel specification (sizes and layout)
- [Writing a script](script.md): everything you can put in a script
- [Narration](narration.md): voices, including the ElevenLabs narrator
- [Working with a coding agent](coding-agents.md): more on working with Claude Code
- [`brand/frame.md`](https://github.com/JoeMountWSWS/explainer-studio/blob/main/brand/frame.md): the house style
- [`episodes/demo-paris-commune/`](https://github.com/JoeMountWSWS/explainer-studio/tree/main/episodes/demo-paris-commune): a finished example to look at

Once you've made one reel, the second takes a fraction of the time: the setup is done, the style is
shared, and you only need to bring an idea and a script.
