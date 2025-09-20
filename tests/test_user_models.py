"""
Unit tests for User models.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from devpi_api_client.models.user import (
    UserCreateResponse,
    UserDeleteResponse,
    UserInfo,
    UserList,
)


class TestUserInfo:
    """Test cases for UserInfo model."""

    def test_create_user_info_minimal(self):
        """Test creating UserInfo with minimal required fields."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        user = UserInfo.model_validate(user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.indexes == {}

    def test_create_user_info_with_indexes(self):
        """Test creating UserInfo with indexes."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "indexes": {
                "dev": {"type": "stage", "bases": ["root/pypi"]},
                "prod": {"type": "stage", "bases": ["root/pypi"]}
            }
        }
        user = UserInfo.model_validate(user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert len(user.indexes) == 2
        assert "dev" in user.indexes
        assert "prod" in user.indexes

    def test_get_index_names(self):
        """Test getting index names."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "indexes": {
                "dev": {"type": "stage"},
                "prod": {"type": "stage"}
            }
        }
        user = UserInfo.model_validate(user_data)

        index_names = user.get_index_names()
        assert set(index_names) == {"dev", "prod"}

    def test_get_index_names_empty(self):
        """Test getting index names when no indexes exist."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        user = UserInfo.model_validate(user_data)

        index_names = user.get_index_names()
        assert index_names == []

    def test_has_index(self):
        """Test checking if user has specific index."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "indexes": {
                "dev": {"type": "stage"}
            }
        }
        user = UserInfo.model_validate(user_data)

        assert user.has_index("dev") is True
        assert user.has_index("prod") is False
        assert user.has_index("nonexistent") is False

    def test_get_index_config(self):
        """Test getting index configuration."""
        index_config = {"type": "stage", "bases": ["root/pypi"]}
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "indexes": {
                "dev": index_config
            }
        }
        user = UserInfo.model_validate(user_data)

        assert user.get_index_config("dev") == index_config
        assert user.get_index_config("nonexistent") is None

    def test_user_info_validation_error(self):
        """Test that validation errors are raised for invalid data."""
        with pytest.raises(PydanticValidationError):
            UserInfo.model_validate({"username": "testuser"})  # Missing email


class TestUserList:
    """Test cases for UserList model."""

    def test_create_user_list(self):
        """Test creating UserList from mapping payload."""
        user_payload = {
            "result": {
                "users": {
                    "user1": {
                        "email": "user1@example.com",
                        "indexes": {"dev": {"type": "stage"}},
                    },
                    "user2": {
                        "email": "",
                        "indexes": {},
                    },
                }
            }
        }
        user_list = UserList.model_validate(user_payload)

        assert len(user_list) == 2
        assert "user1" in user_list
        assert isinstance(user_list.root["user1"], UserInfo)
        assert user_list.root["user1"].email == "user1@example.com"
        assert user_list.root["user1"].indexes["dev"].type == "stage"

    def test_empty_user_list(self):
        """Test creating empty UserList."""
        user_list = UserList.model_validate({"result": {"users": {}}})

        assert len(user_list) == 0
        assert "anyuser" not in user_list

    def test_user_list_iteration(self):
        """Test iterating over UserList."""
        user_map = {"user1": {"email": ""}, "user2": {"email": ""}}
        user_list = UserList.model_validate({"result": {"users": user_map}})

        collected_names = list(user_list)
        assert collected_names == ["user1", "user2"]

    def test_user_list_contains(self):
        """Test checking if username exists in list."""
        user_map = {"user1": {"email": ""}, "user2": {"email": ""}}
        user_list = UserList.model_validate({"result": {"users": user_map}})

        assert "user1" in user_list
        assert "user4" not in user_list

    def test_get_usernames(self):
        """Test getting underlying username list."""
        user_map = {"user1": {"email": ""}, "user2": {"email": ""}}
        user_list = UserList.model_validate(user_map)

        assert user_list.get_usernames() == ["user1", "user2"]

    def test_user_list_from_username_sequence(self):
        """Test creating UserList from sequence of usernames for backward compatibility."""
        user_list = UserList.model_validate(["user1", "user2"])

        assert "user1" in user_list
        assert user_list.root["user1"].username == "user1"
        assert user_list.root["user1"].email == ""

    def test_user_list_real_payload(self):
        """Ensure UserList handles real API payload structure."""
        payload = {
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
                        },
                        "test": {
                            "acl_toxresult_upload": [":ANONYMOUS:"],
                            "acl_upload": ["veloslab"],
                            "bases": [],
                            "mirror_whitelist": [],
                            "mirror_whitelist_inheritance": "intersection",
                            "type": "stage",
                            "volatile": True,
                        },
                    },
                    "username": "veloslab",
                },
            },
            "type": "list:userconfig",
        }

        user_list = UserList.model_validate(payload)

        assert len(user_list) == 5
        assert "veloslab" in user_list
        veloslab = user_list.root["veloslab"]
        assert isinstance(veloslab, UserInfo)
        assert veloslab.username == "veloslab"
        assert veloslab.email == ""
        assert veloslab.indexes["prod"].type == "stage"
        assert veloslab.indexes["prod"].bases == ["root/pypi"]
        assert user_list.root["testuser"].email == "test@example.com"


class TestUserCreateResponse:
    """Test cases for UserCreateResponse model."""

    def test_create_response_from_result(self):
        """Parse creation response that only includes result payload."""
        response_data = {
            "type": "userconfig",
            "result": {
                "created": "2025-09-20T01:41:50Z",
                "email": "test@example.com",
                "indexes": {},
                "username": "newuser"
            }
        }
        response = UserCreateResponse.model_validate(response_data)

        assert response.type == "userconfig"
        assert response.username == "newuser"
        assert response.result is not None
        assert response.result.username == "newuser"
        assert response.result.email == "test@example.com"
        assert response.result.created is not None

    def test_is_success_with_successful_message(self):
        """Retain backward compatibility with message-based responses."""
        response_data = {
            "message": "User created successfully",
            "username": "newuser"
        }
        response = UserCreateResponse.model_validate(response_data)

        assert response.is_success() is True

    def test_is_success_with_result_only(self):
        """Treat presence of a result payload as success."""
        response_data = {
            "result": {
                "username": "newuser",
                "email": "test@example.com",
                "indexes": {}
            }
        }
        response = UserCreateResponse.model_validate(response_data)

        assert response.is_success() is True
        assert response.username == "newuser"

    def test_is_success_with_failure_message(self):
        """Test success detection with failure message."""
        response_data = {
            "message": "Failed to create user",
            "username": "newuser"
        }
        response = UserCreateResponse.model_validate(response_data)

        assert response.is_success() is False

    def test_validation_error_without_username(self):
        """Require username information in the response payload."""
        with pytest.raises(PydanticValidationError):
            UserCreateResponse.model_validate({"message": "test"})


class TestUserDeleteResponse:
    """Test cases for UserDeleteResponse model."""

    def test_delete_response(self):
        """Test creating UserDeleteResponse."""
        response_data = {
            "message": "User deleted successfully"
        }
        response = UserDeleteResponse.model_validate(response_data)

        assert response.message == "User deleted successfully"

    def test_is_success_with_successful_message(self):
        """Test success detection with successful message."""
        response_data = {
            "message": "User deleted successfully"
        }
        response = UserDeleteResponse.model_validate(response_data)

        assert response.is_success() is True

    def test_is_success_with_deleted_message(self):
        """Test success detection with 'deleted' in message."""
        response_data = {
            "message": "User has been deleted"
        }
        response = UserDeleteResponse.model_validate(response_data)

        assert response.is_success() is True

    def test_is_success_with_failure_message(self):
        """Test success detection with failure message."""
        response_data = {
            "message": "Failed to delete user"
        }
        response = UserDeleteResponse.model_validate(response_data)

        assert response.is_success() is False

    def test_validation_error(self):
        """Test validation error for missing required fields."""
        with pytest.raises(PydanticValidationError):
            UserDeleteResponse.model_validate({})  # Missing message
