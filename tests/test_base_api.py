"""
Unit tests for base API functionality.
"""

import pytest
from unittest.mock import Mock
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.exceptions import (
    ValidationError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ConflictError,
    ServerError,
    NetworkError,
    ResponseParsingError,
)


class TestDevApiBase:
    """Test cases for DevApiBase class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        client = Mock()
        client.base_url = "http://test.example.com"
        client.session = Mock()
        return client

    @pytest.fixture
    def api_base(self, mock_client):
        """Create DevApiBase instance with mock client."""
        return DevApiBase(mock_client)

    def test_init(self, mock_client):
        """Test initialization of DevApiBase."""
        api = DevApiBase(mock_client)
        assert api._client == mock_client

    def test_validate_non_empty_string_valid(self, api_base):
        """Test validation with valid non-empty string."""
        # Should not raise any exception
        validate_non_empty_string("test_param", "valid_value")

    def test_validate_non_empty_string_empty(self, api_base):
        """Test validation with empty string."""
        with pytest.raises(ValidationError, match="Parameter 'test_param' must be a non-empty string"):
            validate_non_empty_string("test_param", "")

    def test_validate_non_empty_string_whitespace(self, api_base):
        """Test validation with whitespace-only string."""
        with pytest.raises(ValidationError, match="Parameter 'test_param' must be a non-empty string"):
            validate_non_empty_string("test_param", "   ")

    def test_validate_non_empty_string_not_string(self, api_base):
        """Test validation with non-string value."""
        with pytest.raises(ValidationError, match="Parameter 'test_param' must be a non-empty string"):
            validate_non_empty_string("test_param", 123)

        with pytest.raises(ValidationError, match="Parameter 'test_param' must be a non-empty string"):
            validate_non_empty_string("test_param", None)

    def test_request_success_json(self, api_base, mock_client):
        """Test successful request with JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_client.session.request.return_value = mock_response

        result = api_base._request("GET", "/test")

        assert result == {"result": "success"}
        mock_client.session.request.assert_called_once_with(
            url="http://test.example.com/test",
            method="GET"
        )
        mock_response.raise_for_status.assert_called_once()

    def test_request_success_no_json(self, api_base, mock_client):
        """Test successful request without JSON parsing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.session.request.return_value = mock_response

        result = api_base._request("GET", "/test", return_json=False)

        assert result == mock_response
        mock_response.json.assert_not_called()

    def test_request_authentication_error(self, api_base, mock_client):
        """Test 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_client.session.request.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            api_base._request("GET", "/test")

        assert "Authentication failed" in str(exc_info.value)
        assert exc_info.value.status_code == 401
        assert exc_info.value.response_data == {"error": "Unauthorized"}

    def test_request_permission_error(self, api_base, mock_client):
        """Test 403 permission error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_client.session.request.return_value = mock_response

        with pytest.raises(PermissionError) as exc_info:
            api_base._request("GET", "/test")

        assert "Access forbidden" in str(exc_info.value)
        assert exc_info.value.status_code == 403

    def test_request_not_found_error(self, api_base, mock_client):
        """Test 404 not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_client.session.request.return_value = mock_response

        with pytest.raises(NotFoundError) as exc_info:
            api_base._request("GET", "/test")

        assert "Resource not found at /test" in str(exc_info.value)
        assert exc_info.value.status_code == 404

    def test_request_conflict_error(self, api_base, mock_client):
        """Test 409 conflict error."""
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"error": "Conflict"}
        mock_client.session.request.return_value = mock_response

        with pytest.raises(ConflictError) as exc_info:
            api_base._request("GET", "/test")

        assert "Conflict" in str(exc_info.value)
        assert exc_info.value.status_code == 409

    def test_request_server_error(self, api_base, mock_client):
        """Test 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_client.session.request.return_value = mock_response

        with pytest.raises(ServerError) as exc_info:
            api_base._request("GET", "/test")

        assert "Server error (HTTP 500)" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_request_connection_error(self, api_base, mock_client):
        """Test connection error."""
        mock_client.session.request.side_effect = ConnectionError("Connection failed")

        with pytest.raises(NetworkError) as exc_info:
            api_base._request("GET", "/test")

        assert "Network error while connecting" in str(exc_info.value)

    def test_request_timeout_error(self, api_base, mock_client):
        """Test timeout error."""
        mock_client.session.request.side_effect = Timeout("Request timeout")

        with pytest.raises(NetworkError) as exc_info:
            api_base._request("GET", "/test")

        assert "Network error while connecting" in str(exc_info.value)

    def test_request_http_error(self, api_base, mock_client):
        """Test HTTP error not caught by specific status codes."""
        mock_response = Mock()
        mock_response.status_code = 418  # I'm a teapot
        mock_response.json.return_value = {"error": "Teapot error"}
        mock_client.session.request.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError("HTTP error")

        with pytest.raises(ServerError) as exc_info:
            api_base._request("GET", "/test")

        assert "HTTP error" in str(exc_info.value)

    def test_request_generic_request_exception(self, api_base, mock_client):
        """Test generic request exception."""
        mock_client.session.request.side_effect = RequestException("Generic request error")

        with pytest.raises(NetworkError) as exc_info:
            api_base._request("GET", "/test")

        assert "Request failed" in str(exc_info.value)

    def test_request_json_parsing_error(self, api_base, mock_client):
        """Test JSON parsing error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.session.request.return_value = mock_response

        with pytest.raises(ResponseParsingError) as exc_info:
            api_base._request("GET", "/test")

        assert "Failed to parse JSON response" in str(exc_info.value)

    def test_safe_json_parse_success(self, api_base):
        """Test successful JSON parsing."""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}

        result = api_base._safe_json_parse(mock_response)
        assert result == {"key": "value"}

    def test_safe_json_parse_value_error(self, api_base):
        """Test JSON parsing with ValueError."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        result = api_base._safe_json_parse(mock_response)
        assert result is None

    def test_safe_json_parse_attribute_error(self, api_base):
        """Test JSON parsing with AttributeError."""
        mock_response = Mock()
        mock_response.json.side_effect = AttributeError("No json method")

        result = api_base._safe_json_parse(mock_response)
        assert result is None

    def test_request_with_kwargs(self, api_base, mock_client):
        """Test request with additional keyword arguments."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_client.session.request.return_value = mock_response

        api_base._request("POST", "/test", json={"data": "test"}, headers={"Content-Type": "application/json"})

        mock_client.session.request.assert_called_once_with(
            url="http://test.example.com/test",
            method="POST",
            json={"data": "test"},
            headers={"Content-Type": "application/json"}
        )

    def test_request_url_construction(self, api_base, mock_client):
        """Test URL construction with different path formats."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_client.session.request.return_value = mock_response

        # Test with leading slash
        api_base._request("GET", "/test/path")
        mock_client.session.request.assert_called_with(
            url="http://test.example.com/test/path",
            method="GET"
        )

        # Test without leading slash
        api_base._request("GET", "test/path")
        mock_client.session.request.assert_called_with(
            url="http://test.example.com/test/path",
            method="GET"
        )