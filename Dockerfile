FROM tiangolo/uvicorn-gunicorn:python3.8-slim as base

# Install curl, to install poetry
RUN apt-get update && apt-get -y install curl
# Install and setup poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/tmp/poetry python
RUN cp -R /tmp/poetry/* /usr/local
RUN poetry config virtualenvs.create false

# Set up project
ENV PROJECT_DIR=/app
COPY pyproject.toml $PROJECT_DIR
RUN poetry install --no-dev --no-root -vvv
COPY app/ $PROJECT_DIR/app
RUN poetry install --no-dev -vvv

FROM base as dev
RUN apt-get -y install make
RUN poetry install -vvv
COPY Makefile $PROJECT_DIR
COPY tests/ $PROJECT_DIR/tests
CMD ["/bin/bash"]

FROM base as deploy
# Switch to a non-privaleged user
RUN groupadd -r user && useradd -r -g user user
USER user
