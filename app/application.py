from typing import Iterable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.clients.base import BaseClient, RateLimitError, ResourceNotFoundError
from app.clients.bitbucket import BitBucketClient
from app.clients.github import GitHubClient
from app.config import Config


class App(FastAPI):

    clients: Iterable[BaseClient]
    bitbucket_client: BitBucketClient
    github_client: GitHubClient

    def __init__(self):
        super().__init__(on_startup=[self.startup], on_shutdown=[self.shutdown])
        self.exception_handler(ResourceNotFoundError)(
            resource_not_found_exception_handler
        )
        self.exception_handler(RateLimitError)(rate_limit_exception_handler)

    def startup(self):
        """Initialize config and clients."""
        self.config = Config()
        self.github_client = GitHubClient(
            token=(
                self.config.github_token.get_secret_value()
                if self.config.github_token
                else None
            ),
            base_url=self.config.github_url,
        )
        self.bitbucket_client = BitBucketClient(
            username=self.config.bitbucket_username,
            token=(
                self.config.bitbucket_token.get_secret_value()
                if self.config.bitbucket_token
                else None
            ),
            base_url=self.config.bitbucket_url,
        )
        self.clients = (self.github_client, self.bitbucket_client)

    async def shutdown(self):
        """Gracefully shutdown clients"""
        for client in self.clients:
            await client.aclose()


async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={"message": "Rate limit exceeded"},
    )


async def resource_not_found_exception_handler(
    request: Request, exc: ResourceNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found"},
    )
