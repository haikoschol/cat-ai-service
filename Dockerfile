FROM python:3.12-slim as env

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=1.7.1 \
    # venv will be in $APP_HOME/.venv
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    APP_HOME=/app \
    PORT=8000

FROM env as builder

RUN python3 -m venv $POETRY_HOME
RUN $POETRY_HOME/bin/pip install poetry==$POETRY_VERSION

WORKDIR $APP_HOME

COPY pyproject.toml poetry.lock main.py ./
RUN $POETRY_HOME/bin/poetry install --no-root

from env as production

LABEL org.opencontainers.image.source=https://github.com/haikoschol/cat-ai-service

COPY --from=builder $APP_HOME $APP_HOME

WORKDIR $APP_HOME
EXPOSE $PORT
CMD exec ./.venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT
