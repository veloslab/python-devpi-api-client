import datetime
import pymacaroons
from typing import Any, Dict, List, Optional

from devpi_api_client.api.base import DevApiBase, logger
from devpi_api_client.models.token import (
    TokenInfo,
    TokenList
)
from devpi_api_client.models.base import DeleteResponse


class Token(DevApiBase):
    """
    Manages API tokens for users on a devpi server.

    This class provides methods to create, list, delete, derive, and inspect user
    API tokens. It interacts with the ``devpi-tokens`` plugin on the server. The
    `derive` and `inspect` methods operate client-side and require the
    `pymacaroons` library.

    Access these methods via ``client.token``.
    """

    public_permissions = {
        'del_entry', 'del_project', 'del_verdata', 'index_create',
        'index_delete', 'index_modify', 'pkg_read', 'toxresult_upload', 'upload'
    }
    hidden_permissions = {
        'user_create', 'user_delete', 'user_login', 'user_modify'
    }
    known_permissions = public_permissions.union(hidden_permissions)

    @staticmethod
    def _validate_non_empty_param(name: str, value: Any) -> None:
        """Raise ValueError if a parameter is not a non-blank string."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Parameter '{name}' must be a non-empty string.")

    def _validate_permissions(self, permissions: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validates a list of permissions against the known set.

        :param permissions: A list of permission strings to validate.
        :return: A sorted list of unique, valid permission strings.
        :raises ValueError: If any permission is invalid or unknown.
        """
        if permissions is None:
            return None

        cleaned_permissions = []
        for perm in permissions:
            if not isinstance(perm, str) or not perm.strip():
                raise ValueError(f"Invalid permission '{perm}': must be a non-empty string.")
            cleaned_permissions.append(perm.strip())

        unknown = [p for p in cleaned_permissions if p not in self.known_permissions]
        if unknown:
            raise ValueError(f"Unknown permissions provided: {', '.join(unknown)}")

        return sorted(list(set(cleaned_permissions)))

    def create(
            self,
            username: str,
            allowed: Optional[List[str]] = None,
            expires_in_seconds: Optional[int] = None,
            indexes: Optional[List[str]] = None,
            projects: Optional[List[str]] = None,
    ) -> str:
        """
        Creates a new authentication token for a specified user.

        :param username: The user for whom the token will be created.
        :param allowed: A list of permissions to grant the token (e.g., 'pkg_read', 'upload').
        :param expires_in_seconds: The duration, in seconds, for which the token will be valid.
        :param indexes: A list of indexes to which the token should be restricted.
        :param projects: A list of projects to which the token should be restricted.
        :return: A ``TokenCreateResponse`` model containing the new token secret, or ``None`` if the request fails.
        :raises ValueError: If ``username`` is invalid or if any provided permissions are unknown.
        """
        self._validate_non_empty_param("username", username)
        validated_allowed = self._validate_permissions(allowed)

        path = f"/{username}/+token-create"

        payload: Dict[str, Any] = {}
        if validated_allowed:
            payload["allowed"] = validated_allowed
        if expires_in_seconds is not None:
            expires_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
                seconds=expires_in_seconds)
            payload["expires"] = int(expires_at.timestamp())
        if indexes:
            payload["indexes"] = indexes
        if projects:
            payload["projects"] = projects

        logger.info(f"Requesting creation of a new token for user '{username}'")
        response_data = self._request('POST', path, json=payload)
        return response_data['result']['token']

    def list(self, user: str) -> dict[str, TokenInfo]:
        """
        Lists and parses all authentication tokens for a specified user.

        :param user: The user whose tokens to list.
        :return: A ``TokenListResponse`` model containing fully parsed token data, or ``None`` if the request fails or the user has no tokens.
        """
        self._validate_non_empty_param("user", user)
        path = f"/{user}/+tokens"
        response_data = self._request('GET', path)

        if response_data:
            return TokenList.model_validate(response_data,  context={'user': user}).result.tokens

        return None

    def delete(self, username: str, token_id: str):
        """
        Deletes a specific authentication token.

        :param username: The user who owns the token.
        :param token_id: The unique ID of the token to delete (not the secret).
        """
        self._validate_non_empty_param("username", username)
        self._validate_non_empty_param("token_id", token_id)
        path = f"/{username}/+tokens/{token_id}"

        logger.info(f"Requesting deletion of token '{token_id}' for user '{username}'")
        response_data = self._request('DELETE', path)

        return DeleteResponse.model_validate(response_data)

    def inspect(self, token: str) -> TokenInfo:
        """
        Inspects a token to reveal its contents without server contact (client-side operation).

        :param token: The devpi token string to inspect.
        :return: An ``InspectTokenInfo`` model containing the token's decoded data.
        """
        if token.startswith("devpi-"):
            token = token[6:]

        macaroon = pymacaroons.Macaroon.deserialize(token)
        user, token_id = macaroon.identifier.decode("ascii").rsplit('-', 1)

        restrictions = [caveat.to_dict()['cid'] for caveat in macaroon.caveats]
        return TokenInfo(user=user, id=token_id, restrictions=restrictions)
