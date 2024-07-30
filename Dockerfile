FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Copy the driver-db package first
COPY driver_db /driver_db
COPY packages /packages
COPY ./backend/app /app

# Copy pyproject.toml and poetry.lock first for better caching
COPY backend/pyproject.toml /app/

ENV PYTHONPATH=/app

# Install dependencies
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

# Install start scripts
COPY backend/scripts/start-reload.sh /start-reload.sh
COPY backend/scripts/start.sh /start.sh
COPY backend/scripts/gunicorn_conf.py /gunicorn_conf.py
RUN chmod +x /start-reload.sh
RUN chmod +x /start.sh

# Copy the rest of the application
COPY backend/scripts/ /app/scripts/
COPY backend/prestart.sh /app/
COPY backend/tests-start.sh /app/
COPY backend/app /app/app

RUN apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "/bin/sh", "-c", "if [ \"$INSTALL_DEV\" = 'true' ]; then exec /start-reload.sh \"$@\"; else exec /start.sh \"$@\"; fi" ]
