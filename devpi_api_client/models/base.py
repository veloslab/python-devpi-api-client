from pydantic import BaseModel


class DeleteResponse(BaseModel):
    """
    Represents the confirmation message received after deleting object
    """
    message: str
