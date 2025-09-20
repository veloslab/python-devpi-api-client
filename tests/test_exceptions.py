"""
Unit tests for custom exceptions.
"""

import pytest

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


class TestDevpiApiError:
    """Test cases for base DevpiApiError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = DevpiApiError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response_data is None

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = DevpiApiError("Test error", status_code=404)

        assert error.message == "Test error"
        assert error.status_code == 404
        assert error.response_data is None

    def test_error_with_response_data(self):
        """Test error with response data."""
        response_data = {"error": "Not found", "code": "USER_NOT_FOUND"}
        error = DevpiApiError("Test error", response_data=response_data)

        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response_data == response_data

    def test_error_with_all_parameters(self):
        """Test error with all parameters."""
        response_data = {"error": "Not found"}
        error = DevpiApiError("Test error", status_code=404, response_data=response_data)

        assert error.message == "Test error"
        assert error.status_code == 404
        assert error.response_data == response_data


class TestSpecificExceptions:
    """Test cases for specific exception types."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials", status_code=401)

        assert isinstance(error, DevpiApiError)
        assert error.message == "Invalid credentials"
        assert error.status_code == 401

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid parameter")

        assert isinstance(error, DevpiApiError)
        assert error.message == "Invalid parameter"

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found", status_code=404)

        assert isinstance(error, DevpiApiError)
        assert error.message == "Resource not found"
        assert error.status_code == 404

    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied", status_code=403)

        assert isinstance(error, DevpiApiError)
        assert error.message == "Access denied"
        assert error.status_code == 403

    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Resource already exists", status_code=409)

        assert isinstance(error, DevpiApiError)
        assert error.message == "Resource already exists"
        assert error.status_code == 409

    def test_server_error(self):
        """Test ServerError."""
        error = ServerError("Internal server error", status_code=500)

        assert isinstance(error, DevpiApiError)
        assert error.message == "Internal server error"
        assert error.status_code == 500

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection timeout")

        assert isinstance(error, DevpiApiError)
        assert error.message == "Connection timeout"

    def test_response_parsing_error(self):
        """Test ResponseParsingError."""
        error = ResponseParsingError("Invalid JSON response")

        assert isinstance(error, DevpiApiError)
        assert error.message == "Invalid JSON response"


class TestExceptionInheritance:
    """Test that all custom exceptions inherit properly."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from DevpiApiError."""
        exception_classes = [
            AuthenticationError,
            ValidationError,
            NotFoundError,
            PermissionError,
            ConflictError,
            ServerError,
            NetworkError,
            ResponseParsingError,
        ]

        for exc_class in exception_classes:
            error = exc_class("test message")
            assert isinstance(error, DevpiApiError)
            assert isinstance(error, Exception)

    def test_exception_can_be_caught_as_base(self):
        """Test that specific exceptions can be caught as base exception."""
        try:
            raise AuthenticationError("Auth failed")
        except DevpiApiError as e:
            assert e.message == "Auth failed"
        except Exception:
            pytest.fail("Should have been caught as DevpiApiError")

    def test_exception_maintains_specific_type(self):
        """Test that exceptions maintain their specific type."""
        try:
            raise NotFoundError("Not found")
        except NotFoundError as e:
            assert isinstance(e, NotFoundError)
            assert isinstance(e, DevpiApiError)
        except Exception:
            pytest.fail("Should have been caught as NotFoundError")
