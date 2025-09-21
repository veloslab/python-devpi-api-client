import logging
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from devpi_api_client.exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    ResponseParsingError,
    ServerError,
    ValidationError,
)
from devpi_api_client.exceptions import (
    PermissionError as DevpiPermissionError,
)

if TYPE_CHECKING:
    from devpi_api_client.v1 import Client

logger = logging.getLogger(__name__)


def validate_non_empty_string(name: str, value: Any) -> None:
    """
    Validate that a parameter is a non-empty string.

    :param name: Parameter name for error messages
    :param value: Value to validate
    :raises ValidationError: If value is not a non-empty string
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Parameter '{name}' must be a non-empty string")


class DevApiBase:
    """
    Base class for all devpi API sub-clients.

    Provides common functionality including request handling, error management,
    and parameter validation.

    :param client: An instance of the main DevpiClient
    """

    def __init__(self, client: 'Client') -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        return_json: bool = True,
        **kwargs: Any
    ) -> Any:
        """
        Make an HTTP request to the devpi server with comprehensive error handling.

        :param method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        :param path: API endpoint path
        :param return_json: Whether to parse response as JSON
        :param kwargs: Additional arguments passed to requests
        :return: Response data or Response object
        :raises: Various DevpiApiError subclasses based on error type
        """
        url = urljoin(self._client.base_url, path)
        response = None

        try:
            logger.debug(f"Making {method} request to {url}")
            timeout = kwargs.get('timeout')
            if timeout is None:
                client_timeout = getattr(self._client, '_default_timeout', None)
                if isinstance(client_timeout, (int, float)):
                    kwargs.setdefault('timeout', client_timeout)

            response = self._client.session.request(url=url, method=method, **kwargs)

            # Handle HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your credentials.",
                    status_code=response.status_code,
                    response_data=self._safe_json_parse(response)
                )
            elif response.status_code == 403:
                raise DevpiPermissionError(
                    "Access forbidden. Insufficient permissions.",
                    status_code=response.status_code,
                    response_data=self._safe_json_parse(response)
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found at {path}",
                    status_code=response.status_code,
                    response_data=self._safe_json_parse(response)
                )
            elif response.status_code == 409:
                raise ConflictError(
                    "Conflict - resource may already exist or be in an invalid state",
                    status_code=response.status_code,
                    response_data=self._safe_json_parse(response)
                )
            elif 500 <= response.status_code < 600:
                raise ServerError(
                    f"Server error (HTTP {response.status_code})",
                    status_code=response.status_code,
                    response_data=self._safe_json_parse(response)
                )

            # Raise for other HTTP errors
            response.raise_for_status()

            logger.debug(f"{method} request to {path} succeeded")

            if return_json:
                try:
                    return response.json()
                except ValueError as e:
                    raise ResponseParsingError(f"Failed to parse JSON response: {e}") from e
            else:
                return response

        except (ConnectionError, Timeout) as e:
            raise NetworkError(f"Network error while connecting to {url}: {e}") from e
        except HTTPError as e:
            # This should be caught by our specific status code handling above,
            # but included as a fallback
            error_data = self._safe_json_parse(response) if response else None
            raise ServerError(
                f"HTTP error: {e}",
                status_code=response.status_code if response else None,
                response_data=error_data
            ) from e
        except RequestException as e:
            raise NetworkError(f"Request failed: {e}") from e

    def _safe_json_parse(self, response: requests.Response) -> Optional[Any]:
        """
        Safely parse JSON from response, returning None if parsing fails.

        :param response: HTTP response object
        :return: Parsed JSON data or None
        """
        try:
            return response.json()
        except (ValueError, AttributeError):
            return None
