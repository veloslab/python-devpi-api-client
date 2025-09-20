"""
Project/Package models for devpi API client.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, RootModel, model_validator


class LogItem(BaseModel):
    """Represents a log entry for a release file."""
    what: str
    who: Optional[str] = None
    when: list[int]
    count: Optional[int] = None
    dst: Optional[str] = None


class Link(BaseModel):
    """Represents a release file link."""
    rel: str
    hash_spec: str
    href: HttpUrl
    log: list[LogItem]


class ProjectVersion(BaseModel):
    """Represents the metadata for a specific package version."""
    name: str
    version: str
    metadata_version: Optional[str] = ''
    summary: Optional[str] = ''
    home_page: Optional[str] = ''
    author: Optional[str] = ''
    author_email: Optional[str] = None
    maintainer: Optional[str] = ''
    maintainer_email: Optional[str] = None
    license: Optional[str] = ''
    description: Optional[str] = ''
    keywords: Optional[str] = ''
    platform: list[str] = Field(default_factory=list)
    classifiers: list[str] = Field(default_factory=list)
    download_url: Optional[str] = ''
    supported_platform: list[str] = Field(default_factory=list)
    comment: Optional[str] = ''
    provides: list[Any] = Field(default_factory=list)
    requires: list[Any] = Field(default_factory=list)
    obsoletes: list[Any] = Field(default_factory=list)
    project_urls: list[Any] = Field(default_factory=list)
    provides_dist: list[Any] = Field(default_factory=list)
    obsoletes_dist: list[Any] = Field(default_factory=list)
    requires_dist: list[Any] = Field(default_factory=list)
    requires_external: list[Any] = Field(default_factory=list)
    requires_python: Optional[str] = ''
    description_content_type: Optional[str] = ''
    provides_extras: list[Any] = Field(default_factory=list)
    dynamic: list[Any] = Field(default_factory=list)
    license_expression: Optional[str] = ''
    license_file: list[Any] = Field(default_factory=list)
    links: list[Link] = Field(..., alias='+links')

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

class ProjectVersionList(RootModel[dict[str, ProjectVersion]]):
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
