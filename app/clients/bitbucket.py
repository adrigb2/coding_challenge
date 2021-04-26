import asyncio
from typing import Dict, List, Union

from httpx import BasicAuth, Response, codes

from app.clients.base import BaseClient, ResourceNotFoundError
from app.clients.types import Repository


class BitBucketClient(BaseClient):
    def __init__(self, username: Union[None, str], token: Union[None, str], **kwargs):
        if username and token:
            kwargs["auth"] = BasicAuth(username=username, password=token)
        super().__init__(**kwargs)

    @staticmethod
    async def handle_rate_limit(response: Response) -> None:
        # Unfortunately, BitBucket doesn't provide documentation about rate limit errors
        # and I haven't been able to trigger one even with thousands of unauthenticated requests
        pass

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
        response = await self.get(f"/2.0/repositories/{profile}/")
        if response.status_code == codes.NOT_FOUND:
            raise ResourceNotFoundError
        data = response.json()
        repos: List[Dict] = data["values"]
        while "next" in data:
            response = await self.get(data["next"])
            data = response.json()
            repos.extend(data["values"])
        watcher_tasks: List[asyncio.Task] = []
        for repo in repos:
            repo["forked"] = (
                "parent" in repo
            )  # this is a fork if there is a 'parent' key
            repo["language"] = repo["language"] or None  # replace "" with None
            repo[
                "topics"
            ] = []  # Bitbucket doesn't support topics/tags; interpret as an empty set
            watcher_tasks.append(
                asyncio.create_task(self.get_watcher_count(profile, repo["slug"]))
            )
        for repo, watchers in zip(repos, (await asyncio.gather(*watcher_tasks))):
            repo["watchers"] = watchers
        return [Repository(**repo) for repo in repos]

    async def get_watcher_count(self, profile: str, repository: str) -> int:
        """Get a repositories watcher count.

        Parameters
        ----------
        profile : str
            User/team/profile slug.
        repository : str
            Repository slug.

        Returns
        -------
        int
            Total number of watchers for the repository.
        """
        response = await self.get(f"/2.0/repositories/{profile}/{repository}/watchers")
        data = response.json()
        watchers = len(data["values"])
        while "next" in data:
            response = await self.get(data["next"])
            data = response.json()
            watchers += len(data["values"])
        return watchers
