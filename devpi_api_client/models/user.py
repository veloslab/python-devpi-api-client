# In devpi_api_client/models/user.py

from collections.abc import Iterator
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, RootModel, model_validator

from .index import IndexConfig


class UserInfo(BaseModel):
    """Details for a single devpi user."""

    username: str
    email: str
    indexes: dict[str, IndexConfig] = Field(default_factory=dict)
    created: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _annotate_index_context(cls, data: Any) -> Any:
        if isinstance(data, dict) and "indexes" in data:
            username = data.get("username")
            for index_name, index_config in data["indexes"].items():
                if isinstance(index_config, dict):
                    index_config.setdefault("user", username)
                    index_config.setdefault("name", index_name)
        return data

    def get_index_names(self) -> list[str]:
        """Return the list of index names for the user."""
        return list(self.indexes.keys())

    def has_index(self, index_name: str) -> bool:
        """Check whether the user owns a given index."""
        return index_name in self.indexes

    def get_index_config(self, index_name: str) -> Optional[dict[str, Any]]:
        """Return the configuration dictionary for a given index if it exists."""
        config = self.indexes.get(index_name)
        if config is None:
            return None
        if isinstance(config, IndexConfig):
            return config.model_dump(exclude_defaults=True, exclude_none=True)
        return config


class UserList(RootModel[dict[str, UserInfo]]):
    """Mapping of usernames to UserInfo models with convenience helpers."""

    @model_validator(mode="before")
    @classmethod
    def _normalize_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "result" in data:
                result = data["result"]
                if isinstance(result, dict):
                    if "users" in result:
                        data = result.get("users", {})
                    else:
                        data = result
                else:
                    data = result
            elif "users" in data:
                data = data.get("users", {})

        if isinstance(data, list):
            return {
                username: {"username": username, "email": "", "indexes": {}}
                for username in data
            }

        if isinstance(data, dict):
            normalized: dict[str, dict[str, Any]] = {}
            for username, raw in data.items():
                if isinstance(raw, UserInfo):
                    raw = raw.model_dump()
                if isinstance(raw, dict):
                    normalized[username] = {
                        "username": raw.get("username", username),
                        "email": raw.get("email", ""),
                        "indexes": raw.get("indexes", {}) or {},
                    }
                else:
                    normalized[username] = {
                        "username": username,
                        "email": str(raw) if raw is not None else "",
                        "indexes": {},
                    }
            return normalized

        return data

    def __iter__(self) -> Iterator[str]:  # type: ignore[override]
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, item: object) -> bool:
        return item in self.root

    def get_usernames(self) -> list[str]:
        """Return the list of usernames contained in this mapping."""
        return list(self.root.keys())

    def get(self, username: str) -> Optional[UserInfo]:
        """Return the UserInfo for a username if present."""
        return self.root.get(username)


class UserCreateResponse(BaseModel):
    """API response returned after creating a user."""

    type: Optional[str] = None
    result: Optional[UserInfo] = None
    message: Optional[str] = None
    username: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        result = normalized.get("result")
        if isinstance(result, dict):
            normalized.setdefault("username", result.get("username"))

        return normalized

    @model_validator(mode="after")
    def _ensure_username_present(self) -> "UserCreateResponse":
        if self.result and self.username is None:
            object.__setattr__(self, "username", self.result.username)

        if self.username is None:
            raise ValueError("username missing from user creation response")

        return self

    def is_success(self) -> bool:
        if self.message:
            msg = self.message.lower()
            return "success" in msg or "created" in msg

        return self.result is not None


class UserDeleteResponse(BaseModel):
    """API response returned after deleting a user."""

    message: str

    def is_success(self) -> bool:
        msg = self.message.lower()
        return "success" in msg or "deleted" in msg
