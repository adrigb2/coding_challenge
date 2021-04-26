from typing import List, Union

from pydantic import BaseModel, validator
from pydantic.types import conint


class Repository(BaseModel):
    forked: bool
    language: Union[str, None]
    topics: List[str] = []
    watchers: conint(ge=0)

    @validator("language")
    def santize_language(cls, language: Union[str, None]) -> str:
        """Replace null/missing languages with "other" and make languages lowercase."""
        if language is None:
            return "other"
        return language.lower()
