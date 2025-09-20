# Documentation Overview

## Getting Started

- Install: `pip install devpi-api-client`
- Create a client: `Client("https://devpi.example.com", token=os.environ["DEVPI_TOKEN"])`
- Explore API namespaces: `client.user`, `client.index`, `client.project`, `client.token`, `client.auth`.

## Local Development

```bash
pipx install poetry
poetry install --with dev,docs
poetry run pre-commit run --all-files  # if enabled
```

Run tooling before pushing:

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy devpi_api_client
```

## Logging & Configuration

- All modules use the `devpi_api_client` logger; set `logging.getLogger("devpi_api_client").setLevel(logging.DEBUG)` for verbose output.
- Avoid hard-coding credentials. Use environment variables or `.env` files (ignored by git) and pass them into the client.
- For HTTPS devpi instances with private CAs, provide the CA bundle path via the `verify` argument.

## Packaging & Releases

- Follow the release checklist in `docs/RELEASE_GUIDE.md`.
- CI will build docs with `mkdocs build --strict` and publish to PyPI on version tags.
- Validate the published distribution in a clean virtual environment before announcing a release.
