import unittest
from unittest.mock import MagicMock, patch
import datetime

from devpi_api_client import Client
from devpi_api_client.models.token import TokenInfo
from devpi_api_client.models.base import DeleteResponse
from devpi_api_client.exceptions import ValidationError, NotFoundError


class TestDevpiClientTokenMethods(unittest.TestCase):
    def setUp(self):
        """Set up a fresh client instance before each test."""
        self.client = Client(base_url="http://fake-devpi")
        self.client.token._request = MagicMock()

    def test_create_token_success(self):
        """Tests create() successfully generates a token with custom parameters."""
        username = "testuser"
        mock_token_secret = "devpi-Tj1p_AcxT8222TcaM2Y8yv4E"
        self.client.token._request.return_value = {
            "result": {"token": mock_token_secret},
            "type": "token"
        }

        # A dummy class is the most reliable way to patch datetime.now()
        class DummyDateTime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                # Always return a fixed time, respecting the timezone argument
                return cls(2025, 1, 1, 0, 0, 0, tzinfo=tz)

        with patch('datetime.datetime', new=DummyDateTime):
            token = self.client.token.create(
                username=username,
                allowed=["pkg_read", "upload"],
                expires_in_seconds=3600,
                indexes=["user/dev"],
                projects=["proj-a"]
            )

        self.assertEqual(token, mock_token_secret)

        # Calculate the expected timestamp dynamically to match the code's logic
        expected_timestamp = int(
            (datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc) +
             datetime.timedelta(seconds=3600)).timestamp()
        )  # This will correctly be 1735693200

        expected_payload = {
            "allowed": sorted(["pkg_read", "upload"]),  # Your code sorts permissions
            "expires": expected_timestamp,
            "indexes": ["user/dev"],
            "projects": ["proj-a"]
        }

        self.client.token._request.assert_called_once_with(
            'POST', f"/{username}/+token-create", json=expected_payload
        )

    def test_create_token_invalid_permission(self):
        """Tests create() raises ValidationError for an unknown permission."""
        with self.assertRaisesRegex(ValidationError, "Unknown permissions: invalid_perm"):
            self.client.token.create("user", allowed=["upload", "invalid_perm"])

    def test_create_token_invalid_expiry(self):
        """Tests create() raises ValidationError for a non-positive expiry."""
        with self.assertRaisesRegex(ValidationError, "expires_in_seconds must be a positive integer"):
            self.client.token.create("user", expires_in_seconds=-100)

    def test_list_tokens_success(self):
        """Tests list() successfully retrieves and parses user tokens."""
        username = "testuser"
        mock_token_id = "abc123def"
        mock_api_response = {
            "result": {
                "tokens": {
                    mock_token_id: {
                        "restrictions": [
                            "allowed=pkg_read,upload",
                            "expires=1735689600",
                            "indexes=user/prod",
                        ]
                    }
                }
            },
            "type": "tokenlist"
        }
        self.client.token._request.return_value = mock_api_response

        tokens = self.client.token.list(username)

        self.client.token._request.assert_called_once_with('GET', f"/{username}/+tokens")
        self.assertIn(mock_token_id, tokens)
        self.assertIsInstance(tokens[mock_token_id], TokenInfo)

        token_info = tokens[mock_token_id]
        self.assertEqual(token_info.id, mock_token_id)
        self.assertEqual(token_info.user, username)
        self.assertEqual(token_info.allowed, ["pkg_read", "upload"])
        self.assertEqual(token_info.expires, 1735689600)
        self.assertEqual(token_info.indexes, ["user/prod"])

    def test_list_tokens_empty(self):
        """Tests list() returns an empty dict for a user with no tokens."""
        username = "newuser"
        mock_api_response = {"result": {"tokens": {}}, "type": "tokenlist"}
        self.client.token._request.return_value = mock_api_response

        tokens = self.client.token.list(username)
        self.assertEqual(tokens, {})

    def test_delete_token_success(self):
        """Tests delete() successfully removes a token."""
        username, token_id = "testuser", "abc123def"
        self.client.token._request.return_value = {"message": "deleted"}

        result = self.client.token.delete(username, token_id)

        self.client.token._request.assert_called_once_with('DELETE', f"/{username}/+tokens/{token_id}")
        self.assertIsInstance(result, DeleteResponse)

    def test_inspect_token_success(self):
        """Tests inspect() correctly parses a valid token string."""
        # This is a realistic-looking but fake macaroon for structure
        token_str = "devpi-MDAxY2xvY2F0aW9uIGRldnBpCjAwMTBjaWQgdXNlcj1yb290CjAwMTZjaWQgdG9rZW5faWQ9YWJjMTIzCjAwMmZzaWduYXR1cmUgAe8-p0_gFA"

        # Mocking the pymacaroons library directly
        with patch('pymacaroons.Macaroon') as mock_macaroon:
            mock_caveat = MagicMock()
            mock_caveat.to_dict.return_value = {'cid': 'allowed=pkg_read,upload'}

            mock_macaroon_instance = MagicMock()
            mock_macaroon_instance.identifier.decode.return_value = "root-abc123"
            mock_macaroon_instance.caveats = [mock_caveat]
            mock_macaroon.deserialize.return_value = mock_macaroon_instance

            token_info = self.client.token.inspect(token_str)

        self.assertEqual(token_info.user, "root")
        self.assertEqual(token_info.id, "abc123")
        self.assertEqual(token_info.restrictions, ["allowed=pkg_read,upload"])

    def test_inspect_token_invalid_format(self):
        """Tests inspect() raises ValueError for a malformed token."""
        with self.assertRaisesRegex(ValueError, "Failed to parse token"):
            self.client.token.inspect("not-a-valid-token")

    def test_exists_token_found(self):
        """Tests exists() returns True when a token is found."""
        username, token_id = "testuser", "abc123def"
        self.client.token.list = MagicMock(return_value={token_id: {}})

        self.assertTrue(self.client.token.exists(username, token_id))
        self.client.token.list.assert_called_once_with(username)

    def test_exists_token_not_found(self):
        """Tests exists() returns False when a token is not found."""
        username, token_id = "testuser", "xyz789"
        self.client.token.list = MagicMock(return_value={"abc123def": {}})

        self.assertFalse(self.client.token.exists(username, token_id))

    def test_methods_raise_for_empty_params(self):
        """Ensures required string parameters are validated."""
        with self.assertRaisesRegex(ValidationError, "Parameter 'username' must be a non-empty string"):
            self.client.token.create(username="")
        with self.assertRaisesRegex(ValidationError, "Parameter 'user' must be a non-empty string"):
            self.client.token.list(user="")
        with self.assertRaisesRegex(ValidationError, "Parameter 'token_id' must be a non-empty string"):
            self.client.token.delete(username="user", token_id="")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
