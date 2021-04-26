from fastapi.testclient import TestClient

from app.main import app
from tests.fake_providers import BitBucketRepository, GitHubRepository, mock_apps


def test_profiles():
    # Define some test data
    # really, this should be data driven and parametrized
    # but for simplicity, I'm just defining 4 repos, 2 in each provider
    # and handpicking some test cases (forked, not forked, etc.)
    bitbucket_1 = BitBucketRepository(watchers=[1, 2], language="python", slug="repo1")
    bitbucket_2 = BitBucketRepository(
        watchers=[], language="", slug="repo2", parent=True  # value doesn't matter
    )
    github_1 = GitHubRepository(
        name="repo1",
        fork=False,
        languages={"Python": 1024, "C": 2048},
        topics=["AI"],
        watchers=0,
    )
    github_2 = GitHubRepository(
        name="repo2", fork=True, languages={}, topics=[], watchers=2
    )
    expected = {
        "repositories": {"forked": 2, "owned": 2, "topics": ["AI"]},
        "watchers": 4,
        "languages": {"python": 1, "c": 1, "other": 2},
    }
    with TestClient(app) as client:
        with mock_apps(app) as app_mocks:
            app_mocks.github.set_data(profiles={"adriangb": [github_1, github_2]})
            app_mocks.bitbucket.set_data(
                profiles={"adriangb": [bitbucket_1, bitbucket_2]}
            )
            response = client.get("/v1/profiles/adriangb")
            assert response.status_code == 200
            assert response.json() == expected
