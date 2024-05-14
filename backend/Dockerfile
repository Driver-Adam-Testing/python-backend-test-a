FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Copy the driver-db package first
COPY driver-db /app/driver-db

# Copy pyproject.toml and poetry.lock first for better caching
COPY ./pyproject.toml ./poetry.lock /app/

# Install dependencies
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

ENV PYTHONPATH=/app

# Copy the rest of the application
COPY ./scripts/ /app/scripts/
COPY ./prestart.sh /app/
COPY ./tests-start.sh /app/
COPY ./app /app/app
