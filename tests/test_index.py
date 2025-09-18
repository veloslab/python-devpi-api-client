import unittest
from unittest.mock import MagicMock
from devpi_api_client import Client
from devpi_api_client.models import IndexConfig
from devpi_api_client.exceptions import NotFoundError, ValidationError


class TestDevpiClientIndexMethods(unittest.TestCase):

    def setUp(self):
        """Set up a fresh client instance before each test."""
        self.client = Client(base_url="http://fake-devpi")
        self.client.index._request = MagicMock()

    def test_get_index_success(self):
        """Tests the get() method successfully retrieves and parses an index."""
        user, name = "testuser", "get-index"
        self.client.index._request.return_value = {'type': 'stage', 'volatile': True}

        result = self.client.index.get(user, name)

        self.client.index._request.assert_called_once_with(
            'GET', f"/{user}/{name}", params={'no_projects': ''}
        )
        self.assertIsInstance(result, IndexConfig)
        self.assertEqual(result.user, user)
        self.assertEqual(result.name, name)
        self.assertEqual(result.volatile, True)

    def test_get_index_not_found(self):
        """Tests the get() method raises NotFoundError for a 404 response."""
        user, name = "testuser", "non-existent-index"

        self.client.index._request.side_effect = NotFoundError(
            f"Resource not found at /{user}/{name}"
        )

        with self.assertRaises(NotFoundError):
            self.client.index.get(user, name)

        self.client.index._request.assert_called_once_with(
            'GET', f"/{user}/{name}", params={'no_projects': ''}
        )

    def test_create_index_with_defaults(self):
        """Tests create() with default parameters."""
        user, name = "testuser", "create-index"
        self.client.index._request.return_value = {
            'result': {
                'acl_toxresult_upload': [':ANONYMOUS:'],
                'acl_upload': [user],
                'bases': [],
                'mirror_whitelist': [],
                'mirror_whitelist_inheritance': 'intersection',
                'type': 'stage',
                'volatile': True
            },
            'type': 'indexconfig'
        }

        result = self.client.index.create(user, name)

        self.client.index._request.assert_any_call(
            'PUT', f"/{user}/{name}", json={'type': 'stage', 'volatile': True}
        )
        self.assertEqual(result.user, user)
        self.assertEqual(result.name, name)

    def test_create_index_with_custom_params(self):
        """Tests create() with a full set of custom parameters."""
        user, name = "testuser", "custom-index"
        custom_payload = {
            "type": "mirror",
            "volatile": False,
            "bases": ["root/pypi"],
            "acl_upload": [":ANONYMOUS:"]
        }
        self.client.index._request.return_value = {
            'result': {
                'acl_toxresult_upload': [':ANONYMOUS:'],
                'mirror_whitelist': [],
                'mirror_whitelist_inheritance': 'intersection',
                "type": "mirror",
                "volatile": False,
                "bases": ["root/pypi"],
                "acl_upload": [":ANONYMOUS:"]
            },
            'type': 'indexconfig'
        }
        result = self.client.index.create(user, name, **custom_payload)

        self.client.index._request.assert_any_call('PUT', f"/{user}/{name}", json=custom_payload)
        self.assertEqual(result.user, user)
        self.assertEqual(result.name, name)
        self.assertEqual(result.type, custom_payload['type'])

    def test_modify_index_single_param(self):
        """Tests modify() sends a PATCH request with the correct single field."""
        user, name = "testuser", "modify-index"
        # The GET call will return the "updated" data
        self.client.index._request.return_value = {
            'result': {
                'acl_toxresult_upload': [':ANONYMOUS:'],
                'mirror_whitelist': [],
                'mirror_whitelist_inheritance': 'intersection',
                "type": "mirror",
                "volatile": False,
                "bases": ["root/pypi"],
                "acl_upload": [":ANONYMOUS:"]
            },
            'type': 'indexconfig'
        }

        result = self.client.index.modify(user, name, volatile=False)

        self.client.index._request.assert_any_call(
            'PATCH', f"/{user}/{name}", json={'volatile': False}
        )
        self.assertEqual(result.volatile, False)

    def test_modify_with_no_params_raises_error(self):
        """
        Tests that modify() with no parameters raises ValidationError
        according to the actual implementation.
        """
        user, name = "testuser", "no-op-modify"

        with self.assertRaisesRegex(ValidationError, "No attributes provided to modify"):
            self.client.index.modify(user, name)

    def test_methods_raise_for_empty_params(self):
        """Ensures required parameters are validated across all methods."""
        with self.assertRaisesRegex(ValidationError, "Parameter 'user' must be a non-empty string"):
            self.client.index.get(user="", name="index")
        with self.assertRaisesRegex(ValidationError, "Parameter 'name' must be a non-empty string"):
            self.client.index.create(user="user", name="")
        with self.assertRaisesRegex(ValidationError, "Parameter 'name' must be a non-empty string"):
            self.client.index.modify(user="user", name="", volatile=False)

    def test_list_indexes_success(self):
        """Tests list() successfully retrieves a dictionary of indexes."""
        user = "test"
        # 1. Simulate the raw JSON response from the devpi server API
        mock_api_response = {
            'prod': {
                'type': 'stage',
                'bases': ['root/pypi'],
                'volatile': True,
                'acl_upload': ['root', 'veloslab']
            },
            'test': {
                'type': 'stage',
                'bases': [],
                'volatile': True,
                'acl_upload': [user]
            }
        }
        self.client.index._request.return_value = mock_api_response
        result = self.client.index.list(user)

        self.client.index._request.assert_called_once_with('GET', f"/{user}")

        self.assertIsInstance(result, dict)
        self.assertIn('prod', result)
        self.assertIn('test', result)

        prod_index = result['prod']
        self.assertIsInstance(prod_index, IndexConfig)
        self.assertEqual(prod_index.user, user)
        self.assertEqual(prod_index.name, 'prod')  # The name is derived from the key
        self.assertEqual(prod_index.type, 'stage')
        self.assertEqual(prod_index.bases, ['root/pypi'])
        self.assertEqual(result['test'].volatile, True)

    def test_list_indexes_empty(self):
        """Tests list() for a user with no indexes returns an empty dict."""
        user = "newuser"
        self.client.index._request.return_value = {}

        result = self.client.index.list(user)

        self.client.index._request.assert_called_once_with('GET', f"/{user}")
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
