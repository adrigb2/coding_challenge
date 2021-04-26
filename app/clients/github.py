import asyncio
import operator
from typing import Dict, List, Union

from httpx import Auth, Request, Response, codes

from app.clients.base import BaseClient, RateLimitError, ResourceNotFoundError
from app.clients.types import Repository


async def add_version_header(request: Request) -> None:
    """Attatch the GitHub API v3 header to outgoing requests."""
    request.headers["Content-Type"] = "application/vnd.github.v3+json"


class BearerTokenAuth(Auth):
    """Implement bearer token authentication for httpx requests."""

    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    def auth_flow(self, request: Request) -> None:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


class GitHubClient(BaseClient):
    def __init__(self, token: Union[None, str], **kwargs):
        if token:
            kwargs["auth"] = BearerTokenAuth(token)
        event_hooks = kwargs.get("event_hooks") or {}
        request_hooks = event_hooks.get("request") or []
        request_hooks.append(add_version_header)
        event_hooks["request"] = request_hooks
        kwargs["event_hooks"] = event_hooks
        super().__init__(**kwargs)

    @staticmethod
    async def handle_rate_limit(response: Response) -> None:
        if response.is_error and int(response.headers["X-RateLimit-Remaining"]) == 0:
            raise RateLimitError

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
        response = await self.get(f"/users/{profile}/repos")
        if response.status_code == codes.NOT_FOUND:
            raise ResourceNotFoundError
        # at this point, all input is coming from existing data
        # so we no longer check for status codes
        repos = response.json()
        topic_tasks: List[asyncio.Task] = []
        language_tasks: List[asyncio.Task] = []
        for repo in repos:
            # rename keys
            repo["forked"] = repo["fork"]
            # get topics
            topic_tasks.append(
                asyncio.create_task(self.get_repo_topics(profile, repo["name"]))
            )
            language_tasks.append(
                asyncio.create_task(self.get_repo_language(profile, repo["name"]))
            )
        repo_topics = await asyncio.gather(*topic_tasks)
        repo_languages = await asyncio.gather(*language_tasks)
        for repo, topics, language in zip(repos, repo_topics, repo_languages):
            repo["topics"] = topics
            repo["language"] = language
        return [Repository(**repo_data) for repo_data in repos]

    async def get_repo_topics(self, profile: str, repo: str) -> List[str]:
        """Get all of the topics a repo is tagged with.

        Parameters
        ----------
        profile : str
            User/team/profile slug.
        repository : str
            Repository slug.

        Returns
        -------
        List[str]
            Topics the repository is tagged with.
        """
        response = await self.get(
            f"/repos/{profile}/{repo}/topics",
            headers={"accept": "application/vnd.github.mercy-preview+json"},
        )
        return response.json()["names"]

    async def get_repo_language(self, profile: str, repo: str) -> Union[str, None]:
        """Get the top language used in a repo.

        Parameters
        ----------
        profile : str
            User/team/profile slug.
        repository : str
            Repository slug.

        Returns
        -------
        Union[str, None]
            Top language used in the repository, or None if no language was found.
        """
        response = await self.get(f"/repos/{profile}/{repo}/languages")
        data: Dict[str, int] = response.json()  # {"language": bytes_of_code}
        if not data:
            return None
        return max(data.items(), key=operator.itemgetter(1))[0]
