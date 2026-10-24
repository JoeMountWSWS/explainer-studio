# Releasing

[release-please](https://github.com/googleapis/release-please)
([`.github/workflows/release-please.yml`](.github/workflows/release-please.yml)) reads the
[Conventional Commit](https://www.conventionalcommits.org/) messages on `main` and keeps a release
PR open that bumps the version in `pyproject.toml` and `uv.lock` and updates `CHANGELOG.md`.
Merging it tags `vX.Y.Z` and publishes a GitHub release.

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
