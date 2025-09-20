"""
Devpi API Client - Python client library for devpi server API.

This package provides a comprehensive Python client for interacting with
devpi servers, including user management, index operations, project management,
and authentication.
"""

from devpi_api_client.exceptions import (
    AuthenticationError,
    ConflictError,
    DevpiApiError,
    NetworkError,
    NotFoundError,
    PermissionError,
    ResponseParsingError,
    ServerError,
    ValidationError,
)
from devpi_api_client.v1 import Client
from devpi_api_client.version import __version__

# Main client class
__all__ = [
    "Client",
    "__version__",
    # Exceptions
    "DevpiApiError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "PermissionError",
    "ConflictError",
    "ServerError",
    "NetworkError",
    "ResponseParsingError",
]
