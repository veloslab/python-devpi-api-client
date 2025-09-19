"""
Token models for devpi API client.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, model_validator, ValidationInfo


class TokenInfo(BaseModel):
    """
    Represents the parsed restrictions and metadata for a single token.
    """
    id: str
    user: str
    allowed: Optional[List[str]] = None
    expires: Optional[int] = None
    indexes: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    restrictions: List[str]

    @model_validator(mode='before')
    @classmethod
    def parse_and_flatten_restrictions(cls, data: Any, info: ValidationInfo) -> Any:
        """
        Parse the 'restrictions' list from the raw data and flatten
        its key-value pairs into the model's main fields.
        """
        if not isinstance(data, dict):
            return data

        for item in data.get('restrictions', []):
            if '=' in item:
                key, value = item.split('=', 1)
                if key == 'expires':
                    data['expires'] = int(value)
                elif key in ['allowed', 'indexes', 'projects']:
                    data[key] = value.split(',')
        return data

class TokenListResult(BaseModel):
    tokens: Dict[str, TokenInfo]

#class TokenList(RootModel[Dict[str, IndexConfig]]):
class TokenList(BaseModel):
    result: TokenListResult

    @model_validator(mode='before')
    @classmethod
    def inject_context_into_tokens(cls, data: Any, info: ValidationInfo) -> Any:
        """
        Injects context (like user and token ID) into each token's data
        before it is passed to the TokenInfo model for validation.
        """
        if not isinstance(data, dict) or 'result' not in data:
            return data

        user = info.context.get('user') if info.context else 'unknown'

        for token_id, token_data in data['result']['tokens'].items():
            token_data['id'] = token_id
            token_data['user'] = user

        return data
