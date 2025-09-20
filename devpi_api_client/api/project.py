import logging
import os
from pathlib import Path
from typing import Optional

import pkginfo
from pkginfo import Distribution

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.exceptions import NotFoundError, ValidationError
from devpi_api_client.models.base import DeleteResponse
from devpi_api_client.models.project import ProjectVersion, ProjectVersionList

logger = logging.getLogger(__name__)


class Project(DevApiBase):
    """
    Project/Package API client for devpi server package management.

    Provides methods to list packages, get package versions, upload new packages,
    and delete specific package versions from an index.
    Accessed via ``client.project`` or ``client.package``.
    """

    def list(self, user: str, index: str) -> list[str]:
        """
        List all unique package names available in an index.

        This method queries the index configuration to get the list of projects.

        :param user: User namespace for the index (must be non-empty)
        :param index: Name of the index to query (must be non-empty)
        :return: List of package names
        :raises ValidationError: If user or index is empty
        :raises NotFoundError: If index does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("index", index)

        logger.debug(f"Listing packages in index: {user}/{index}")
        index_config = self._client.index.get(user, index, no_projects=False)
        return index_config.projects or []

    def get(self, user: str, index: str, package_name: str) -> dict[str, ProjectVersion]:
        """
        Retrieve version and release file information for a specific package.

        :param user: User namespace for the index (must be non-empty)
        :param index: Name of the index (must be non-empty)
        :param package_name: Name of the package to retrieve (must be non-empty)
        :return: Dictionary mapping version strings to ProjectVersion objects
        :raises ValidationError: If user, index, or package_name is empty
        :raises NotFoundError: If package does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("index", index)
        validate_non_empty_string("package_name", package_name)

        path = f"/{user}/{index}/{package_name}"
        logger.debug(f"Retrieving package info: {user}/{index}/{package_name}")

        response_data = self._request('GET', path)
        if response_data:
            project_config_model = ProjectVersionList.model_validate(response_data)
            return project_config_model.root

        # If we get here without an exception, return empty dict
        return {}

    def upload(self, user: str, index: str, filepath: str) -> bool:
        """
        Upload a package file (e.g., .whl or .tar.gz) to a devpi index.

        This method replicates the `devpi upload` command by sending a
        multipart/form-data POST request containing both package metadata
        and the package file itself.

        :param user: User namespace for the index (must be non-empty)
        :param index: Name of the index (must be non-empty)
        :param filepath: Local path to the package file to upload
        :return: True if upload successful
        :raises ValidationError: If user or index is empty
        :raises FileNotFoundError: If package file does not exist
        :raises ValueError: If unsupported package file type or metadata parsing fails
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("index", index)

        if not filepath or not filepath.strip():
            raise ValidationError("filepath cannot be empty")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Package file not found at: {filepath}")

        file = Path(filepath)
        path = f"/{user}/{index}"

        # Extract metadata from the package file using pkginfo
        try:
            pkg_info: Distribution
            if file.name.endswith(".whl"):
                pkg_info = pkginfo.Wheel(filepath)
            elif file.name.endswith((".tar.gz", ".tgz")):
                pkg_info = pkginfo.SDist(filepath)
            elif file.name.endswith(".egg"):
                pkg_info = pkginfo.BDist(filepath)
            else:
                raise ValueError(
                    f"Unsupported package file type: {file.name}. Supported types: .whl, .tar.gz, .tgz, .egg"
                )
        except Exception as e:
            raise ValueError(f"Could not parse package metadata from {file.name}: {e}") from e

        # Validate that we got the required metadata
        if not pkg_info.name or not pkg_info.version:
            raise ValueError("Package metadata is incomplete - missing name or version")

        # Prepare the metadata payload
        metadata_payload = {
            ":action": "file_upload",
            "protocol_version": "1",
            "name": pkg_info.name,
            "version": pkg_info.version,
        }

        # Add optional metadata if available
        if pkg_info.summary:
            metadata_payload["summary"] = pkg_info.summary

        # Handle headers for multipart upload
        upload_headers = dict(self._client.session.headers)
        upload_headers.pop('Content-Type', None)

        logger.info(f"Uploading package {pkg_info.name} v{pkg_info.version} to {user}/{index}")

        # Perform the multipart POST request
        with open(filepath, 'rb') as f:
            files = {"content": (file.name, f)}

            self._request(
                'POST',
                path,
                return_json=False,
                data=metadata_payload,
                files=files,
                headers=upload_headers
            )

        logger.info(f"Successfully uploaded {pkg_info.name} v{pkg_info.version}")
        return True


    def delete(self, user: str, index: str, package_name: str, version: str) -> DeleteResponse:
        """
        Delete a specific version of a package from an index.

        :param user: User namespace for the index (must be non-empty)
        :param index: Name of the index (must be non-empty)
        :param package_name: Name of the package (must be non-empty)
        :param version: Specific version to delete (e.g., "1.2.3")
        :return: DeleteResponse confirming deletion
        :raises ValidationError: If any parameter is empty
        :raises NotFoundError: If package version does not exist
        :raises PermissionError: If insufficient permissions to delete
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("index", index)
        validate_non_empty_string("package_name", package_name)
        validate_non_empty_string("version", version)

        path = f"/{user}/{index}/{package_name}/{version}"
        logger.info(f"Deleting package version: {user}/{index}/{package_name}/{version}")

        response_data = self._request('DELETE', path)
        return DeleteResponse.model_validate(response_data)

    def exists(self, user: str, index: str, package_name: str, version: Optional[str] = None) -> bool:
        """
        Check if a package (or specific version) exists in an index.

        :param user: User namespace for the index (must be non-empty)
        :param index: Name of the index (must be non-empty)
        :param package_name: Name of the package (must be non-empty)
        :param version: Optional specific version to check
        :return: True if package/version exists, False otherwise
        :raises ValidationError: If any required parameter is empty
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("index", index)
        validate_non_empty_string("package_name", package_name)

        try:
            package_versions = self.get(user, index, package_name)
            if version:
                return version in package_versions
            else:
                return len(package_versions) > 0
        except NotFoundError:
            return False
