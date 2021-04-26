from typing import Optional

from pydantic import BaseSettings
from pydantic.networks import AnyHttpUrl
from pydantic.types import SecretStr


class Config(BaseSettings):
    github_url: AnyHttpUrl
    bitbucket_url: AnyHttpUrl
    github_token: Optional[SecretStr] = None
    bitbucket_token: Optional[SecretStr] = None
    bitbucket_username: Optional[str] = None
