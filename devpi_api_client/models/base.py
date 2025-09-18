"""
Base models and common response types for devpi API client.
"""

from pydantic import BaseModel


class DeleteResponse(BaseModel):
    """
    Represents the confirmation message received after deleting an object.
    """
    message: str
