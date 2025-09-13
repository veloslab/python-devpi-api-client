from typing import Any, List, Optional, Dict
from devpi_api_client.api.base import DevApiBase, logger
from devpi_api_client.models.index import DeleteResponse, IndexConfig, IndexList


class Index(DevApiBase):
    """
    Index API Methods. Accessed via ``client.index``.
    Provides methods to create, retrieve, modify, list, and delete indices.
    """

    @staticmethod
    def _validate_non_empty_param(name: str, value: Any) -> None:
        """Raise ValueError if a parameter is not a non-blank string."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Parameter '{name}' cannot be empty or a blank string.")

    def create(
            self,
            user: str,
            name: str,
            type: str = "stage",
            bases: Optional[List[str]] = None,
            volatile: bool = True,
            acl_upload: Optional[List[str]] = None,
            acl_toxresult_upload: Optional[List[str]] = None,
            mirror_whitelist_inheritance: Optional[str] = None,
            mirror_whitelist: Optional[List[str]] = None,
    ) -> Optional[IndexConfig]:
        """
        Creates a new index with fully explicit configuration parameters.

        :param user: The user namespace for the index. Cannot be empty.
        :param name: The name of the new index. Cannot be empty.
        :param type: The type of the index, typically 'stage' or 'mirror'.
        :param bases: A list of parent indexes to inherit from.
        :param volatile: If True, allows packages to be overwritten or deleted.
        :param acl_upload: A list of users/groups allowed to upload to this index.
        :param acl_toxresult_upload: A list of users/groups allowed to upload tox results.
        :param mirror_whitelist_inheritance: Defines how the mirror whitelist is inherited.
        :param mirror_whitelist: A list of packages to exclusively mirror.
        :return: An `IndexConfig` model of the created index, or None on failure.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("name", name)

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

        self._request('PUT', path, json=payload)
        logger.info(f"Sent request to create index {path} with payload: {payload}")

        return self.get(user, name, no_projects=True)

    def get(self, user: str, name: str, no_projects: bool = True) -> Optional[IndexConfig]:
        """
        Retrieves configuration for a specific index.

        :param user: The user namespace for the index. Cannot be empty.
        :param name: The name of the index to retrieve. Cannot be empty.
        :param no_projects: If True, exclude the large project list for performance.
        :return: An `IndexConfig` model of the configuration, or None if not found.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("name", name)
        path = f"/{user}/{name}"
        params = {'no_projects': ''} if no_projects else None
        response_data = self._request('GET', path, params=params)

        if response_data:
            # Pass user and name in the context dictionary
            validation_context = {"user": user, "name": name}
            return IndexConfig.model_validate(
                response_data,
                context=validation_context
            )
        return None

    def delete(self, user: str, name: str) -> Optional[DeleteResponse]:
        """
        Deletes an index.

        :param user: The user namespace for the index. Cannot be empty.
        :param name: The name of the index to delete. Cannot be empty.
        :return: A `DeleteResponse` model confirming deletion, or None on failure.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("name", name)

        path = f"/{user}/{name}"
        logger.info(f"Requesting deletion of index: {path}")
        response_data = self._request('DELETE', path)
        if response_data:
            return DeleteResponse.model_validate(response_data)
        return None

    def modify(
            self,
            user: str,
            name: str,
            type: Optional[str] = None,
            bases: Optional[List[str]] = None,
            volatile: Optional[bool] = None,
            acl_upload: Optional[List[str]] = None,
            acl_toxresult_upload: Optional[List[str]] = None,
            mirror_whitelist_inheritance: Optional[str] = None,
            mirror_whitelist: Optional[List[str]] = None,
    ) -> 'IndexConfig':
        """
        Modifies an existing index's attributes using explicit parameters.

        Only the parameters provided (i.e., not None) will be included in
        the PATCH request.

        :param user: The user namespace for the index. Cannot be empty.
        :param name: The name of the index to modify. Cannot be empty.
        :param type: The type of the index, typically 'stage' or 'mirror'.
        :param bases: A list of parent indexes to inherit from.
        :param volatile: If True, allows packages to be overwritten or deleted.
        :param acl_upload: A list of users/groups allowed to upload to this index.
        :param acl_toxresult_upload: A list of users/groups allowed to upload tox results.
        :param mirror_whitelist_inheritance: Defines how the mirror whitelist is inherited.
        :param mirror_whitelist: A list of packages to exclusively mirror.
        :return: An `IndexConfig` model of the updated configuration, or None on failure.
        """
        self._validate_non_empty_param("user", user)
        self._validate_non_empty_param("name", name)
        path = f"/{user}/{name}"

        # Build the payload with only the provided arguments
        payload = {}
        if type is not None:
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

        # Proceed only if there's something to update
        if not payload:
            logger.warning("Modify called without any parameters to update.")
            # Optionally, you could return self.get() here directly or even raise an error
            return self.get(user, name, no_projects=True)

        logger.info(f"Sending PATCH request for {path} with data: {payload}")
        self._request('PATCH', path, json=payload)

        # Fetch the updated configuration
        return self.get(user, name, no_projects=True)

    def list(self, user: str) -> Dict[str, IndexConfig]:
        """
        Lists all indexes for a given user.

        :param user: The user whose indexes should be listed. Cannot be empty.
        :return: An `IndexList` root model containing a dictionary of indexes, or None on failure.
        """
        self._validate_non_empty_param("user", user)

        path = f"/{user}"
        response = self._request('GET', path)
        if response:
            # Pass the user in the context dictionary
            validation_context = {"user": user}

            # Validate using the IndexList RootModel
            index_list_model = IndexList.model_validate(
                response,
                context=validation_context
            )
            # Return the underlying dictionary from the RootModel
            return index_list_model.root
