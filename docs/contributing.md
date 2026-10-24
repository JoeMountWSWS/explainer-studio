# Contributing

## Layout

| Path | What it is |
| --- | --- |
| `tools/studio/` | The Python CLI |
| `brand/` | House style: design spec, CSS, fonts, GSAP, pronunciations |
| `templates/` | Starter script, scene patterns and thumbnail |
| `episodes/<slug>/` | One HyperFrames project per video |
| `docs/` | This site |

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

- `uv sync --locked`, `ruff check tools/`, and a CLI smoke test (`status` on every episode, plus
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
