# Releasing

[release-please](https://github.com/googleapis/release-please)
([`.github/workflows/release-please.yml`](.github/workflows/release-please.yml)) reads the
[Conventional Commit](https://www.conventionalcommits.org/) messages on `main` and keeps a release
PR open that bumps the version in `pyproject.toml` and `uv.lock` and updates `CHANGELOG.md`.
Merging it tags `vX.Y.Z`, publishes a GitHub release with the source bundle attached (the repo without the non-demo
episodes and music beds, which are `export-ignore` in `.gitattributes` and live in Git LFS), and uploads
the wheel and sdist to [PyPI](https://pypi.org/project/explainer-studio/).

| Prefix | Changelog section | Bump (while < 1.0) |
| --- | --- | --- |
| `feat:` | Features | patch |
| `fix:`, `perf:` | Bug fixes, Performance | patch |
| `episode:`, `brand:`, `docs:`, `deps:` | Episodes, House style, Documentation, Dependencies | patch |
| `refactor:`, `test:`, `ci:`, `chore:` | hidden | none |
| `feat!:` or a `BREAKING CHANGE:` footer | | minor |

The repository needs **Settings → Actions → General → Allow GitHub Actions to create and approve
pull requests** turned on. Release PRs opened with the default token don't trigger CI; close and
reopen the PR (or push to its branch) to run checks before merging.

## PyPI

The `pypi` job in `release-please.yml` builds with `uv build`, smoke-tests the wheel in a clean
virtual environment outside the repository, and uploads with
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API token is stored. It needs
a one-time setup on PyPI (a *pending* publisher until the first upload creates the project):

| Field | Value |
| --- | --- |
| PyPI project name | `explainer-studio` |
| Owner | `JoeMountWSWS` |
| Repository name | `explainer-studio` |
| Workflow name | `release-please.yml` |
| Environment name | `pypi` |

The wheel carries `tools/studio` plus the house style (`brand/brand.css`, `frame.md`,
`pronunciations.yaml`, `fonts/`, `vendor/`) and `templates/` as `studio/data/`; music beds, voice
clips and episodes are left out. CI builds and smoke-tests the wheel on every pull request.
