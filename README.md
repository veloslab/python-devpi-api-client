# Devpi API Client

Python client for automating user, index, token, and package management on a devpi server.

## Installation

```bash
pip install devpi-api-client
```

To hack on the project locally:

```bash
pip install pipx
pipx install poetry
poetry install --with dev,docs
```

## Quickstart

```python
from devpi_api_client import Client

with Client("https://devpi.example.com", user="root", password="s3cret") as client:
    client.user.create("service", "changeme", email="svc@example.com")
    indexes = client.index.list("service")
    token = client.token.create("service", allowed=["upload"], expires_in_seconds=3600)
```

### Logging

Enable debug logging to observe outgoing requests and error handling:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("devpi_api_client").setLevel(logging.DEBUG)
```

## Documentation

Refer to `docs/index.md` for contributor and operator guides. Build the HTML docs locally:

```bash
poetry run mkdocs serve
```

## Testing

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy devpi_api_client
```

## Release Process

1. Update `CHANGELOG.md` and bump the version with `poetry version <patch|minor|major>`.
2. Commit changes and push a tag like `v0.2.0`.
3. GitHub Actions builds and publishes to PyPI using the workflow described in `docs/RELEASE_GUIDE.md`.

## License

MIT License. See `LICENSE` for full text.
