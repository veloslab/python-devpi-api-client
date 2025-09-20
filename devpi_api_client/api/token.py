import datetime
import logging
from typing import Any, Optional, cast

import pymacaroons

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.exceptions import NotFoundError, ValidationError
from devpi_api_client.models.base import DeleteResponse
from devpi_api_client.models.token import TokenInfo, TokenList

logger = logging.getLogger(__name__)


class Token(DevApiBase):
    """
    Token API client for devpi server token management.

    This class provides methods to create, list, delete, and inspect user
    API tokens. It interacts with the ``devpi-tokens`` plugin on the server.
    The `inspect` method operates client-side using the `pymacaroons` library.

    Accessed via ``client.token``.
    """

    public_permissions = {
        'del_entry', 'del_project', 'del_verdata', 'index_create',
        'index_delete', 'index_modify', 'pkg_read', 'toxresult_upload', 'upload'
    }
    hidden_permissions = {
        'user_create', 'user_delete', 'user_login', 'user_modify'
    }
    known_permissions = public_permissions.union(hidden_permissions)


    def _validate_permissions(self, permissions: Optional[list[str]]) -> Optional[list[str]]:
        """
        Validate a list of permissions against the known set.

        :param permissions: A list of permission strings to validate
        :return: A sorted list of unique, valid permission strings
        :raises ValidationError: If any permission is invalid or unknown
        """
        if permissions is None:
            return None

        if not isinstance(permissions, list):
            raise ValidationError("Permissions must be provided as a list")

        cleaned_permissions = []
        for perm in permissions:
            if not isinstance(perm, str) or not perm.strip():
                raise ValidationError(f"Invalid permission '{perm}': must be a non-empty string")
            cleaned_permissions.append(perm.strip())

        unknown = [p for p in cleaned_permissions if p not in self.known_permissions]
        if unknown:
            valid = ', '.join(sorted(self.public_permissions))
            raise ValidationError(
                f"Unknown permissions: {', '.join(unknown)}. Valid permissions: {valid}"
            )

        return sorted(list(set(cleaned_permissions)))

    def create(
            self,
            username: str,
            allowed: Optional[list[str]] = None,
            expires_in_seconds: Optional[int] = None,
            indexes: Optional[list[str]] = None,
            projects: Optional[list[str]] = None,
    ) -> str:
        """
        Create a new authentication token for a specified user.

        :param username: Username for whom the token will be created (must be non-empty)
        :param allowed: List of permissions to grant the token (e.g., 'pkg_read', 'upload')
        :param expires_in_seconds: Duration in seconds for which the token will be valid
        :param indexes: List of indexes to which the token should be restricted
        :param projects: List of projects to which the token should be restricted
        :return: The new token secret string
        :raises ValidationError: If username is invalid or permissions are unknown
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        validated_allowed = self._validate_permissions(allowed)

        # Validate expires_in_seconds if provided
        if expires_in_seconds is not None:
            if not isinstance(expires_in_seconds, int) or expires_in_seconds <= 0:
                raise ValidationError("expires_in_seconds must be a positive integer")

        path = f"/{username}/+token-create"
        payload: dict[str, Any] = {}

        if validated_allowed:
            payload["allowed"] = validated_allowed
        if expires_in_seconds is not None:
            expires_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
                seconds=expires_in_seconds
            )
            payload["expires"] = int(expires_at.timestamp())
        if indexes:
            payload["indexes"] = indexes
        if projects:
            payload["projects"] = projects

        logger.info(f"Creating new token for user: {username}")
        response_data = self._request('POST', path, json=payload)

        if 'result' not in response_data or 'token' not in response_data['result']:
            raise ValueError("Unexpected response format when creating token")

        return cast(str, response_data['result']['token'])

    def list(self, user: str) -> dict[str, TokenInfo]:
        """
        List and parse all authentication tokens for a specified user.

        :param user: Username whose tokens to list (must be non-empty)
        :return: Dictionary mapping token IDs to TokenInfo objects
        :raises ValidationError: If user is empty
        :raises DevpiApiError: For API errors
        """
        validate_non_empty_string("user", user)
        path = f"/{user}/+tokens"

        logger.debug(f"Listing tokens for user: {user}")
        response_data = self._request('GET', path)

        if response_data:
            token_list = TokenList.model_validate(response_data, context={'user': user})
            return token_list.result.tokens

        # If we get here without an exception, return empty dict
        return {}

    def delete(self, username: str, token_id: str) -> DeleteResponse:
        """
        Delete a specific authentication token.

        :param username: Username who owns the token (must be non-empty)
        :param token_id: Unique ID of the token to delete (not the secret)
        :return: DeleteResponse confirming the deletion
        :raises ValidationError: If username or token_id is empty
        :raises NotFoundError: If token does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("token_id", token_id)
        path = f"/{username}/+tokens/{token_id}"

        logger.info(f"Deleting token '{token_id}' for user '{username}'")
        response_data = self._request('DELETE', path)

        return DeleteResponse.model_validate(response_data)

    @staticmethod
    def inspect(token: str) -> TokenInfo:
        """
        Inspect a token to reveal its contents without server contact (client-side operation).

        :param token: The devpi token string to inspect (must be non-empty)
        :return: TokenInfo containing the token's decoded data
        :raises ValidationError: If token is empty or invalid format
        :raises ValueError: If token cannot be parsed
        """
        validate_non_empty_string("token", token)

        # Remove devpi- prefix if present
        token_data = token[6:] if token.startswith("devpi-") else token

        try:
            macaroon = pymacaroons.Macaroon.deserialize(token_data)
            identifier = macaroon.identifier.decode("ascii")

            # Split user and token_id
            parts = identifier.rsplit('-', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid token identifier format: {identifier}")

            user, token_id = parts
            restrictions = [caveat.to_dict()['cid'] for caveat in macaroon.caveats]

            return TokenInfo(user=user, id=token_id, restrictions=restrictions)

        except Exception as e:
            raise ValueError(f"Failed to parse token: {e}") from e

    def exists(self, username: str, token_id: str) -> bool:
        """
        Check if a specific token exists for a user.

        :param username: Username who owns the token (must be non-empty)
        :param token_id: Unique ID of the token to check
        :return: True if token exists, False otherwise
        :raises ValidationError: If username or token_id is empty
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("token_id", token_id)

        try:
            tokens = self.list(username)
            return token_id in tokens
        except NotFoundError:
            return False
