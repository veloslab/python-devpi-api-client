# api/user.py

import logging
from typing import Any, Optional

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.exceptions import NotFoundError, ResponseParsingError, ValidationError
from devpi_api_client.models.user import (
    UserCreateResponse,
    UserDeleteResponse,
    UserInfo,
    UserList,
)

logger = logging.getLogger(__name__)


class User(DevApiBase):
    """
    User API client for devpi server user management.

    Provides methods to create, retrieve, modify, list, and delete users.
    Accessed via ``client.user``.

    All methods handle errors consistently and return typed model instances
    or None for failed operations.
    """

    def create(self, username: str, password: str, email: Optional[str] = None) -> UserInfo:
        """
        Create a new user on the devpi server.

        :param username: Username for the new user (must be non-empty)
        :param password: Password for the new user (must be non-empty)
        :param email: Optional email address for the new user
        :return: UserInfo model confirming creation
        :raises ValidationError: If username or password is empty
        :raises ConflictError: If user already exists
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("password", password)

        path = f"/{username}"
        payload = {"password": password}
        if email and email.strip():
            payload["email"] = email.strip()

        logger.info(f"Creating user: {username}")
        response_data = self._request('PUT', path, json=payload)

        create_response = UserCreateResponse.model_validate(response_data)
        if create_response.result is None:
            raise ResponseParsingError(
                "User creation response missing result payload",
                response_data=response_data,
            )

        return create_response.result

    def get(self, username: str) -> UserInfo:
        """
        Retrieve configuration and index information for a specific user.

        :param username: Username to retrieve (must be non-empty)
        :return: UserInfo model with user details
        :raises ValidationError: If username is empty
        :raises NotFoundError: If user does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        path = f"/{username}"

        logger.debug(f"Retrieving user info: {username}")
        response_data = self._request('GET', path)

        if response_data and 'result' in response_data:
            return UserInfo.model_validate(response_data['result'])

        # If we get here without an exception, the response format is unexpected
        raise ValueError(f"Unexpected response format when retrieving user {username}")

    def delete(self, username: str) -> UserDeleteResponse:
        """
        Delete a user from the devpi server.

        :param username: Username to delete (must be non-empty)
        :return: UserDeleteResponse model confirming deletion
        :raises ValidationError: If username is empty
        :raises NotFoundError: If user does not exist
        :raises PermissionError: If insufficient permissions to delete user
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        path = f"/{username}"

        logger.info(f"Deleting user: {username}")
        response_data = self._request('DELETE', path)
        return UserDeleteResponse.model_validate(response_data)

    def modify(self, username: str, **kwargs: Any) -> UserInfo:
        """
        Modify an existing user's attributes (password, email, etc.).

        :param username: Username to modify (must be non-empty)
        :param kwargs: Key-value pairs to update (e.g., password="new", email="user@example.com")
        :return: UserInfo model with updated user configuration
        :raises ValidationError: If username is empty or no attributes provided
        :raises NotFoundError: If user does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        if not kwargs:
            raise ValidationError("No attributes provided to modify. Use password= or email=")

        # Validate common attributes
        if 'password' in kwargs and not kwargs['password']:
            raise ValidationError("Password cannot be empty")
        if 'email' in kwargs and kwargs['email'] and not kwargs['email'].strip():
            raise ValidationError("Email cannot be empty when provided")

        path = f"/{username}"
        logger.info(f"Modifying user {username} with attributes: {list(kwargs.keys())}")
        self._request('PATCH', path, json=kwargs)

        # Return updated user info
        return self.get(username)

    def list(self) -> dict[str, UserInfo]:
        """
        List all users on the devpi server.

        :return: Dictionary mapping usernames to ``UserInfo`` models
        :raises DevpiApiError: For API errors
        """
        logger.debug("Retrieving list of all users")
        response_data = self._request('GET', "/")
        user_list = UserList.model_validate(response_data)
        return user_list.root

    def exists(self, username: str) -> bool:
        """
        Check if a user exists on the devpi server.

        :param username: Username to check (must be non-empty)
        :return: True if user exists, False otherwise
        :raises ValidationError: If username is empty
        """
        validate_non_empty_string("username", username)
        try:
            self.get(username)
            return True
        except NotFoundError:
            return False

    def change_password(self, username: str, new_password: str) -> UserInfo:
        """
        Change a user's password.

        :param username: Username to modify (must be non-empty)
        :param new_password: New password (must be non-empty)
        :return: UserInfo model with updated user configuration
        :raises ValidationError: If username or password is empty
        :raises NotFoundError: If user does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("new_password", new_password)

        logger.info(f"Changing password for user: {username}")
        return self.modify(username, password=new_password)

    def change_email(self, username: str, new_email: str) -> UserInfo:
        """
        Change a user's email address.

        :param username: Username to modify (must be non-empty)
        :param new_email: New email address (must be non-empty)
        :return: UserInfo model with updated user configuration
        :raises ValidationError: If username or email is empty
        :raises NotFoundError: If user does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("username", username)
        validate_non_empty_string("new_email", new_email)

        logger.info(f"Changing email for user: {username}")
        return self.modify(username, email=new_email)
