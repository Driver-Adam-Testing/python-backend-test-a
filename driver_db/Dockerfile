FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /driver_db

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry
RUN poetry config virtualenvs.create false

COPY . /driver_db

RUN poetry install
RUN apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /driver_db/database
CMD [ "/bin/sh", "-c", "poetry run alembic upgrade head" ]
