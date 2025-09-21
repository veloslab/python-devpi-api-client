# devpi_api_client/exceptions.py

"""
Custom exceptions for the devpi API client.
"""

from typing import Optional


class DevpiApiError(Exception):
    """Base exception for all devpi API client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(DevpiApiError):
    """Raised when authentication fails."""
    pass


class ValidationError(DevpiApiError):
    """Raised when input validation fails."""
    pass


class NotFoundError(DevpiApiError):
    """Raised when a resource is not found (404)."""
    pass


class PermissionError(DevpiApiError):
    """Raised when access is forbidden (403)."""
    pass


class ConflictError(DevpiApiError):
    """Raised when there's a conflict (409) - e.g., resource already exists."""
    pass


class ServerError(DevpiApiError):
    """Raised when the server returns a 5xx error."""
    pass


class NetworkError(DevpiApiError):
    """Raised when network communication fails."""
    pass


class ResponseParsingError(DevpiApiError):
    """Raised when response parsing fails."""
    pass
