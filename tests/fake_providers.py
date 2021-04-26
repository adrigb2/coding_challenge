"""Fake apps to mimick VCS providers.

These get attatched to httpx to fake out calls.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import patch

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.main import App


class RepositoryBase(BaseModel):
    pass


class GitHubRepository(RepositoryBase):
    name: str
    fork: bool
    languages: Dict[str, int]
    topics: List[str]
    watchers: int


class BitBucketRepository(RepositoryBase):
    slug: str
    parent: Optional[Any]
    language: str
    watchers: List[Any]


class MockProvider(FastAPI):

    profiles: Dict[str, List[RepositoryBase]]

    def set_data(self, profiles: Dict[str, List[RepositoryBase]]) -> None:
        self.profiles = profiles


bitbucket = MockProvider()


def split_items(items: List[Any]):
    arrs = []
    while len(items) > 10:
        pice = items[:10]
        arrs.append(pice)
        items = items[10:]
    arrs.append(items)
    return arrs


def bitbucket_paginate(items: List[Any], page: int, base_url: str) -> Dict[str, Any]:
    split = split_items(items)
    if page > len(split):
        raise HTTPException(404)
    res = {"values": split[page - 1]}
    if page < len(split):
        res["next"] = f"{base_url}?page={page+1}"
    return res


@bitbucket.get("/2.0/repositories/{profile}")
def get_bitbucket_profiles(profile: str, page: Optional[int] = 1):
    if profile not in bitbucket.profiles:
        raise HTTPException(404)
    repos = bitbucket.profiles[profile]
    data = [r.dict(exclude={"watchers"}, exclude_unset=True) for r in repos]
    return bitbucket_paginate(
        data, page, f"https://api.bitbucket.org/2.0/repositories/{profile}"
    )


@bitbucket.get("/2.0/repositories/{profile}/{repository}/watchers")
def get_bitbucket_repo_watchers(profile: str, repository: str, page: Optional[int] = 1):
    if profile not in bitbucket.profiles:
        raise HTTPException(404)
    profile_repos: List[BitBucketRepository] = bitbucket.profiles[profile]
    repos = {r.slug: r for r in profile_repos}
    if repository not in repos:
        raise HTTPException(404)
    return bitbucket_paginate(
        repos[repository].watchers,
        page,
        f"https://api.bitbucket.org/2.0/repositories/{profile}/{repository}/watchers",
    )


github = MockProvider()


@github.get("/users/{profile}/repos")
def get_github_repos(profile: str):
    if profile not in github.profiles:
        raise HTTPException(404)
    repos = github.profiles[profile]
    return [r.dict(exclude={"languages", "topics"}) for r in repos]


@github.get("/repos/{profile}/{repository}/languages")
def get_github_repo_languages(profile: str, repository: str):
    if profile not in github.profiles:
        raise HTTPException(404)
    profile_repos: List[GitHubRepository] = github.profiles[profile]
    repos = {r.name: r for r in profile_repos}
    if repository not in repos:
        raise HTTPException(404)
    return repos[repository].languages


@github.get("/repos/{profile}/{repository}/topics")
def get_github_repo_topics(profile: str, repository: str):
    if profile not in github.profiles:
        raise HTTPException(404)
    profile_repos: List[GitHubRepository] = github.profiles[profile]
    repos = {r.name: r for r in profile_repos}
    if repository not in repos:
        raise HTTPException(404)
    return {"names": repos[repository].topics}


@contextmanager
def attatch_app(client: httpx.AsyncClient, app: FastAPI):
    transport = client._init_transport(app=app)
    with patch.object(client, "_transport", transport):
        yield


class MockApps(BaseModel):
    github: MockProvider
    bitbucket: MockProvider

    class Config:
        arbitrary_types_allowed = True


@contextmanager
def mock_apps(app: App) -> Generator[MockApps, None, None]:
    with attatch_app(app.bitbucket_client, bitbucket), attatch_app(
        app.github_client, github
    ):
        yield MockApps(github=github, bitbucket=bitbucket)
