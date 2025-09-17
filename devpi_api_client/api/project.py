import os
import pkginfo
from typing import Any, List, Optional, Dict
from pathlib import Path
from devpi_api_client.api.base import DevApiBase, logger
from devpi_api_client.models.project import ProjectVersionList, ProjectVersion
from devpi_api_client.models.base import DeleteResponse


class Project(DevApiBase):
    """
    Package API Methods. Accessed via ``client.package``.

    Provides methods to list packages, get package versions, upload new packages,
    and delete specific package versions from an index.
    """

    @staticmethod
    def _validate_non_empty_param(name: str, value: Any) -> None:
        """Raise ValueError if a parameter is not a non-blank string."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Parameter '{name}' cannot be empty or a blank string.")

    def list(self, user: str, index: str) -> Optional[List[str]]:
        """
        Lists all unique package names available in an index.

        This method queries the simple index API, which is designed for package
        installation tools but is also perfect for listing package names.

        :param user: The user namespace for the index.
        :param index: The name of the index to query.
        :return: A list of package names or None
        """
        index_config = self._client.index.get(user, index, no_projects=False)
        return index_config.projects

    def get(self, user: str, index: str, package_name: str) -> Dict[str, ProjectVersion]:
        """
        Retrieves version and release file information for a specific package.

        :param user: The user namespace for the index.
        :param index: The name of the index.
        :param package_name: The name of the package to retrieve.
        :return: A `PackageInfo` model detailing versions and files, or None.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("index", index)
        self._validate_non_empty_param("package_name", package_name)
        path = f"/{user}/{index}/{package_name}"

        response_data = self._request('GET', path)
        if response_data:
            project_config_model = ProjectVersionList.model_validate(response_data)
            return project_config_model.root
        return None

    def upload(self, user: str, index: str, filepath: str) -> Any:
        """
        Uploads a package file (e.g., .whl or .tar.gz) to a devpi index.

        This method replicates the `devpi upload` command by sending a
        multipart/form-data POST request containing both package metadata
        and the package file itself.

        :param user: The user namespace for the index.
        :param index: The name of the index.
        :param filepath: The local path to the package file to upload.
        :return: The JSON response from the devpi server.
        """
        # 1. Parameter and file existence validation (remains the same)
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("index", index)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Package file not found at: {filepath}")

        path = f"/{user}/{index}"
        file = Path(filepath)

        # 2. Extract metadata from the package file using pkginfo
        try:
            if file.name.endswith(".whl"):
                pkg_info = pkginfo.Wheel(filepath)
            elif file.name.endswith(".tar.gz") or file.name.endswith(".tgz"):
                pkg_info = pkginfo.SDist(filepath)
            else:
                # Add other types if needed, like .egg
                raise TypeError(f"Unsupported package file type: {file.name}")
        except Exception as e:
            raise RuntimeError(f"Could not parse package metadata from {file.name}: {e}")

        # 3. Prepare the metadata payload to be sent as form data
        metadata_payload = {
            ":action": "file_upload",
            "protocol_version": "1",
            "name": pkg_info.name,
            "version": pkg_info.version,
            "summary": pkg_info.summary,
        }

        # 4. Correctly handle headers for multipart upload
        # Create a temporary copy of headers and remove Content-Type
        upload_headers = self._client.session.headers.copy()
        if 'Content-Type' in upload_headers:
            del upload_headers['Content-Type']

        # 5. Perform the multipart POST request
        with open(filepath, 'rb') as f:
            # Pass the file object directly for streaming upload
            files = {"content": (file.name, f)}

            # Pass metadata via 'data' and the file via 'files'
            # Your _request method should pass these through to requests.post
            self._request(
                'POST',
                path,
                return_json=False,
                data=metadata_payload,
                files=files,
                headers=upload_headers
            )
            return True


    def delete(self, user: str, index: str, package_name: str, version: str):
        """
        Deletes a specific version of a package from an index.

        :param user: The user namespace for the index.
        :param index: The name of the index.
        :param package_name: The name of the package.
        :param version: The specific version to delete (e.g., "1.2.3").
        :return: A `DeleteResponse` model confirming deletion, or None.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("index", index)
        self._validate_non_empty_param("package_name", package_name)
        self._validate_non_empty_param("version", version)

        path = f"/{user}/{index}/{package_name}/{version}"
        logger.info(f"Requesting deletion of package version: {path}")

        response_data = self._request('DELETE', path)
        if response_data:
            return DeleteResponse.model_validate(response_data)

