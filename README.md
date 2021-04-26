# Coding Challenge App

A FastAPI app to aggregate profiles across GitHub and BitBucket.

## Enviroment variables

Like most 12-factor apps, this app expects its configuration as enviroment variables.
The easiest way to populate these is by making a `.env` text file in the root of the repo
and putting them there. See [Docker's .env syntax rules] for syntax guidence.

## API Keys

This app is set up to run with or without API keys.
_Without_ API keys, you will quickly hit the API rate limits for GitHub and/or BitBucket.
API Keys are set via the following enviroment variables:

- `GITHUB_TOKEN`: a GitHub personal token. See [GitHub's guide] for gudiance in generating one. You don't need to check/grant _any_ permissions.
- `BITBUCKET_TOKEN`: a BitBucket app password. See [BitBucket's app password docs] for guidance creating them. You must grant account and repository read access by checking the appropriate boxes.
- `BITBUCKET_USERNAME`: the username that the token/app password corresponds to.

## Run via Docker

Build the Docker image:

```bash
$ docker build -t app .
```

And run it:

```bash
$ docker run -it -p 80:80 --env-file .env app
```

Now you can access the Swagger docs at [http://localhost:80/docs](http://localhost:80/docs).
The Swagger docs let you explore the API and test endpoints.
When you test an endpoint, you will also get a `curl` command that you can run from a terminal.

## Run tests via Docker

Build the Docker image:

```bash
$ docker build -t app-test --target dev .
```

And run tests:

```bash
$ docker run --env-file .env app-test make test
```

## Local install

First, install [Poetry] and Python 3.8.

Then, you can install the project by doing:

```bash
$ poetry install
```

And you can run tests locally:

```bash
$ make test
```

Or start the app:

```bash
$ python -m app.main
```

Now you can access the Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs).

Install pre-commit hooks for linting:

```bash
$ pre-commit install
$ pre-commit run --all-files
```

## Error handling

There are two types of errors for which handling is implemented:

1. Rate limit errors. The clients are expected to raise a custom `RateLimitErrror` if they get a rate limit error response from a provider. FastAPI is configured to handle these errors by giving our client a unified 429 rate limit error.
2. Not found errors. For example, if an invalid username is given. These are also implemented via the pattern of having the clients raise a specific error hand having FastAPI handle the errors and give the client a unified 404.

Without this erorr handling in place, a generic 500 error would be returned to our clients.

## Improvements

### Authentication

Really this app should have one of two things:

- If it is a user-facing service, it should use OAuth 2.0 to proxy user authentication against GitHub/BitBucket so that it does not need its own credentials.
- If it is an internal / non user facing service, it needs machine user credentials (and probably several of them) to be able to programatically access GitHub/BitBucket without exceeding rate limits.

### Performance

The way it is currently set up, using REST APIs without filtering, there is a large amount of data being needlessly transfered.

For GitHub, we really should be using their GraphQL API so that in a single query we can fetch exactly the data we need and no more.

For BitBucket, we should be applying filters to our queries to extract fields from the returned resources.

This said, since the task is largely IO bound and we are already using an async web framework and asyncio Tasks internally, we are doing _much_ better than if everything was synchronous (eg. Flask).

### More providers, or differing names between providers

There's three ways to look at this:

1. A new feature to support more providers (eg. GitLab).
2. A new feature to support aggregating data across totally different accounts.
3. A failure of the current implementation to account for differing usernames across providers.

A (mostly) backwards compatible way in which all of these could be addressed is to add query parameters for a username on each platform, keeping the current path parameter as the default option. For example:

```
GET /v2/profiles/adriangb?bitbucket_name=adrigb
```

### Better data unification

For example, the languages are just cast to lowercase right now before merging the counts. Ideally we'd have some type of maaping between BitBucket names and GitHub names since I'm sure there's several that don't exactly match up.

[Docker's .env syntax rules]: https://docs.docker.com/compose/env-file/#syntax-rules
[BitBucket's app password docs]: https://developer.atlassian.com/bitbucket/api/2/reference/meta/authentication#app-pw
[GitHub's guide]: https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
