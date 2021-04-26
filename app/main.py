import asyncio
from typing import List

from fastapi import Path, Request, Response, status

from app.application import App
from app.models import Profile
from app.utils import aggreagate_profile_data

app = App()


@app.get("/v1/profiles/{profile}", response_model=Profile)
async def profiles(
    request: Request,
    profile: str = Path(..., description="Team/user profile name", example="adriangb"),
) -> Profile:
    app: App = request.app
    tasks: List[asyncio.Task] = []
    for client in app.clients:
        tasks.append(asyncio.create_task(client.get_repos(profile)))
    data = await asyncio.gather(*tasks)
    repos = [repo for repos in data for repo in repos]
    return aggreagate_profile_data(repos)


@app.get("/healthcheck", response_class=Response)
async def healtcheck():
    return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run(app)
