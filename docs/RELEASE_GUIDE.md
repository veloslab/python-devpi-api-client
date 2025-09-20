# Documentation & Release Playbook

## Documentation Workflow
- All public guides live under `docs/`; mirror the package layout (for example `docs/user/`) so code snippets stay close to the modules they describe.
- `mkdocs.yml` defines the nav and uses the Material theme. Update it whenever new pages are added so the sidebar stays in sync.
- Preview docs locally with `poetry run mkdocs serve`; enforce link and formatting checks via `poetry run mkdocs build --strict` before committing.
- Treat `docs/index.md` as the landing page. Ensure it links to the release playbook and task-specific guides like token management or package uploads.
- CI already runs `mkdocs build --strict` (see `.github/workflows/ci.yml`), so fix any doc failures before merging.

## Publishing to PyPI with GitHub Actions
- Generate a PyPI API token (`__token__` scope) and store it as the repository secret `PYPI_API_TOKEN`.
- Bump the version via Poetry (`poetry version patch|minor|major`), update the changelog, and commit before tagging.
- The tag-triggered workflow in `.github/workflows/publish.yml` reruns tests, lint checks, type checks, and the docs build before executing `poetry build` and `poetry publish`. Ensure the `PYPI_API_TOKEN` secret is present or the job will fail.
- For pre-release smoke tests, append `--repository testpypi` and store a `TEST_PYPI_API_TOKEN` secret; only swap to the production token when the package looks good.
- Keep CI green before tagging: `ci.yml` already runs pytest across Python 3.9/3.11/3.13 plus Ruff, Mypy, and MkDocs. Mirror those commands locally (`poetry run pytest`, `poetry run ruff check .`, `poetry run mypy devpi_api_client`, `poetry run mkdocs build --strict`).
- After upload, verify the release by installing it in a clean environment (`pip install devpi-api-client==<version>`) and spot-check the README rendering on PyPI (uses Markdown).

## Release Checklist
- [ ] Tests pass (`poetry run pytest`).
- [ ] Docs build cleanly (`poetry run mkdocs build --strict`).
- [ ] Version bumped in `pyproject.toml` via Poetry.
- [ ] `CHANGELOG.md` (or release notes) updated.
- [ ] Tag pushed (`git tag vX.Y.Z && git push --tags`).
- [ ] GitHub Action run succeeded and package installs from PyPI.
