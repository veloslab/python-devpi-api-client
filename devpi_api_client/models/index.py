"""
Index models for devpi API client.
"""
from typing import Any, Optional, cast

from pydantic import BaseModel, Field, RootModel, ValidationInfo, model_validator


class IndexConfig(BaseModel):
    user: Optional[str] = None
    name: Optional[str] = None
    type: str
    bases: Optional[list[str]] = Field(default_factory=list)
    volatile: bool = Field(default=False)
    acl_upload: Optional[list[str]] = Field(default_factory=list)
    acl_toxresult_upload: Optional[list[str]] = Field(default_factory=list)
    mirror_whitelist_inheritance: Optional[str] = None
    mirror_whitelist: Optional[list[Any]] = Field(default_factory=list)
    projects: Optional[list[str]] = None

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
            self.user = info.context.get('user', self.user)
            self.name = info.context.get('name', self.name)
        return self


class IndexList(RootModel[dict[str, IndexConfig]]):
    @model_validator(mode='before')
    @classmethod
    def _unwrap_and_inject_context(cls, data: Any, info: ValidationInfo) -> Any:
        """
        Unwraps the 'result' key from the raw response and injects context
        (user, index_name) into each index's data before validation.
        """
        if not isinstance(data, dict) or 'result' not in data:
            indexes_data = data  # Return as is if format is not as expected
        else:
            # Extract the dictionary of indexes from the 'result' key
            indexes_data = data['result']['indexes']

        # Get user from the validation context
        user = info.context.get('user') if info.context else None

        if user and isinstance(indexes_data, dict):
            indexes_dict = cast(dict[str, dict[str, Any]], indexes_data)
            for index_name, index_config in indexes_dict.items():
                index_config.setdefault('user', user)
                index_config.setdefault('name', index_name)
            return indexes_dict

        return indexes_data
