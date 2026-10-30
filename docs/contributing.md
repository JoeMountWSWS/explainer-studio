# Contributing

## Get involved

Start with an issue, so we can agree on the approach before you write code:

| You want to… | Open |
| --- | --- |
| Report a `studio` command that fails, crashes or produces the wrong output | [Bug report](https://github.com/JoeMountWSWS/explainer-studio/issues/new?template=bug_report.yml) |
| Suggest a new command, setting, scene template or house-style change | [Feature request](https://github.com/JoeMountWSWS/explainer-studio/issues/new?template=feature_request.yml) |
| Ask a question or raise anything else | [Blank issue](https://github.com/JoeMountWSWS/explainer-studio/issues/new) |

Or [pick from every template](https://github.com/JoeMountWSWS/explainer-studio/issues/new/choose).
Check [Troubleshooting](troubleshooting.md) and the
[open issues](https://github.com/JoeMountWSWS/explainer-studio/issues) first. To fix something
yourself, fork the repository, branch from `main` and open a
[pull request](https://github.com/JoeMountWSWS/explainer-studio/pulls). Use the commit prefixes
[below](#commit-messages-and-releases), and make sure CI passes.

## Layout

| Path | What it is |
| --- | --- |
| `tools/studio/` | The Python CLI |
| `tests/` | pytest suite for the CLI |
| `brand/` | House style: design spec, CSS, fonts, GSAP, pronunciations |
| `templates/` | Starter script, scene patterns and thumbnail |
| `episodes/<slug>/` | One HyperFrames project per video |
| `docs/` | This site |

## Tests

```bash
uv run pytest                                    # all tests, with a coverage table
uv run pytest --cov-report=html                  # browsable report in htmlcov/index.html
uv run pytest tests/test_script.py -k pause      # one file, or tests matching a name
```

The suite needs no TTS model or HyperFrames: narration goes through a fake engine
(`fake_tts` in `tests/conftest.py`), transcripts are stubbed, and scene renders are stubbed. The
`mix` tests run real ffmpeg, mastering a test tone and measuring that it lands on the loudness target;
they skip when ffmpeg isn't installed (CI installs it). Paths in
`studio.common` are fixed at import time, so tests that write files point the module attributes
they use at `tmp_path` with `monkeypatch`. `test_demo_episode_timing_is_reproducible` checks that
the committed `episodes/demo-paris-commune/timing.json` still follows from its script and
narration, so a change to timing maths shows up as a failing test, not a silently re-timed video.

Coverage settings are under `[tool.coverage]` in `pyproject.toml`. The run fails below the
`fail_under` floor; raise it as coverage grows.

## Documentation site

The site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) from `docs/`
and `mkdocs.yml`, and published to GitHub Pages by `.github/workflows/docs.yml` on every push to
`main` that touches them.

```bash
uvx --with mkdocs-material==9.7.7 mkdocs serve    # live preview at http://127.0.0.1:8000
uvx --with mkdocs-material==9.7.7 mkdocs build    # strict build into ./site
```

The build is strict, so broken links fail it. In the repository settings, set **Pages → Source** to
**GitHub Actions** once.

## CI

[`ci.yml`](https://github.com/JoeMountWSWS/explainer-studio/blob/main/.github/workflows/ci.yml) runs
on every push to `main` and every pull request:

- `pytest` with coverage on Python 3.12 and 3.13; the coverage table goes in the run's summary,
  and `coverage.xml` plus the HTML report are uploaded as the `coverage` artifact. On pull requests
  from this repository, [python-coverage-comment-action](https://github.com/py-cov-action/python-coverage-comment-action)
  posts one comment with the total and the coverage of the changed lines (updated on each push), and
  pushes to `main` refresh the README badge, stored on the `python-coverage-comment-action-data` branch
- `uv sync --locked`, `ruff check tools/ tests/`, and a CLI smoke test (`status` on every episode, plus
  `new`)
- `hyperframes check` on every episode, at the pinned HyperFrames version

CI never narrates or renders, so commit `audio/vo/`, `timing.json` and `index.html` after `sync`.

## Commit messages and releases

[release-please](https://github.com/googleapis/release-please) reads
[Conventional Commit](https://www.conventionalcommits.org/) messages on `main` and keeps a release PR
open that bumps the version in `pyproject.toml` and `uv.lock` and updates `CHANGELOG.md`. Merging it
tags `vX.Y.Z` and publishes a GitHub release. Never hand-edit the version or the changelog.

| Prefix | Changelog section | Bump (while < 1.0) |
| --- | --- | --- |
| `feat:` | Features | patch |
| `fix:`, `perf:` | Bug fixes, Performance | patch |
| `episode:`, `brand:`, `docs:`, `deps:` | Episodes, House style, Documentation, Dependencies | patch |
| `refactor:`, `test:`, `ci:`, `chore:` | hidden | none |
| `feat!:` or a `BREAKING CHANGE:` footer | | minor |

The repository needs **Settings → Actions → General → Allow GitHub Actions to create and approve pull
requests** turned on. Release PRs opened with the default token don't trigger CI; close and reopen
the PR to run checks before merging.

## Upgrading HyperFrames

Bump `HF_VERSION` in `tools/studio/common.py`, run `studio check` on an episode, and compare a draft
render.

## Licence

The studio software is released under the [MIT licence](https://github.com/JoeMountWSWS/explainer-studio/blob/main/LICENSE).
Editorial content (everything under `episodes/` and `scripts/`) is © World Socialist Web Site, all
rights reserved. Fonts (SIL OFL 1.1), GSAP (GreenSock Standard License) and third-party photographs
keep their own terms.
