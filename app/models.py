from typing import Dict, Set

from pydantic import BaseModel, Field
from pydantic.types import conint


class Repositories(BaseModel):
    forked: conint(ge=0)
    owned: conint(ge=0)
    topics: Set[str] = Field(..., example={"backend", "frontend"})


class Profile(BaseModel):
    repositories: Repositories
    watchers: conint(ge=0)
    languages: Dict[str, conint(ge=0)] = Field(..., example={"C": 3, "Python": 4})
