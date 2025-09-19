"""
Project/Package models for devpi API client.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, RootModel, model_validator, ValidationInfo


class LogItem(BaseModel):
    """Represents a log entry for a release file."""
    what: str
    who: Optional[str] = None
    when: List[int]
    count: Optional[int] = None
    dst: Optional[str] = None


class Link(BaseModel):
    """Represents a release file link."""
    rel: str
    hash_spec: str
    href: HttpUrl
    log: List[LogItem]


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
    platform: List[str] = []
    classifiers: List[str] = []
    download_url: Optional[str] = ''
    supported_platform: List[str] = []
    comment: Optional[str] = ''
    provides: List[Any] = []
    requires: List[Any] = []
    obsoletes: List[Any] = []
    project_urls: List[Any] = []
    provides_dist: List[Any] = []
    obsoletes_dist: List[Any] = []
    requires_dist: List[Any] = []
    requires_external: List[Any] = []
    requires_python: Optional[str] = ''
    description_content_type: Optional[str] = ''
    provides_extras: List[Any] = []
    dynamic: List[Any] = []
    license_expression: Optional[str] = ''
    license_file: List[Any] = []
    links: List[Link] = Field(..., alias='+links')

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

class ProjectVersionList(RootModel[Dict[str, ProjectVersion]]):
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

