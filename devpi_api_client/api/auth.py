import logging
from typing import Optional

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.api.token import Token

logger = logging.getLogger(__name__)


class Auth(DevApiBase):
    """
    Authentication API client for devpi server.

    Provides methods for username/password and token-based authentication.
    Accessed via ``client.auth``.
    """

    def user(self, username: str, password: str) -> None:
        """
        Authenticate using username and password.

        :param username: Username for authentication (must be non-empty)
        :param password: Password for authentication (must be non-empty)
        :raises ValidationError: If username or password is empty
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("password", password)

        self._basic_auth(username, password)
        logger.info(f"Successfully authenticated user: {username}")

    def token(self, token: str) -> None:
        """
        Authenticate using an API token.

        :param token: API token for authentication (must be non-empty)
        :raises ValidationError: If token is empty
        """
        validate_non_empty_string("token", token)

        self._client.session.auth = ("__token__", token)
        logger.info("Successfully authenticated with token")

    def logout(self) -> None:
        """
        Clear authentication credentials from the session.
        """
        self._client.session.auth = None
        logger.info("Successfully logged out - cleared authentication credentials")

    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.

        :return: True if authentication credentials are set, False otherwise
        """
        return self._client.session.auth is not None

    def get_current_user(self) -> Optional[str]:
        """
        Get the currently authenticated username.

        :return: Username when using password authentication. Returns None for token auth or if not
            authenticated.
        """
        auth = self._client.session.auth
        if auth and isinstance(auth, tuple):
            username, secret = auth
            if username == '__token__':
                token = Token.inspect(secret)
                return token.user
            return str(username)
        return None

    def _basic_auth(self, username: str, password: str) -> None:
        """
        Set basic authentication credentials on the session.

        :param username: Username for authentication
        :param password: Password for authentication
        """
        self._client.session.auth = (username, password)
