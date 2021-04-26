from abc import ABC, abstractmethod, abstractstaticmethod
from typing import List

from httpx import AsyncClient, Response

from app.clients.types import Repository


class RateLimitError(Exception):
    """Unified exception to indicate a rate limit error."""

    pass


class ResourceNotFoundError(Exception):
    """Unified exception to handle 404s."""

    pass


class BaseClient(ABC, AsyncClient):
    def __init__(self, **kwargs):
        event_hooks = kwargs.get("event_hooks") or {}
        response_hooks = event_hooks.get("response") or []
        response_hooks.append(self.handle_rate_limit)
        event_hooks["response"] = response_hooks
        kwargs["event_hooks"] = event_hooks
        super().__init__(**kwargs)

    @abstractstaticmethod
    async def handle_rate_limit(response: Response) -> None:
        """Parse the response and raise a RateLimitError if needed.

        Parameters
        ----------
        response : Response
            Response to an outgoing request.
        """
        pass

    @abstractmethod
    async def get_repos(self, profile: str) -> List[Repository]:
        """Retrieve a user/teams' repositories.

        Parameters
        ----------
        profile : str
            The username/team/profile slug.

        Returns
        -------
        List[Repository]
            List of repositories found for this provider.
        """
        pass
