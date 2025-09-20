import logging
from typing import Any, Optional

from devpi_api_client.api.base import DevApiBase, validate_non_empty_string
from devpi_api_client.exceptions import NotFoundError, ValidationError
from devpi_api_client.models.base import DeleteResponse
from devpi_api_client.models.index import IndexConfig, IndexList

logger = logging.getLogger(__name__)


class Index(DevApiBase):
    """
    Index API client for devpi server index management.

    Provides methods to create, retrieve, modify, list, and delete indexes.
    Accessed via ``client.index``.
    """

    def create(
            self,
            user: str,
            name: str,
            type: str = "stage",
            bases: Optional[list[str]] = None,
            volatile: bool = True,
            acl_upload: Optional[list[str]] = None,
            acl_toxresult_upload: Optional[list[str]] = None,
            mirror_whitelist_inheritance: Optional[str] = None,
            mirror_whitelist: Optional[list[str]] = None,
    ) -> IndexConfig:
        """
        Create a new index with specified configuration parameters.

        :param user: User namespace for the index (must be non-empty)
        :param name: Name of the new index (must be non-empty)
        :param type: Type of the index, typically 'stage' or 'mirror'
        :param bases: List of parent indexes to inherit from
        :param volatile: If True, allows packages to be overwritten or deleted
        :param acl_upload: List of users/groups allowed to upload to this index
        :param acl_toxresult_upload: List of users/groups allowed to upload tox results
        :param mirror_whitelist_inheritance: Defines how the mirror whitelist is inherited
        :param mirror_whitelist: List of packages to exclusively mirror
        :return: IndexConfig model of the created index
        :raises ValidationError: If user or name is empty, or invalid type
        :raises ConflictError: If index already exists
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("name", name)

        # Validate type parameter
        valid_types = ['stage', 'mirror']
        if type not in valid_types:
            raise ValidationError(f"Invalid index type '{type}'. Must be one of: {', '.join(valid_types)}")

        path = f"/{user}/{name}"
        payload = {"type": type, "volatile": volatile}

        if bases is not None:
            payload["bases"] = bases
        if acl_upload is not None:
            payload["acl_upload"] = acl_upload
        if acl_toxresult_upload is not None:
            payload["acl_toxresult_upload"] = acl_toxresult_upload
        if mirror_whitelist_inheritance is not None:
            payload["mirror_whitelist_inheritance"] = mirror_whitelist_inheritance
        if mirror_whitelist is not None:
            payload["mirror_whitelist"] = mirror_whitelist

        logger.info(f"Creating index {user}/{name} with type: {type}")
        response_data = self._request('PUT', path, json=payload)
        validation_context = {"user": user, "name": name}
        return IndexConfig.model_validate(response_data, context=validation_context)


    def get(self, user: str, name: str, no_projects: bool = True) -> IndexConfig:
        """
        Retrieve configuration for a specific index.

        :param user: User namespace for the index (must be non-empty)
        :param name: Name of the index to retrieve (must be non-empty)
        :param no_projects: If True, exclude the large project list for performance
        :return: IndexConfig model of the configuration
        :raises ValidationError: If user or name is empty
        :raises NotFoundError: If index does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("name", name)

        path = f"/{user}/{name}"
        params = {'no_projects': ''} if no_projects else None

        logger.debug(f"Retrieving index configuration: {user}/{name}")
        response_data = self._request('GET', path, params=params)

        validation_context = {"user": user, "name": name}
        return IndexConfig.model_validate(response_data, context=validation_context)

    def delete(self, user: str, name: str) -> DeleteResponse:
        """
        Delete an index.

        :param user: User namespace for the index (must be non-empty)
        :param name: Name of the index to delete (must be non-empty)
        :return: DeleteResponse model confirming deletion
        :raises ValidationError: If user or name is empty
        :raises NotFoundError: If index does not exist
        :raises PermissionError: If insufficient permissions to delete index
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("name", name)

        path = f"/{user}/{name}"
        logger.info(f"Deleting index: {user}/{name}")
        response_data = self._request('DELETE', path)

        return DeleteResponse.model_validate(response_data)

    def modify(
            self,
            user: str,
            name: str,
            type: Optional[str] = None,
            bases: Optional[list[str]] = None,
            volatile: Optional[bool] = None,
            acl_upload: Optional[list[str]] = None,
            acl_toxresult_upload: Optional[list[str]] = None,
            mirror_whitelist_inheritance: Optional[str] = None,
            mirror_whitelist: Optional[list[str]] = None,
    ) -> IndexConfig:
        """
        Modify an existing index's attributes using explicit parameters.

        Only the parameters provided (i.e., not None) will be included in
        the PATCH request.

        :param user: User namespace for the index (must be non-empty)
        :param name: Name of the index to modify (must be non-empty)
        :param type: Type of the index, typically 'stage' or 'mirror'
        :param bases: List of parent indexes to inherit from
        :param volatile: If True, allows packages to be overwritten or deleted
        :param acl_upload: List of users/groups allowed to upload to this index
        :param acl_toxresult_upload: List of users/groups allowed to upload tox results
        :param mirror_whitelist_inheritance: Defines how the mirror whitelist is inherited
        :param mirror_whitelist: List of packages to exclusively mirror
        :return: IndexConfig model of the updated configuration
        :raises ValidationError: If user or name is empty, or no parameters to update
        :raises NotFoundError: If index does not exist
        :raises DevpiApiError: For other API errors
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("name", name)

        # Build the payload with only the provided arguments
        payload: dict[str, Any] = {}
        if type is not None:
            # Validate type parameter
            valid_types = ['stage', 'mirror']
            if type not in valid_types:
                raise ValidationError(f"Invalid index type '{type}'. Must be one of: {', '.join(valid_types)}")
            payload["type"] = type
        if bases is not None:
            payload["bases"] = bases
        if volatile is not None:
            payload["volatile"] = volatile
        if acl_upload is not None:
            payload["acl_upload"] = acl_upload
        if acl_toxresult_upload is not None:
            payload["acl_toxresult_upload"] = acl_toxresult_upload
        if mirror_whitelist_inheritance is not None:
            payload["mirror_whitelist_inheritance"] = mirror_whitelist_inheritance
        if mirror_whitelist is not None:
            payload["mirror_whitelist"] = mirror_whitelist

        # Ensure there's something to update
        if not payload:
            raise ValidationError("No attributes provided to modify")

        path = f"/{user}/{name}"
        logger.info(f"Modifying index {user}/{name} with attributes: {list(payload.keys())}")
        response_data = self._request('PATCH', path, json=payload)
        validation_context = {"user": user, "name": name}
        return IndexConfig.model_validate(response_data, context=validation_context)

    def list(self, user: str) -> dict[str, IndexConfig]:
        """
        List all indexes for a given user.

        :param user: Username whose indexes should be listed (must be non-empty)
        :return: Dictionary mapping index names to IndexConfig objects
        :raises ValidationError: If user is empty
        :raises DevpiApiError: For API errors
        """
        validate_non_empty_string("user", user)

        path = f"/{user}"
        logger.debug(f"Listing indexes for user: {user}")
        response = self._request('GET', path)

        validation_context = {"user": user}
        index_list_model = IndexList.model_validate(response, context=validation_context)
        return index_list_model.root


    def exists(self, user: str, name: str) -> bool:
        """
        Check if a specific index exists.

        :param user: User namespace for the index (must be non-empty)
        :param name: Name of the index to check (must be non-empty)
        :return: True if index exists, False otherwise
        :raises ValidationError: If user or name is empty
        """
        validate_non_empty_string("user", user)
        validate_non_empty_string("name", name)

        try:
            self.get(user, name, no_projects=True)
            return True
        except NotFoundError:
            return False
