from collections import defaultdict
from typing import DefaultDict, List

from app.clients.types import Repository
from app.models import Profile, Repositories


def aggreagate_profile_data(repos: List[Repository]) -> Profile:
    """Aggregate data across repositories to form a profile.

    Parameters
    ----------
    repos : List[Repository]
        All of the user/teams' repositories.

    Returns
    -------
    Profile
        User/team profile with data collected from all of the repositories.
    """
    owned_count = forks_count = watchers = 0
    language_count: DefaultDict[str, int] = defaultdict(int)
    topics = set()
    for repo in repos:
        language_count[repo.language] += 1
        if repo.forked:
            forks_count += 1
        else:
            owned_count += 1
        watchers += repo.watchers
        topics = topics.union(repo.topics)
    repos = Repositories.construct(owned=owned_count, forked=forks_count, topics=topics)
    return Profile.construct(
        repositories=repos, languages=dict(language_count), watchers=watchers
    )
