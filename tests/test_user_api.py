"""
Unit tests for User API client.
"""

from unittest.mock import Mock, patch

import pytest

from devpi_api_client.api.user import User
from devpi_api_client.exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    PermissionError,
    ResponseParsingError,
    ValidationError,
)
from devpi_api_client.models.user import (
    UserDeleteResponse,
    UserInfo,
)


class TestUserApi:
    """Test cases for User API client."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        client = Mock()
        client.base_url = "http://test.example.com"
        client.session = Mock()
        return client

    @pytest.fixture
    def user_api(self, mock_client):
        """Create User API instance with mock client."""
        return User(mock_client)

    def test_create_user_success(self, user_api, mock_client):
        """Test successful user creation."""
        # Mock response data
        response_data = {
            "type": "userconfig",
            "result": {
                "username": "testuser",
                "email": "test@example.com",
                "indexes": {},
                "created": "2025-09-20T01:41:50Z"
            }
        }

        # Setup mock
        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            result = user_api.create("testuser", "password123", "test@example.com")

            # Verify request was made correctly
            mock_request.assert_called_once_with(
                'PUT',
                '/testuser',
                json={"password": "password123", "email": "test@example.com"}
            )

            # Verify result
            assert isinstance(result, UserInfo)
            assert result.username == "testuser"
            assert result.email == "test@example.com"

    def test_create_user_without_email(self, user_api):
        """Test user creation without email."""
        response_data = {
            "type": "userconfig",
            "result": {
                "username": "testuser",
                "email": "",
                "indexes": {}
            }
        }

        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            result = user_api.create("testuser", "password123")

            mock_request.assert_called_once_with(
                'PUT',
                '/testuser',
                json={"password": "password123"}
            )

            assert isinstance(result, UserInfo)
            assert result.username == "testuser"

    def test_create_user_missing_result(self, user_api):
        """Raise parsing error if result payload is missing."""
        response_data = {
            "message": "User created successfully",
            "username": "testuser"
        }

        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            with pytest.raises(ResponseParsingError, match="missing result payload"):
                user_api.create("testuser", "password123", "test@example.com")

            mock_request.assert_called_once_with(
                'PUT',
                '/testuser',
                json={"password": "password123", "email": "test@example.com"}
            )

    def test_create_user_validation_errors(self, user_api):
        """Test validation errors during user creation."""
        # Test empty username
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.create("", "password123")

        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.create("   ", "password123")

        # Test empty password
        with pytest.raises(ValidationError, match="Parameter 'password' must be a non-empty string"):
            user_api.create("testuser", "")

        with pytest.raises(ValidationError, match="Parameter 'password' must be a non-empty string"):
            user_api.create("testuser", "   ")

    def test_get_user_success(self, user_api):
        """Test successful user retrieval."""
        response_data = {
            "result": {
                "username": "testuser",
                "email": "test@example.com",
                "indexes": {"dev": {"type": "stage"}}
            }
        }

        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            result = user_api.get("testuser")

            mock_request.assert_called_once_with('GET', '/testuser')

            assert isinstance(result, UserInfo)
            assert result.username == "testuser"
            assert result.email == "test@example.com"
            assert "dev" in result.indexes

    def test_get_user_validation_error(self, user_api):
        """Test validation error when getting user with empty username."""
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.get("")

    def test_delete_user_success(self, user_api):
        """Test successful user deletion."""
        response_data = {
            "message": "User deleted successfully"
        }

        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            result = user_api.delete("testuser")

            mock_request.assert_called_once_with('DELETE', '/testuser')

            assert isinstance(result, UserDeleteResponse)
            assert result.message == "User deleted successfully"

    def test_delete_user_validation_error(self, user_api):
        """Test validation error when deleting user with empty username."""
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.delete("")

    def test_modify_user_success(self, user_api):
        """Test successful user modification."""
        # Mock the get method that's called after modify
        user_info_data = {
            "result": {
                "username": "testuser",
                "email": "new@example.com",
                "indexes": {}
            }
        }

        with patch.object(user_api, '_request', return_value=user_info_data) as mock_request:
            # First call is PATCH, second is GET
            mock_request.side_effect = [None, user_info_data]

            result = user_api.modify("testuser", email="new@example.com", password="newpass")

            # Verify PATCH request was made
            assert mock_request.call_count == 2
            mock_request.assert_any_call('PATCH', '/testuser', json={"email": "new@example.com", "password": "newpass"})
            mock_request.assert_any_call('GET', '/testuser')

            assert isinstance(result, UserInfo)
            assert result.email == "new@example.com"

    def test_modify_user_validation_errors(self, user_api):
        """Test validation errors during user modification."""
        # Test empty username
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.modify("", email="test@example.com")

        # Test no attributes provided
        with pytest.raises(ValidationError, match="No attributes provided to modify"):
            user_api.modify("testuser")

        # Test empty password
        with pytest.raises(ValidationError, match="Password cannot be empty"):
            user_api.modify("testuser", password="")

        # Test empty email
        with pytest.raises(ValidationError, match="Email cannot be empty when provided"):
            user_api.modify("testuser", email="   ")

    def test_list_users_success(self, user_api):
        """Test successful user listing returns mapping of UserInfo."""
        response_data = {
            "result": {
                "gitea": {"created": "2025-09-10T00:22:47Z", "indexes": {}, "username": "gitea"},
                "root": {
                    "created": "2025-09-10T00:16:08Z",
                    "indexes": {
                        "pypi": {
                            "mirror_url": "https://pypi.org/simple/",
                            "mirror_web_url_fmt": "https://pypi.org/project/{name}/",
                            "title": "PyPI",
                            "type": "mirror",
                            "volatile": False,
                        }
                    },
                    "username": "root",
                },
                "test1783": {"created": "2025-09-18T04:25:40Z", "indexes": {}, "username": "test1783"},
                "testuser": {
                    "created": "2025-09-17T04:46:53Z",
                    "email": "test@example.com",
                    "indexes": {},
                    "username": "testuser",
                },
                "veloslab": {
                    "created": "2025-09-10T00:22:58Z",
                    "indexes": {
                        "prod": {
                            "acl_toxresult_upload": ["veloslab"],
                            "acl_upload": ["root", "veloslab"],
                            "bases": ["root/pypi"],
                            "mirror_whitelist": [],
                            "mirror_whitelist_inheritance": "intersection",
                            "type": "stage",
                            "volatile": True,
                        }
                    },
                    "username": "veloslab",
                },
            },
            "type": "list:userconfig",
        }

        with patch.object(user_api, '_request', return_value=response_data) as mock_request:
            result = user_api.list()

            mock_request.assert_called_once_with('GET', '/')

            assert isinstance(result, dict)
            assert set(result) == {"gitea", "root", "test1783", "testuser", "veloslab"}
            assert isinstance(result["veloslab"], UserInfo)
            assert result["veloslab"].email == ""
            assert result["veloslab"].indexes["prod"].bases == ["root/pypi"]
            assert result["testuser"].email == "test@example.com"
            assert result["root"].indexes["pypi"].type == "mirror"
            assert len(result) == 5

    def test_exists_user_true(self, user_api):
        """Test user exists check returns True."""
        user_info_data = {
            "result": {
                "username": "testuser",
                "email": "test@example.com",
                "indexes": {}
            }
        }

        with patch.object(user_api, '_request', return_value=user_info_data):
            result = user_api.exists("testuser")
            assert result is True

    def test_exists_user_false(self, user_api):
        """Test user exists check returns False when user not found."""
        with patch.object(user_api, '_request', side_effect=NotFoundError("User not found")):
            result = user_api.exists("nonexistent")
            assert result is False

    def test_exists_user_validation_error(self, user_api):
        """Test validation error when checking existence with empty username."""
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.exists("")

    def test_change_password_success(self, user_api):
        """Test successful password change."""
        user_info_data = {
            "result": {
                "username": "testuser",
                "email": "test@example.com",
                "indexes": {}
            }
        }

        with patch.object(
            user_api,
            'modify',
            return_value=UserInfo.model_validate(user_info_data["result"]),
        ) as mock_modify:
            result = user_api.change_password("testuser", "newpassword")

            mock_modify.assert_called_once_with("testuser", password="newpassword")
            assert isinstance(result, UserInfo)

    def test_change_password_validation_errors(self, user_api):
        """Test validation errors during password change."""
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.change_password("", "newpassword")

        with pytest.raises(ValidationError, match="Parameter 'new_password' must be a non-empty string"):
            user_api.change_password("testuser", "")

    def test_change_email_success(self, user_api):
        """Test successful email change."""
        user_info_data = {
            "result": {
                "username": "testuser",
                "email": "new@example.com",
                "indexes": {}
            }
        }

        with patch.object(
            user_api,
            'modify',
            return_value=UserInfo.model_validate(user_info_data["result"]),
        ) as mock_modify:
            result = user_api.change_email("testuser", "new@example.com")

            mock_modify.assert_called_once_with("testuser", email="new@example.com")
            assert isinstance(result, UserInfo)

    def test_change_email_validation_errors(self, user_api):
        """Test validation errors during email change."""
        with pytest.raises(ValidationError, match="Parameter 'username' must be a non-empty string"):
            user_api.change_email("", "new@example.com")

        with pytest.raises(ValidationError, match="Parameter 'new_email' must be a non-empty string"):
            user_api.change_email("testuser", "")


class TestUserApiErrorHandling:
    """Test error handling in User API."""

    @pytest.fixture
    def user_api(self):
        """Create User API instance with mock client."""
        client = Mock()
        client.base_url = "http://test.example.com"
        return User(client)

    def test_create_user_conflict_error(self, user_api):
        """Test ConflictError when user already exists."""
        with patch.object(user_api, '_request', side_effect=ConflictError("User already exists")):
            with pytest.raises(ConflictError, match="User already exists"):
                user_api.create("existinguser", "password123")

    def test_get_user_not_found(self, user_api):
        """Test NotFoundError when user doesn't exist."""
        with patch.object(user_api, '_request', side_effect=NotFoundError("User not found")):
            with pytest.raises(NotFoundError, match="User not found"):
                user_api.get("nonexistent")

    def test_delete_user_permission_error(self, user_api):
        """Test PermissionError when insufficient permissions."""
        with patch.object(user_api, '_request', side_effect=PermissionError("Access forbidden")):
            with pytest.raises(PermissionError, match="Access forbidden"):
                user_api.delete("testuser")

    def test_authentication_error(self, user_api):
        """Test AuthenticationError propagation."""
        with patch.object(user_api, '_request', side_effect=AuthenticationError("Authentication failed")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                user_api.list()

    def test_network_error(self, user_api):
        """Test NetworkError propagation."""
        with patch.object(user_api, '_request', side_effect=NetworkError("Connection failed")):
            with pytest.raises(NetworkError, match="Connection failed"):
                user_api.get("testuser")
