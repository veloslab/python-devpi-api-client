import logging
from types import TracebackType
from typing import Any, Optional, Union, cast

import requests

from devpi_api_client.api import Auth, Index, Project, Token, User
from devpi_api_client.api.base import DevApiBase
from devpi_api_client.exceptions import ValidationError
from devpi_api_client.version import __version__

logger = logging.getLogger(__name__)


class Client:
    """
    Main devpi API client providing access to all devpi server functionality.

    This client provides namespaced sub-clients for different aspects of devpi
    server management including users, indexes, projects/packages, tokens, and authentication.

    Example usage:
        client = Client("http://localhost:3141", user="admin", password="secret")
        users = client.user.list()
        client.user.create("newuser", "password123")
    """

    def __init__(
        self,
        base_url: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        verify: Optional[Union[bool, str]] = True,
        timeout: Optional[float] = 30.0,
    ) -> None:
        """
        Initialize the devpi API client.

        :param base_url: Base URL of the devpi server (e.g., http://localhost:3141)
        :param user: Username for password-based authentication
        :param password: Password for password-based authentication
        :param token: Authentication token (takes precedence over user/password)
        :param verify: SSL certificate verification (True/False or path to CA bundle)
        :param timeout: Request timeout in seconds
        :raises ValidationError: If base_url is empty or invalid authentication parameters
        """
        if not base_url or not base_url.strip():
            raise ValidationError("base_url cannot be empty")

        # Ensure base_url is properly formatted
        base_url = base_url.strip()
        if not base_url.startswith(('http://', 'https://')):
            raise ValidationError("base_url must start with http:// or https://")

        self.base_url = base_url.rstrip('/')

        # Configure session
        self.session = requests.Session()
        if timeout is not None:
            try:
                timeout_value = float(timeout)
            except (TypeError, ValueError) as exc:
                raise ValidationError("timeout must be a numeric value") from exc
            if timeout_value <= 0:
                raise ValidationError("timeout must be greater than 0 seconds")
            timeout = timeout_value

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": f"devpi-api-client/{__version__}"
        })
        self.session.verify = verify
        self._default_timeout = timeout
        self._core_api = DevApiBase(self)

        # Initialize API sub-clients
        self.auth = Auth(self)
        self.user = User(self)
        self.index = Index(self)
        self.project = Project(self)
        self.package = self.project  # Alias for backward compatibility
        self.token = Token(self)

        # Handle authentication
        username_value = user.strip() if isinstance(user, str) and user.strip() else None
        password_value = password.strip() if isinstance(password, str) and password.strip() else None

        if token:
            self.auth.token(token)
        elif username_value is not None and password_value is not None:
            self.auth.user(username_value, password_value)
        elif user is not None or password is not None:
            raise ValidationError("Both username and password must be provided for password authentication")

        logger.info(f"Initialized devpi client for {self.base_url}")

    def close(self) -> None:
        """
        Close the HTTP session to free up resources.
        """
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("Closed devpi client session")

    def __enter__(self) -> "Client":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Context manager exit - close session."""
        self.close()

    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.

        :return: True if authenticated, False otherwise
        """
        return self.auth.is_authenticated()

    def get_server_info(self) -> dict[str, Any]:
        """
        Get basic server information by making a request to the root endpoint.

        :return: Dictionary containing server information
        :raises DevpiApiError: For API errors
        """
        logger.debug("Retrieving server information")
        result = self._core_api._request('GET', '/')
        return cast(dict[str, Any], result)
