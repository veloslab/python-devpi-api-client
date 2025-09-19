import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
from pathlib import Path

from devpi_api_client import Client
from devpi_api_client.models.project import ProjectVersion
from devpi_api_client.models.index import IndexConfig
from devpi_api_client.models.base import DeleteResponse
from devpi_api_client.exceptions import NotFoundError, ValidationError


class TestDevpiClientProjectMethods(unittest.TestCase):
    def setUp(self):
        """Set up a fresh client instance before each test."""
        self.client = Client(base_url="http://fake-devpi")
        self.client.project._request = MagicMock()
        # The project.list method depends on the index.get method, so we mock it.
        self.client.index.get = MagicMock()

    def test_list_projects_success(self):
        """Tests list() correctly returns projects from an index."""
        user, index = "testuser", "testindex"
        project_list = ["package-a", "package-b"]

        # Mock the return value of index.get to be an IndexConfig with projects
        mock_index_config = IndexConfig(
            type='stage',
            volatile=True,
            projects=project_list
        )
        self.client.index.get.return_value = mock_index_config

        result = self.client.project.list(user, index)

        self.client.index.get.assert_called_once_with(user, index, no_projects=False)
        self.assertEqual(result, project_list)

    def test_list_projects_empty(self):
        """Tests list() returns an empty list if an index has no projects."""
        user, index = "testuser", "emptyindex"
        mock_index_config = IndexConfig(type='stage', volatile=True, projects=None)
        self.client.index.get.return_value = mock_index_config

        result = self.client.project.list(user, index)

        self.assertEqual(result, [])

    def test_get_project_success(self):
        """Tests get() successfully retrieves version info for a package."""
        user, index, package = "testuser", "testindex", "package-a"
        mock_api_response = {
            "result": {
                "1.0.0": {
                    "name": package,
                    "version": "1.0.0",
                    "+links": [{
                        "rel": "releasefile",
                        "hash_spec": "sha256=abc",
                        "href": "http://fake-devpi/test.whl",
                        "log": []
                    }]
                }
            }
        }
        self.client.project._request.return_value = mock_api_response

        result = self.client.project.get(user, index, package)

        self.client.project._request.assert_called_once_with('GET', f"/{user}/{index}/{package}")
        self.assertIn("1.0.0", result)
        self.assertIsInstance(result["1.0.0"], ProjectVersion)
        self.assertEqual(result["1.0.0"].version, "1.0.0")

    def test_get_project_not_found(self):
        """Tests get() raises NotFoundError for a non-existent package."""
        user, index, package = "testuser", "testindex", "non-existent"
        self.client.project._request.side_effect = NotFoundError("Not Found")

        with self.assertRaises(NotFoundError):
            self.client.project.get(user, index, package)

    def test_delete_project_version_success(self):
        """Tests delete() for a specific package version."""
        user, index, package, version = "testuser", "testindex", "package-a", "1.0.0"
        self.client.project._request.return_value = {"message": "deleted"}

        result = self.client.project.delete(user, index, package, version)

        self.client.project._request.assert_called_once_with('DELETE', f"/{user}/{index}/{package}/{version}")
        self.assertIsInstance(result, DeleteResponse)

    def test_exists_package_found(self):
        """Tests exists() returns True when a package exists."""
        user, index, package = "testuser", "testindex", "package-a"
        # Mock the internal get call to return some data
        self.client.project.get = MagicMock(return_value={"1.0.0": {}})

        self.assertTrue(self.client.project.exists(user, index, package))
        self.client.project.get.assert_called_once_with(user, index, package)

    def test_exists_version_found(self):
        """Tests exists() returns True when a specific version exists."""
        user, index, package, version = "testuser", "testindex", "package-a", "1.0.0"
        self.client.project.get = MagicMock(return_value={"1.0.0": {}, "1.0.1": {}})

        self.assertTrue(self.client.project.exists(user, index, package, version=version))

    def test_exists_version_not_found(self):
        """Tests exists() returns False when a specific version does not exist."""
        user, index, package, version = "testuser", "testindex", "package-a", "1.0.2"
        self.client.project.get = MagicMock(return_value={"1.0.0": {}, "1.0.1": {}})

        self.assertFalse(self.client.project.exists(user, index, package, version=version))

    def test_exists_package_not_found(self):
        """Tests exists() returns False when the package itself does not exist."""
        user, index, package = "testuser", "testindex", "non-existent"
        # FIX: Instantiate the exception for the side_effect
        self.client.project.get = MagicMock(side_effect=NotFoundError("Package not found"))

        self.assertFalse(self.client.project.exists(user, index, package))
        self.client.project.get.assert_called_once_with(user, index, package)

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data=b'file content')
    @patch('pkginfo.Wheel')
    def test_upload_wheel_success(self, mock_pkginfo_wheel, mock_open_file, mock_path_exists):
        """Tests a successful wheel upload."""
        user, index, filepath = "testuser", "testindex", "/path/to/fake.whl"

        # Configure the pkginfo mock
        mock_wheel_instance = MagicMock()
        mock_wheel_instance.name = "fake-package"
        mock_wheel_instance.version = "1.2.3"
        mock_wheel_instance.summary = "A test package"
        mock_pkginfo_wheel.return_value = mock_wheel_instance

        # We don't care about the return value, just that it doesn't fail
        self.client.project._request.return_value = None

        result = self.client.project.upload(user, index, filepath)

        self.assertTrue(result)

        # Verify the POST request
        call_args, call_kwargs = self.client.project._request.call_args
        self.assertEqual(call_args[0], 'POST')
        self.assertEqual(call_args[1], f"/{user}/{index}")

        # Check metadata payload
        expected_data = {
            ":action": "file_upload",
            "protocol_version": "1",
            "name": "fake-package",
            "version": "1.2.3",
            "summary": "A test package"
        }
        self.assertEqual(call_kwargs['data'], expected_data)

        # Check that 'content' file part was prepared
        self.assertIn('files', call_kwargs)
        self.assertIn('content', call_kwargs['files'])

    def test_upload_file_not_found(self):
        """Tests upload() raises FileNotFoundError for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.client.project.upload("user", "index", "/non/existent/file.whl")

    def test_upload_unsupported_file_type(self):
        """Tests upload() raises ValueError for an unsupported file extension."""
        with patch('os.path.exists', return_value=True):
            with self.assertRaisesRegex(ValueError, "Unsupported package file type"):
                self.client.project.upload("user", "index", "package.zip")

    def test_upload_incomplete_metadata(self):
        """Tests upload() raises ValueError if pkginfo fails to find metadata."""
        with patch('os.path.exists', return_value=True):
            with patch('pkginfo.Wheel') as mock_pkginfo_wheel:
                mock_wheel_instance = MagicMock()
                mock_wheel_instance.name = None  # Incomplete metadata
                mock_wheel_instance.version = "1.2.3"
                mock_pkginfo_wheel.return_value = mock_wheel_instance

                with self.assertRaisesRegex(ValueError, "Package metadata is incomplete"):
                    self.client.project.upload("user", "index", "fake.whl")

    def test_methods_raise_for_empty_params(self):
        """Ensures required string parameters are validated across all methods."""
        with self.assertRaisesRegex(ValidationError, "Parameter 'user' must be a non-empty string"):
            self.client.project.list(user="", index="index")
        with self.assertRaisesRegex(ValidationError, "Parameter 'index' must be a non-empty string"):
            self.client.project.get(user="user", index="", package_name="pkg")
        with self.assertRaisesRegex(ValidationError, "Parameter 'package_name' must be a non-empty string"):
            self.client.project.delete(user="user", index="index", package_name="", version="1.0")
        with self.assertRaisesRegex(ValidationError, "filepath cannot be empty"):
            self.client.project.upload(user="user", index="index", filepath="")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
