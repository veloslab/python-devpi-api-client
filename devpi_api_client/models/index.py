from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, RootModel, model_validator
from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator, ValidationInfo


class IndexConfig(BaseModel):
    user: Optional[str] = None
    name: Optional[str] = None
    type: str
    bases: Optional[List[str]] = Field(default_factory=list)
    volatile: bool = Field(default=False)
    acl_upload: Optional[List[str]] = Field(default_factory=list)
    acl_toxresult_upload: Optional[List[str]] = Field(default_factory=list)
    mirror_whitelist_inheritance: Optional[str] = None
    mirror_whitelist: Optional[List[Any]] = Field(default_factory=list)
    projects: Optional[List[str]] = None

    @model_validator(mode='before')
    @classmethod
    def _unwrap_result_key(cls, data: Any) -> Any:
        """
        If the input is a dictionary with a 'result' key, this validator
        extracts the nested dictionary before validation proceeds.
        """
        if isinstance(data, dict) and 'result' in data:
            return data['result']
        return data

    @model_validator(mode='after')
    def _add_context_to_fields(self, info: ValidationInfo) -> "IndexConfig":
        """
        After initial validation, populate the 'user' and 'index_name' fields
        from the validation context, if provided.
        """
        if info.context:
            self.user = info.context.get('user')
            self.name = info.context.get('name')
        return self


class IndexList(RootModel[Dict[str, IndexConfig]]):
    @model_validator(mode='before')
    @classmethod
    def _unwrap_and_inject_context(cls, data: Any, info: ValidationInfo) -> Any:
        """
        Unwraps the 'result' key from the raw response and injects context
        (user, index_name) into each index's data before validation.
        """
        if not isinstance(data, dict) or 'result' not in data:
            return data  # Return as is if format is not as expected

        # Extract the dictionary of indexes from the 'result' key
        indexes_data = data['result']['indexes']

        # Get user from the validation context
        user = info.context.get('user') if info.context else None

        if user and isinstance(indexes_data, dict):
            # Mutate the data in-place to add the required context
            for index_name, index_config in indexes_data.items():
                if isinstance(index_config, dict):
                    index_config['user'] = user
                    index_config['name'] = index_name

        # Return only the modified dictionary to the RootModel for validation
        return indexes_data


class DeleteResponse(BaseModel):
    """
    Represents the confirmation message received after deleting an index.
    """
    message: str
